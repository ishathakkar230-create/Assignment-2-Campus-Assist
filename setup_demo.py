from getpass import getpass
import sqlite3
from core import init, add_user, connect
from settings import VERSION
if __name__=='__main__':
    init()
    for username in (['S001','S002','reviewer'] if VERSION=='2' else ['S001','S002']):
        with connect() as c: exists=c.execute('SELECT 1 FROM users WHERE username=?',(username,)).fetchone()
        if exists:
            print(username+': already configured; existing password kept.'); continue
        while True:
            password=getpass(f'Create password for {username} (12+ characters): ')
            if len(password)<12:
                print('Too short. Try again.'); continue
            if password!=getpass('Repeat password: '):
                print('Passwords did not match. Try again.'); continue
            add_user(username,password); print(username+': created.'); break
    print('All required demo accounts are ready. Run START_WINDOWS.cmd.')
