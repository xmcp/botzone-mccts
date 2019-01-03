import time
start_time=time.time()

import os
import sys
import subprocess

FALLBACK_EXECUTABLE=''
TIMEOUT=9.8

session_id='%d'%(time.time()*1e6)
inp_fn='/data/misaka_query_%s.txt'%session_id
out_fn='/data/misaka_answer_%s.txt'%session_id

inp=sys.stdin.read()
SKIP_MCC=os.path.exists('/data/misaka_offline.txt')

if not SKIP_MCC:
    with open(inp_fn, 'w') as f:
        f.write(inp)

if FALLBACK_EXECUTABLE:
    p=subprocess.Popen(
        executable=FALLBACK_EXECUTABLE,args=[],shell=True,
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE
    )
    pout,perr=p.communicate(inp.encode())
    fallback_result=pout.decode()
else:
    fallback_result=''

if not SKIP_MCC:
    while not os.path.exists(out_fn) and time.time()-start_time<TIMEOUT:
        time.sleep(.05)
        with open('/data/misaka_keepalive.txt','w') as f:
            f.write('.')
        os.remove('/data/misaka_keepalive.txt')

if os.path.exists(out_fn):
    with open(out_fn) as f:
        print(f.read())
    os.remove(out_fn)
elif fallback_result:
    print(fallback_result)
else:
    print('mcc error no output')

if not SKIP_MCC:
    os.remove(inp_fn)
