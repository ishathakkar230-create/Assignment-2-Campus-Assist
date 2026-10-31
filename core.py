"""Local demo services; permissions are checked here, outside the language model."""
from contextlib import contextmanager
import hashlib, hmac, json, re, secrets, sqlite3, time, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parent
DB = ROOT / 'runtime' / 'campus.db'
PROGRAMMES = ('PGDM AI', 'PGDM BDA')
LANGUAGES = ('English', 'Gujarati', 'Hindi')

@contextmanager
def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()

def init():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, role TEXT, student TEXT, salt TEXT, hash TEXT);
        CREATE TABLE IF NOT EXISTS students(id TEXT PRIMARY KEY, programme TEXT, fee INTEGER, scholarship TEXT);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, username TEXT, expires REAL);
        CREATE TABLE IF NOT EXISTS memory(student TEXT, key TEXT, value TEXT, PRIMARY KEY(student,key));
        CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY, student TEXT, programme TEXT, status TEXT, reviewer TEXT);
        CREATE TABLE IF NOT EXISTS tickets(id TEXT PRIMARY KEY, student TEXT, category TEXT);
        CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY, ts REAL, actor TEXT, student TEXT, action TEXT, decision TEXT, result TEXT, request_id TEXT);
        ''')
        for sid,fee,scholarship in [('S001',25000,'Pending'),('S002',10000,'Approved')]:
            c.execute('INSERT OR IGNORE INTO students VALUES(?,?,?,?)',(sid,'PGDM AI',fee,scholarship))

def digest(password, salt):
    return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),200000).hex()

def add_user(username, password):
    users={'S001':('student','S001'),'S002':('student','S002'),'reviewer':('reviewer',None)}
    if username not in users or len(password)<12:
        raise ValueError('Use a listed account and a password of at least 12 characters.')
    role,student=users[username]; salt=secrets.token_hex(16)
    with connect() as c:
        c.execute('INSERT INTO users VALUES(?,?,?,?,?)',(username,role,student,salt,digest(password,salt)))

def login(username,password):
    with connect() as c:
        r=c.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
        if not r or not hmac.compare_digest(r['hash'],digest(password,r['salt'])): return None
        token=secrets.token_urlsafe(32)
        c.execute('INSERT INTO sessions VALUES(?,?,?)',(token,username,time.time()+3600))
    return token

def principal(token):
    with connect() as c:
        r=c.execute('SELECT u.username,u.role,u.student FROM sessions s JOIN users u ON u.username=s.username WHERE s.token=? AND s.expires>?',(token,time.time())).fetchone()
    if not r: raise PermissionError('Session expired. Please sign in again.')
    return dict(r)

def logout(token):
    with connect() as c: c.execute('DELETE FROM sessions WHERE token=?',(token,))

def record(c,p,action,decision,result,request_id=None,student=None):
    c.execute('INSERT INTO audit VALUES(?,?,?,?,?,?,?,?)',
              (uuid.uuid4().hex,time.time(),p['username'],student or p['student'],action,decision,result,request_id))

def audit(p,action,decision,result):
    with connect() as c: record(c,p,action,decision,result)

def sensitive(text):
    # Conservative gate; arbitrary preference values are separately denied in tool code.
    return bool(re.search(r'(?i)\b(otp|password|passcode|secret|token|api[ _-]?key)\b|\b\d{4,8}\b|(?:sk-|gsk_)[A-Za-z0-9_-]+',text))

def policy_search(query):
    chunks=json.loads((ROOT/'data/policy.json').read_text(encoding='utf-8'))
    stop={'the','a','an','is','my','i','can','what','of','to','in','and','on','for','do','you'}
    words=set(re.findall(r'[a-z]+',query.lower()))-stop
    scored=[(len(words & (set(re.findall(r'[a-z]+',x['text'].lower()))-stop)),x) for x in chunks]
    return [x for score,x in sorted(scored,key=lambda v:v[0],reverse=True)[:2] if score>0]

def dispatch(token,name,args,version):
    p=principal(token)
    if p['role']!='student':
        audit(p,name,'blocked','student_role_required'); return {'error':'Student role required.'}
    sid=p['student']
    if args.get('student_id',sid)!=sid:
        audit(p,name,'blocked','other_student'); return {'error':'Access denied: you may only access your own private record.'}
    try:
        with connect() as c:
            if name=='get_status':
                if args.get('kind') not in ('fee','scholarship','programme'): raise ValueError()
                kind=args['kind']; r=c.execute(f'SELECT {kind} FROM students WHERE id=?',(sid,)).fetchone()
                out={'student_id':sid,kind:r[kind]}
                if kind=='fee': out['currency']='INR'
            elif name=='search_policy':
                q=args.get('query')
                if not isinstance(q,str) or len(q)>500: raise ValueError()
                out={'evidence':policy_search(q)}
            elif name=='remember':
                key,value=args.get('key'),args.get('value')
                choices={'programme':PROGRAMMES,'language':LANGUAGES}
                if key not in choices or value not in choices[key]: raise ValueError()
                c.execute('INSERT OR REPLACE INTO memory VALUES(?,?,?)',(sid,key,value)); out={'saved':{key:value}}
            elif name=='recall':
                key=args.get('key')
                if key not in ('programme','language'): raise ValueError()
                r=c.execute('SELECT value FROM memory WHERE student=? AND key=?',(sid,key)).fetchone()
                out={'key':key,'value':r['value'] if r else None}
            elif name=='create_ticket':
                category=args.get('category')
                if category not in ('payment','scholarship','general'): raise ValueError()
                tid=uuid.uuid4().hex[:12]; c.execute('INSERT INTO tickets VALUES(?,?,?)',(tid,sid,category))
                out={'ticket_id':tid,'status':'created'}
            elif name=='request_programme_change':
                if version!='2' or args.get('programme') not in PROGRAMMES: raise ValueError()
                rid=uuid.uuid4().hex
                c.execute('INSERT INTO requests VALUES(?,?,?,?,?)',(rid,sid,args['programme'],'pending',None))
                out={'request_id':rid,'status':'pending','message':'Reviewer approval required; no change executed.'}
                record(c,p,name,'allowed','pending',rid)
                return out
            else: raise ValueError()
            record(c,p,name,'allowed','success')
            return out
    except (ValueError,TypeError,KeyError):
        audit(p,name,'error','invalid_arguments')
        return {'error':'Invalid or missing arguments. Ask for clarification. Memory accepts only listed programme/language values.'}
    except sqlite3.Error:
        return {'error':'Storage unavailable. Retry later.'}

def rows(token,table):
    p=principal(token)
    if table not in ('audit','requests','memory'): raise ValueError('Invalid table')
    if p['role']=='reviewer':
        if table=='memory': raise PermissionError('Student memory is not available to reviewers.')
        with connect() as c: return [dict(r) for r in c.execute(f'SELECT * FROM {table}')]
    with connect() as c: return [dict(r) for r in c.execute(f'SELECT * FROM {table} WHERE student=?',(p['student'],))]

def review(token,request_id,approve):
    p=principal(token)
    if p['role']!='reviewer':
        audit(p,'review','blocked','reviewer_role_required'); return False
    if type(approve) is not bool: return False
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        r=c.execute('SELECT * FROM requests WHERE id=?',(request_id,)).fetchone()
        if not r or r['status']!='pending':
            record(c,p,'review','blocked','not_pending',request_id); return False
        status='approved' if approve else 'rejected'
        if approve: c.execute('UPDATE students SET programme=? WHERE id=?',(r['programme'],r['student']))
        c.execute('UPDATE requests SET status=?,reviewer=? WHERE id=?',(status,p['username'],request_id))
        record(c,p,'review',status,'executed' if approve else 'not_executed',request_id,r['student'])
    return True
