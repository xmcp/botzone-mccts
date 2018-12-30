#coding=utf-8
import autopy.key
import os
import random
import time
import re

output_re=re.compile(r'^\s(?:\s\d+\. \w{2} - \w{2} \(\w{2}\))?\s\d+\. (\w{2}) - (\w{2}) \((\w{2})\)$')

TIMEOUT=4
SCRIPT_LOCATION=os.path.split(__file__)[0]

INVADER_CONFIG_COMPUTER='1:7:7:%d:Computer'%TIMEOUT
INVADER_CONFIG_HUMAN='0:7:7:%d:Human Player'%TIMEOUT
INVADER_CONFIG_TEMPLATE='''
<GAME-INFO-START>
RED-TYPE={first_type}
BLUE-TYPE={second_type}
<GAME-INFO-END>

<BOARD-SETUP-START>
RED-AMAZONS=A3,C1,F1,H3
BLUE-AMAZONS=A6,C8,F8,H6
ARROWS=
COLUMNS=8
ROWS=8
<BOARD-SETUP-END>

<MOVE-HISTORY-START>
Red/Blue
{history}
<MOVE-HISTORY-END>

'''

def coord_to_name(x,y):
    return '%s%s'%(chr(ord('A')+x),y+1)
def name_to_coord(name):
    nx,ny=name
    return ord(nx)-ord('A'),int(ny)-1

def proc_input(inp):
    head,*lines=list(filter(None,inp.split('\n')))
    turns=int(head)

    FIRST=INVADER_CONFIG_HUMAN
    SECOND=INVADER_CONFIG_COMPUTER
    if lines[0]=='-1 -1 -1 -1 -1 -1':
        FIRST,SECOND=SECOND,FIRST
        lines=lines[1:]

    history=[]
    for ind,(first,second) in enumerate(zip(lines[::2],lines[1::2])):
        f_c=list(map(int,first.split()))
        s_c=list(map(int,second.split()))
        history.append('  %d. %s - %s (%s)	%d. %s - %s (%s)'%(
            ind*2+1,coord_to_name(f_c[0],f_c[1]),coord_to_name(f_c[2],f_c[3]),coord_to_name(f_c[4],f_c[5]),
            ind*2+2,coord_to_name(s_c[0],s_c[1]),coord_to_name(s_c[2],s_c[3]),coord_to_name(s_c[4],s_c[5])
        ))

    if FIRST==INVADER_CONFIG_HUMAN:
        f_c=list(map(int,lines[-1].split()))
        history.append('  %d. %s - %s (%s)'%(
            turns*2-1,coord_to_name(f_c[0],f_c[1]),coord_to_name(f_c[2],f_c[3]),coord_to_name(f_c[4],f_c[5]),
        ))

    return INVADER_CONFIG_TEMPLATE.format(
        first_type=FIRST,
        second_type=SECOND,
        history='\n'.join(history),
    )

def proc_output(out):
    line=out.partition('\n\n<MOVE-HISTORY-END>')[0].split('\n')[-1]
    coords=list(map(name_to_coord,output_re.match(line).groups()))
    return ' '.join(' '.join(map(str,x)) for x in coords)

def main(inp):
    session='%04d'%(random.random()*10000)
    #print(session)

    if os.path.exists('o%s.txt'%session):
        os.remove('o%s.txt'%session)
    with open('i%s.txt'%session,'w') as f:
        f.write(proc_input(inp))

    os.system('start %s i%s.txt'%(os.path.join(SCRIPT_LOCATION,'invader.exe'),session))
    time.sleep(.45)
    # un-pause
    autopy.key.tap(autopy.key.Code.F3,[])
    time.sleep(.05)
    # do move
    autopy.key.tap('M',[autopy.key.Modifier.ALT])
    time.sleep(.05)
    autopy.key.tap('A',[])
    time.sleep(TIMEOUT)
    autopy.key.tap(autopy.key.Code.SPACE,[])
    time.sleep(.1)
    # open save dialog
    autopy.key.tap('G',[autopy.key.Modifier.ALT])
    autopy.key.tap('V',[])
    time.sleep(.2)
    # save
    autopy.key.type_string(os.path.abspath('o%s'%session))
    autopy.key.tap(autopy.key.Code.RETURN,[])
    time.sleep(.1)
    # quit
    autopy.key.tap(autopy.key.Code.F4,[autopy.key.Modifier.ALT])

    with open('o%s.txt'%session) as f:
        ret=proc_output(f.read())

    os.remove('i%s.txt'%session)
    os.remove('o%s.txt'%session)
    return ret

if __name__=='__main__':
    print(main('''1
-1 -1 -1 -1 -1 -1
'''))