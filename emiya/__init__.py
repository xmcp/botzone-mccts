#coding=utf-8
import threading
import queue
import requests
import os
import sys
import json
import subprocess
import time
import logging

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_LOCATION=os.path.split(__file__)[0]
FALLBACK_EXE=os.path.join(SCRIPT_LOCATION,'fallback.exe' if sys.platform=='win32' else 'fallback')

s=requests.Session()
s.verify=False

init_logger=logging.getLogger('emiya init')
if 'mcc_localai' in os.environ:
    emiya_args=json.loads(os.environ['mcc_localai'])
else:
    emiya_args=json.loads(input('List of User ID and API Key: '))
init_logger.info('loaded %d emiya bots'%len(emiya_args))

if 'mcc_opponent' in os.environ:
    opponent=os.environ['mcc_opponent']
    init_logger.info('using opponent from environment')
else:
    opponent=input('Opponent ID: ')


class Match:
    def __init__(self,play_q):
        self.avail=threading.Event()
        self.dead=False
        self.history=[]
        self.match_id=''
        self.play_q=play_q

    def play_turn(self,output):
        self.avail.clear()
        self.history.append(output)
        self.play_q.put({'X-Match-'+self.match_id: output})

class EmiyaBot:
    def __init__(self,userid,apikey,ind):
        self.ind=ind
        self.userid=userid
        self.apikey=apikey

        self.ongoing_match=None
        self.matchid_got_event=threading.Event()
        self.play_q=queue.Queue()
        threading.Thread(target=self.localai_worker,daemon=True).start()

    def localai_worker(self):
        logger=logging.getLogger('emiya %d worker'%self.ind)
        logger.info('worker thread started')
        while True:
            can_skip_response=self.ongoing_match is None or not self.ongoing_match.avail.is_set()
            if can_skip_response and self.play_q.empty():
                item={}
                logger.info('send localai request without item')
            else:
                logger.info('waiting for item')
                item=self.play_q.get(block=True)
                logger.info('send localai request with item %r'%item)

            while True:
                res=s.get(
                    'https://www.botzone.org.cn/api/%s/%s/localai'%(self.userid,self.apikey),
                    headers=item
                )
                if res.status_code!=200:
                    logger.error('network error %s, will retry'%res.status_code)
                    logger.debug(res.text)
                    time.sleep(.2)
                else:
                    break

            lines=res.text.split('\n')

            evt_count, dead_count=map(int, lines[0].split(' '))

            for match_id, evt in zip(lines[1:1+2*evt_count:2],lines[2:1+2*evt_count:2]):
                while self.ongoing_match is None or match_id!=self.ongoing_match.match_id:
                    if not self.matchid_got_event.wait(.5):
                        logger.warning('unrecognized ongoing match, will kill %s'%match_id)
                        self.play_q.put({'X-Match-'+match_id: '-1 -1 -1 -1 -1 -1'})
                        break
                    else:
                        self.matchid_got_event.clear()
                else:
                    logger.info('got response for %s'%match_id)
                    evt=evt.strip()
                    if evt!='-1 -1 -1 -1 -1 -1':
                        self.ongoing_match.history.append(evt)
                    self.ongoing_match.avail.set()

            for match_id,*_ in map(str.split,lines[1+2*evt_count:]):
                if self.ongoing_match is not None and match_id==self.ongoing_match.match_id:
                    logger.info('match died %s'%match_id)
                    self.ongoing_match.dead=True
                    self.ongoing_match.avail.set()
                    self.ongoing_match=None
                else:
                    logger.warning('ignoring unrecognized dead match %s'%match_id)

    def start_match(self,me_first):
        logger=logging.getLogger('emiya %d starter'%self.ind)
        if self.ongoing_match is not None:
            logger.warning('replacing ongoing match')
            self.play_q.put({})

        self.ongoing_match=Match(self.play_q)
        retries_left=6

        def do_req():
            logger.info('starting match')
            res=s.get(
                'https://www.botzone.org.cn/api/%s/%s/runmatch'%(self.userid,self.apikey),
                headers={
                    'X-Game': 'Amazons',
                    'X-Player-0': 'me' if me_first else opponent,
                    'X-Player-1': 'me' if not me_first else opponent,
                }
            )
            if res.status_code!=200:
                logger.error('cannot start match',res.status_code)
                logger.info(res.text)

                nonlocal retries_left
                if retries_left:
                    retries_left-=1
                    logger.info('will retry: %d retries left'%retries_left)
                    time.sleep(.2)
                    do_req()
                else:
                    logger.critical('will NOT retry')
                return

            self.ongoing_match.match_id=res.text.strip()
            logger.info('new match id %s'%self.ongoing_match.match_id)
            self.matchid_got_event.set()

        threading.Thread(target=do_req).start()
        return self.ongoing_match

emiya_bots=[EmiyaBot(*arg,i) for i,arg in enumerate(emiya_args)]

def fallback(inp):
    p=subprocess.Popen(
        executable=FALLBACK_EXE, args=[], shell=False,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    pout,perr=p.communicate(inp.encode())
    return pout.decode()

def main(inp):
    logger=logging.getLogger('emiya main')

    hist=list(filter(None, inp.split('\n')))[1:]
    if hist[0]=='-1 -1 -1 -1 -1 -1':
        hist=hist[1:]

    logger.debug('hist %r'%hist)

    def do_first_step(bot):
        mat=bot.start_match(len(hist)==1)
        mat.avail.wait()

        if len(hist)==1:
            logger.info('match started, playing our first turn')
            mat.play_turn(hist[0])
            mat.avail.wait()

        logger.info('got result %r'%mat.history[-1])
        return mat.history[-1]

    if len(hist)<=1:
        logger.info('start new match')
        for bot in emiya_bots:
            if not bot.ongoing_match:
                return do_first_step(bot)

        logger.error('no empty bot, will restart first one')
        return do_first_step(emiya_bots[0])

    else:
        for bot in emiya_bots:
            if not bot.ongoing_match:
                continue
            mat=bot.ongoing_match

            if mat.avail.is_set() and mat.history==hist[:-1]:
                logger.info('found match %s'%mat.match_id)
                mat.play_turn(hist[-1])
                mat.avail.wait()

                if mat.dead:
                    logger.info('dead turn, using fallback')
                    return fallback(inp)
                else:
                    logger.info('got result %r'%mat.history[-1])
                    return mat.history[-1]

        logger.critical('no corresponding match')
        return '-1 -1 -1 -1 -1 -1'

if __name__=='__main__':
    print(main('1\n-1 -1 -1 -1 -1 -1\n'))
