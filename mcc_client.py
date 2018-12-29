import os
import random
import time
import sys

session_id='%d%06d'%(time.time(),random.random()*1000000)
inp=sys.stdin.read()

with open('/data/misaka_query_%s.txt'%session_id, 'w') as f:
    f.write(inp)
while not os.path.exists('/data/misaka_answer_%s.txt'%session_id):
    time.sleep(.1)
    with open('/data/misaka_keepalive.txt','w') as f:
        f.write('.')
    os.remove('/data/misaka_keepalive.txt')

with open('/data/misaka_answer_%s.txt'%session_id) as f:
    print(f.read())

os.remove('/data/misaka_query_%s.txt'%session_id)
os.remove('/data/misaka_answer_%s.txt'%session_id)
