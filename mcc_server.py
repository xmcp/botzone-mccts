import requests
from bs4 import BeautifulSoup
import re
import time
import subprocess
import getpass
import os
import json
import logging
import threading

logging.basicConfig(level=logging.INFO,format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')

s=requests.Session()
#s.verify=False
fn_re=re.compile(r'^\s*misaka_query_(\d+)\.txt\s*$')

EXE_NAME=input('Program Name: ')

if 'mcc-credentials' in os.environ:
    username,password=json.loads(os.environ['mcc-credentials'])
else:
    username=input('Username (Email Address): ')
    password=getpass.getpass('Password: ')

res=s.post(
    'https://botzone.org.cn/login',
    data={
        'email': username,
        'password': password,
    },
)
res.raise_for_status()
assert res.json()['success']

solved_session=set()
def get_session():
    res=s.get(
        'https://botzone.org.cn/userfiles',
        timeout=(1,1),
    )
    res.raise_for_status()
    doc=BeautifulSoup(res.text,'lxml')
    table=doc.find('table',{'id':'tabFiles'})
    fns=table.find_all('a',{'data-noajax':'true'})
    for fn in fns:
        match=fn_re.match(fn.get_text())
        if match:
            session_id=match.groups()[0]
            if session_id not in solved_session:
                return session_id

def wait_session():
    while True:
        sid=get_session()
        dispatcher_logger.debug('current session %s'%sid)
        if sid:
            return sid
        time.sleep(.5)

def get_input(session_id):
    res=s.get(
        'https://botzone.org.cn/userfiles/misaka_query_%s.txt'%session_id,
        timeout=(1,1),
    )
    res.raise_for_status()
    return res.text

def run_solution(inp):
    p=subprocess.Popen(
        executable=EXE_NAME,
        args=[],
        shell=False,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    pout,perr=p.communicate(inp.encode())
    return pout.decode()

def upload_solution(out,session_id):
    filename='misaka_answer_%s.txt'%session_id
    out_len=len(out)
    res=s.post(
        'https://botzone.org.cn/userfile/uploadfile',
        timeout=(1,2),
        params={
            'resumableChunkNumber': '1',
            'resumableChunkSize': '1048576',
            'resumableCurrentChunkSize': out_len,
            'resumableTotalSize': out_len,
            'resumableType': 'text/plain',
            'resumableIdentifier': '%d-answertxt'%out_len,
            'resumableFilename': filename,
            'resumableRelativePath': filename,
            'resumableTotalChunks': '1',
            'filename': filename,
        },
        files=[
            ('resumableChunkNumber',(None,'1')),
            ('resumableChunkSize',(None,'1048576')),
            ('resumableCurrentChunkSize',(None,out_len)),
            ('resumableTotalSize',(None,out_len)),
            ('resumableType',(None,'text/plain')),
            ('resumableIdentifier',(None,'%d-answertxt'%out_len)),
            ('resumableFilename',(None,filename)),
            ('resumableRelativePath',(None,filename)),
            ('resumableTotalChunks',(None,'1')),
            ('filename',(None,filename)),
            ('file',(filename,out,'application/octet-stream')),
        ],
    )
    res.raise_for_status()
    assert res.json()['success']

def solver_main(session_id):
    start_time=time.time()
    solver_logger=logging.getLogger('solver %s'%session_id)
    for _ in range(3):
        try:
            solver_logger.info('downloading input')
            inp=get_input(session_id)
            solver_logger.debug('got input %r'%inp)

            solver_logger.info('running solution')
            out=run_solution(inp)
            solver_logger.debug('output %r'%out)

            solver_logger.info('uploading solution')
            upload_solution(out, session_id)
            solver_logger.info('solver completed in %.2fs'%(time.time()-start_time))
        except Exception:
            solver_logger.exception('error, will try again')
            time.sleep(.2)
        else:
            break
    else:
        solver_logger.error('error, will skip this request')

dispatcher_logger=logging.getLogger('dispatcher')

dispatcher_logger.info('dispatcher started')
while True:
    try:
        dispatcher_logger.debug('waiting for session')
        session_id=wait_session()
        dispatcher_logger.info('starting solver for session %s'%session_id)
        threading.Thread(target=solver_main,args=[session_id],daemon=True).start()
        solved_session.add(session_id)
        time.sleep(.2)
    except Exception:
        dispatcher_logger.exception('error, will try again')
        time.sleep(.2)