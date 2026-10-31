import json
import streamlit as st
from core import init,login,logout,principal,rows,review,sensitive,dispatch
from agent import run
from settings import VERSION
st.set_page_config(page_title='Campus Assist · Assignment '+VERSION,page_icon='🎓',layout='centered')
init()
st.title('🎓 Campus Assist')
st.caption('Assignment '+VERSION+' · Fictional Student Support Agent · Groq')
if 'token' not in st.session_state:
    st.info('First run SETUP_WINDOWS.cmd. Use the local passwords you created there.')
    with st.form('signin'):
        username=st.selectbox('Account',['S001','S002','reviewer'] if VERSION=='2' else ['S001','S002'])
        password=st.text_input('Password',type='password')
        submit=st.form_submit_button('Sign in')
    if submit:
        token=login(username,password)
        if token:
            st.session_state.clear(); st.session_state.token=token; st.rerun()
        else: st.error('Incorrect credentials.')
    st.stop()
token=st.session_state.token
try: p=principal(token)
except PermissionError:
    st.session_state.clear(); st.rerun()
st.sidebar.write('Signed in: '+p['username'])
st.sidebar.caption('Role: '+p['role'])
if st.sidebar.button('Sign out'):
    logout(token); st.session_state.clear(); st.rerun()
if st.sidebar.button('New chat session'):
    st.session_state.pop('messages',None); st.session_state.pop('trace',None); st.rerun()
if VERSION=='2' and p['role']=='reviewer':
    st.subheader('Reviewer approval workspace')
    st.caption('Student requests cannot execute without this separate role. Each decision is audited.')
    requests=rows(token,'requests')
    pending=[r for r in requests if r['status']=='pending']
    if not pending: st.info('No pending requests. Sign in as a student to request a programme change.')
    for r in pending:
        st.write(r['student']+' → '+r['programme']); st.caption('Request '+r['id'])
        a,b=st.columns(2)
        if a.button('Approve and execute',key='a'+r['id']): review(token,r['id'],True); st.rerun()
        if b.button('Reject',key='r'+r['id']): review(token,r['id'],False); st.rerun()
    with st.expander('Request history'): st.dataframe(requests)
    with st.expander('Audit trail'):
        events=rows(token,'audit'); st.dataframe(events)
        st.download_button('Download audit evidence',json.dumps(events,indent=2),'audit.json')
    st.stop()
for msg in st.session_state.get('messages',[]):
    with st.chat_message(msg['role']): st.write(msg['content'])
q=st.chat_input('Ask about fees, scholarship, policy, memory or support…')
if q:
    with st.spinner('Checking tools and relevant evidence…'): answer,trace=run(token,q)
    safe_question='[Sensitive input discarded]' if sensitive(q) else q
    st.session_state.setdefault('messages',[]).extend([{'role':'user','content':safe_question},{'role':'assistant','content':answer}])
    st.session_state.trace=trace; st.rerun()
if 'trace' in st.session_state:
    with st.expander('Latest run trace and measurements',expanded=True):
        st.json(st.session_state.trace)
        st.download_button('Download this trace',json.dumps(st.session_state.trace,indent=2),'A'+VERSION+'_trace.json')
with st.expander('My persistent memory'): st.json(rows(token,'memory'))
if VERSION=='2':
    with st.expander('My change requests'): st.json(rows(token,'requests'))
    with st.expander('My current official programme'):
        if st.button('Read my official programme'): st.json(dispatch(token,'get_status',{'kind':'programme'},VERSION))
    with st.expander('My audit records'):
        events=rows(token,'audit'); st.json(events)
        st.download_button('Download my audit',json.dumps(events,indent=2),'my_audit.json')
