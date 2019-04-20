from enum import Enum, IntEnum
import json
import tkinter
import tkinter.messagebox
import threading
import os

cwd=os.path.split(__file__)[0]

S=9

class Terrain(Enum):
    air=0
    brick=1
    steel=2
    water=3
    base0=4
    base1=5
    tank_backdrop=6

    destroyed=7
    killed=8

class Action(IntEnum):
    idle=-1
    up=0
    right=1
    down=2
    left=3
    fup=4
    fright=5
    fdown=6
    fleft=7

def shooting_each(a1,a2):
    a1,a2 = min(a1,a2),max(a1,a2)
    return (a1==Action.fup and a2==Action.fdown) or (a1==Action.fright and a2==Action.fleft)

DY=[-1,0,1,0]*2 # *2 for move and fire
DX=[0,1,0,-1]*2

class InvalidAction(Exception):
    def __init__(self,s):
        self.str=s
    def __str__(self):
        return f'<Invalid Move: {self.str}>'
    __repr__=__str__

class GameOver(Exception):
    def __str__(self):
        return '<Game Over>'
    __repr__=__str__

class Tank:
    def __init__(self,world,y,x):
        self.y=y
        self.x=x
        self.world=world
        self.shoot_cd=0
        self.killed=False
        self.action_todo=None

        self.world.terrain[self.y][self.x]=Terrain.tank_backdrop

    def check_move(self,action):
        ny=self.y+DY[action]
        nx=self.x+DX[action]
        if not (0<=nx<S and 0<=ny<S):
            return False
        if self.world.terrain[ny][nx]!=Terrain.air:
            return False
        return True

    def do_action_move(self):
        action=self.action_todo
        if self.killed:
            return

        if Action.idle<action<Action.fup: # move
            if not self.check_move(action):
                raise InvalidAction('bad move')

            assert self.world.terrain[self.y][self.x]==Terrain.tank_backdrop
            if len(self.world.get_tank_by_cord(self.y,self.x))==1: # last tank
                self.world.terrain[self.y][self.x]=Terrain.air

            self.y+=DY[action]
            self.x+=DX[action]

            #self.world.terrain[self.y][self.x]=Terrain.tank_backdrop # set terrain later

    def do_action_fire(self):
        action=self.action_todo
        if self.killed:
            return

        if action>=Action.fup:
            if self.shoot_cd>0:
                raise InvalidAction('fire with cd')
            self.shoot_cd=2

            self_overlapping=len(self.world.get_tank_by_cord(self.y,self.x))>1
            ny=self.y
            nx=self.x

            while True:
                ny+=DY[action]
                nx+=DX[action]
                if not (0<=nx<S and 0<=ny<S):
                    break

                terr=self.world.terrain[ny][nx]
                if terr==Terrain.tank_backdrop: # shooting tank
                    tanks=self.world.get_tank_by_cord(ny,nx)
                    assert tanks
                    if self_overlapping or len(tanks)>1 or not shooting_each(self.action_todo,tanks[0].action_todo): # passed counter-shoot test
                        self.world.terrain[ny][nx]=Terrain.killed
                    break
                elif terr not in [Terrain.air,Terrain.water]: # shooting terrain
                    if terr in [Terrain.base0,Terrain.base1]:
                        raise GameOver()
                    elif terr!=Terrain.steel: # do shoot
                        self.world.terrain[ny][nx]=Terrain.destroyed
                    break

        if self.shoot_cd>0:
            self.shoot_cd-=1

class World:
    def __init__(self,terrain_desc):
        self.terrain=[[Terrain.air for _x in range(S)] for _y in range(S)]
        self.terrain[0][S//2]=Terrain.base0
        self.terrain[S-1][S//2]=Terrain.base1
        self.team=[
            [
                Tank(self,0,S//2-2),
                Tank(self,0,S//2+2),
            ],
            [
                Tank(self,S-1,S//2+2),
                Tank(self,S-1,S//2-2),
            ]
        ]
        if terrain_desc is not None:
            self.init_terrain(Terrain.brick,terrain_desc['brickfield'])
            self.init_terrain(Terrain.steel,terrain_desc['steelfield'])
            self.init_terrain(Terrain.water,terrain_desc['waterfield'])

    def init_terrain(self,terrain,desc):
        block_size=S*3
        mask=desc[0]+desc[1]*(2**block_size)+desc[2]*(4**block_size)
        for y in range(S):
            for x in range(S):
                if mask&(1<<(y*S+x)):
                    self.terrain[y][x]=terrain

    def proc_turn(self,actions):
        for team,tank in [[0,0],[0,1],[1,0],[1,1]]: # plan action
            self.team[team][tank].action_todo=actions[team][tank]

        for team,tank in [[0,0],[0,1],[1,0],[1,1]]: # move
            self.team[team][tank].do_action_move()

        for team, tank in [[0,0],[0,1],[1,0],[1,1]]: # update tank backdrop
            t=self.team[team][tank]
            if not t.killed:
                self.terrain[t.y][t.x]=Terrain.tank_backdrop

        for team,tank in [[0,0],[0,1],[1,0],[1,1]]: # fire
            self.team[team][tank].do_action_fire()

        for y in range(S): # remove destroyed terrain and killed tank
            for x in range(S):
                if self.terrain[y][x]==Terrain.destroyed:
                    self.terrain[y][x]=Terrain.air
                elif self.terrain[y][x]==Terrain.killed:
                    self.terrain[y][x]=Terrain.air
                    for tank in self.get_tank_by_cord(y,x):
                        tank.killed=True

        for team in [0,1]: # check all tanks died
            if self.team[team][0].killed and self.team[team][1].killed:
                raise GameOver()

    def get_tank_by_cord(self,y,x):
        return [
            tank
            for team in self.team for tank in team
            if tank.y==y and tank.x==x and not tank.killed
        ]

D=48

class GUI:
    PROMPT=-10
    action_txt={
        PROMPT: ' input  ',
        Action.idle: '        ',
        Action.up: ' ↑      ',
        Action.down: ' ↓      ',
        Action.left: ' ←      ',
        Action.right: ' →      ',
        Action.fup: ' ↑ FIRE ',
        Action.fdown: ' ↓ FIRE ',
        Action.fleft: ' ← FIRE ',
        Action.fright: ' → FIRE ',
    }
    hover_txt={
        PROMPT: '×',
        Action.idle: '',
        Action.up: '↑',
        Action.down: '↓',
        Action.left: '←',
        Action.right: '→',
        Action.fup: '╩',
        Action.fdown: '╦',
        Action.fleft: '╣',
        Action.fright: '╠',
    }

    def __init__(self):
        self.tk=tkinter.Tk()
        self.tk.title('tank gui')
        self.tk.resizable(False,False)
        self.done_flag=threading.Event()
        self.done_flag.set()
        self.lock=threading.Lock()

        self.imgs={
            k:tkinter.PhotoImage(file=f'{cwd}/img/{k.name}.png')
            for k in [Terrain.base0,Terrain.base1,Terrain.brick,Terrain.steel,Terrain.water,Terrain.tank_backdrop]
        }
        self.tank_imgs={
            (team,tank,cd):tkinter.PhotoImage(file=f'{cwd}/img/tank_{team}{tank}{"x" if cd else ""}.png')
            for team in [0,1] for tank in [0,1] for cd in [0,1]
        }

        self.world=World(None)
        self.myside=0
        self.action=[Action.idle, Action.idle]
        self.action_tank=None
        self.action_var=[tkinter.StringVar(self.tk),tkinter.StringVar(self.tk)]
        self.done_var=tkinter.StringVar(self.tk,value='.')

        self.cvs=tkinter.Canvas(self.tk,width=9*D,height=9*D,bg='black')
        self.cvs.grid(row=0,column=0)
        self.hover_id=[None,None]

        bar=tkinter.Frame(self.tk)
        self.tank_label=[
            tkinter.Label(bar,image=self.tank_imgs[0,0,self.world.team[self.myside][0].shoot_cd]),
            tkinter.Label(bar,image=self.tank_imgs[0,1,self.world.team[self.myside][1].shoot_cd]),
        ]
        self.tank_label[0].grid(row=0,column=0)
        tkinter.Label(bar,textvariable=self.action_var[0],font='Consolas').grid(row=0,column=1)
        self.tank_label[1].grid(row=0,column=2)
        tkinter.Label(bar,textvariable=self.action_var[1],font='Consolas').grid(row=0,column=3)
        tkinter.Label(bar,textvariable=self.done_var,bg='green',fg='white',font='Consolas').grid(row=0,column=4)
        self.update_action_var()
        bar.grid(row=1,column=0,sticky='we',pady=3)

        self.tk.bind('<Key-1>',lambda *_: self.change_action_tank(0))
        self.tk.bind('<Key-2>',lambda *_: self.change_action_tank(1))
        self.tk.bind('<Up>',lambda *_: self.change_action(Action.up))
        self.tk.bind('<Down>',lambda *_: self.change_action(Action.down))
        self.tk.bind('<Left>',lambda *_: self.change_action(Action.left))
        self.tk.bind('<Right>',lambda *_: self.change_action(Action.right))
        self.tk.bind('<Return>',lambda *_: self.done())

    def new_mission(self,world:World,myside):
        self.world=world
        self.myside=myside
        self.action=[Action.idle,Action.idle]
        self.action_tank=None
        self.done_flag.clear()
        self.done_var.set(' INPUT ')

        self.cvs.delete('all')
        self.draw_terrain()
        self.draw_tank()
        self.tank_label[0]['image']=self.tank_imgs[0,0,self.world.team[self.myside][0].shoot_cd]
        self.tank_label[1]['image']=self.tank_imgs[0,1,self.world.team[self.myside][1].shoot_cd]
        self.update_action_var()

    def update_action_var(self):
        for tank in [0,1]:
            act=self.action[tank]
            if act==Action.idle and tank==self.action_tank:
                act=self.PROMPT
            self.action_var[tank].set(self.action_txt[act])
            self.cvs.itemconfigure(self.hover_id[tank],text=self.hover_txt[act])

    def change_action_tank(self,ind):
        self.action_tank=ind
        self.action[ind]=Action.idle
        self.update_action_var()

    def change_action(self,act:Action):
        if self.action_tank is None:
            return
        if self.action[self.action_tank]==act and self.world.team[self.myside][self.action_tank].shoot_cd==0:
            self.action[self.action_tank]+=(Action.fup-Action.up)
        else:
            self.action[self.action_tank]=act
        self.update_action_var()

    def done(self):
        for tank in [0,1]:
            if Action.up<=self.action[tank]<Action.fup and not self.world.team[self.myside][tank].check_move(self.action[tank]):
                tkinter.messagebox.showerror('tank gui',f'Tank {tank+1} Invalid Move')
                return
        self.done_var.set('.')
        self.done_flag.set()

    def draw_terrain(self):
        imgs=self.imgs.copy()
        if self.myside==1:
            imgs[Terrain.base0],imgs[Terrain.base1] = imgs[Terrain.base1],imgs[Terrain.base0]

        for y in range(S):
            for x in range(S):
                if self.world.terrain[y][x] in self.imgs.keys():
                    self.cvs.create_image(x*D,y*D,anchor='nw',image=imgs[self.world.terrain[y][x]])

    def draw_tank(self):
        tank_imgs=self.tank_imgs.copy()
        if self.myside==1:
            for tank in [0,1]:
                for cd in[0,1]:
                    tank_imgs[0,tank,cd],tank_imgs[1,tank,cd] = tank_imgs[1,tank,cd],tank_imgs[0,tank,cd]

        for team in [0,1]:
            for tank in [0,1]:
                t=self.world.team[team][tank]
                y=t.y*D+team*D//2
                x=t.x*D+tank*D//2
                if not t.killed:
                    self.cvs.create_image(x, y, anchor='nw', image=tank_imgs[team, tank, t.shoot_cd])
                if team==self.myside:
                    self.hover_id[tank]=self.cvs.create_text(x,y,anchor='nw',font='黑体 -24',fill='blue')

    def process(self,world:World,myside):
        with self.lock:
            self.new_mission(world,myside)
            self.done_flag.wait()
            #self.cvs.delete('all')
            return json.dumps(self.action)

def main(inp_str):
    inp=json.loads(inp_str)
    init,*first_moves=inp['requests']
    second_moves=inp['responses']

    if init['mySide']==0:
        first_moves,second_moves = second_moves,first_moves
    assert len(second_moves)==len(first_moves)

    world=World(init)
    for move in zip(first_moves,second_moves):
        world.proc_turn(move)

    res=gui.process(world,init['mySide'])
    return res

sample_str='''{
	"requests": [
		{
			"brickfield": [
				14119466,
				54744598,
				44201816
			],
			"mySide": 0,
			"steelfield": [
				16777217,
				43008,
				67108868
			],
			"waterfield": [
				524288,
				8388616,
				128
			]
		},
		[
			5,
			6
		],
		[
			-1,
			-1
		],
		[
			-1,
			5
		],
		[
			6,
			3
		],
		[
			0,
			3
		]
	],
	"responses": [
		[
			2,
			2
		],
		[
			5,
			7
		],
		[
			1,
			3
		],
		[
			5,
			7
		],
		[
			1,
			3
		]
	]
}'''

startup_done=threading.Event()
def startup():
    global gui
    gui=GUI()
    startup_done.set()
    tkinter.mainloop()

threading.Thread(target=startup).start()
startup_done.wait()

if __name__=='__main__':
    threading.Thread(target=lambda:main(sample_str)).start()
    threading.Thread(target=lambda:main(sample_str)).start()
    threading.Thread(target=lambda:main(sample_str)).start()