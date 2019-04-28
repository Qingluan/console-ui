import curses
import os, sys
from .event import EventMix, listener
from curses.textpad import Textbox, rectangle
import time


def msgBox(screen, msg):
    h,w = screen.getmaxyx()
    msg = msg + ' ' * (w-len(msg))
    screen.addstr(0, 0, msg, curses.A_REVERSE)

    #editwin = curses.newwin(5,30, 2,1)
    #rectangle(stdscr, 1,0, 1+5+1, 1+30+1)
    screen.refresh()

    #box = Textbox(editwin)

    # Let the user edit until Ctrl-G is struck.
    #box.edit()

    # Get resulting contents
    #message = box.gather()

def infoShow(screen, win):
    cy,cx = screen.getyx()
    h,w = screen.getmaxyx()
    wh = win.height
    msgBox(screen, "id:%s yx:%d,%d  py:%d, height:%d, screen_h:%d cur:%d" % (win.id, cy,cx, win.py, wh, h, win.cursor))


class Application(EventMix):
    height,width = 0,0

    def __init__(self, top_margin=1):
        self.border = 1
        self.screen = None#curses.initscr()
        self.widgets = {}
        self.widgets_opts = {}
        self.top = top_margin
        self.ids = []

    @property
    def weight(self):
        return float(self.size[1]) / sum([self.widgets_opts[i]['weight'] for i in self.widgets_opts])
    
    @property
    def size(self):
        Application.height, Application.width = self.screen.getmaxyx() 
        return Application.height, Application.width

    def add_widget(self, widget,id=None, weight=1, **kargs):
        kargs.update({
            'weight':weight,
        })
        if widget.id:
            id = widget.id
        if not id:
            id = os.urandom(8).hex()
        widget.top = self.top

        #import pdb;pdb.set_trace();
        if len(self.ids) > 0:
            widget.left_widget = self.widgets[self.ids[-1]]
            self.widgets[self.ids[-1]].right_widget = widget
        self.ids.append(id)
        self.widgets[id] = widget
        self.widgets_opts[id] = kargs


    def update_all(self, top=2,ch=None):
        height, width = self.size
        width_weight = self.weight
        now_x = 0
        is_not_first = False
        for widget in self.widgets.values():
            if widget.focus:
                widget.action_listener(ch)

        for id, widget in self.widgets.items():
            ops = self.widgets_opts[id]
            y = top
            pad_width = int(ops['weight'] * width_weight)
            widget.update(self.screen,y,now_x, pad_width,ch=ch)
            if is_not_first:
                self.draw_extra(y, now_x)

            now_x += pad_width
            if not is_not_first:
                is_not_first = True
        if ch:
            self.ready_key(ch)

    def focus(self, idx):
        self.widgets[idx].focus = True

    def draw_extra(self, y ,x):
        if self.border:
            #self.draw_border(y, x)
            pass

    def draw_border(self, y ,x):
        h,w = self.size
        for r in range(self.top,h):
            self.screen.addstr(r,x-1, '|')

    def loop(self, stdscr):
        k = 0
        if not self.screen:
            self.screen = stdscr
        self.focus("1")
        self.screen.clear()
        self.update_all(self.top, ch=k)
        self.screen.refresh()
        #curses.doupdate()
        #self.screen.move(0,0)
        while k != ord('q'):
            self.update_all(self.top, ch=k)
            self.screen.refresh()
            curses.doupdate()
            k = self.screen.getch()






class Stack(EventMix):

    def __init__(self, datas,id=None, **opts):
        self.screen = None
        self.datas = datas
        self.cursor = 0
        self.border = 1
        self.focus = False
        self.left_widget = None
        self.right_widget = None
        self.id = id
        self.pad = None
        self.top = 0

        self.px = None
        self.py = None

    @property
    def width(self):
        return max([len(i) for i in self.datas])
    @property
    def height(self):
        return len(self.datas)

    @listener("k")
    def up(self):
        if self.cursor > 0 and self.py == 0:
            self.cursor -= 1
        else:
            if self.py > 0:
               self.py -= 1
               self.screen.move(self.py ,self.px)
               infoShow(self.screen, self)

            #self.py -= 1

    @listener('h')
    def left(self):
        if self.left_widget:
            self.focus = False
            self.left_widget.focus = True
            infoShow(self.screen,self.left_widget)

    @listener('l', use=1)
    def right(self):
        # invoid right and right and right, 
        # only right -> id's window
        if self.right_widget:
            self.focus = False
            self.right_widget.focus = True
            infoShow(self.screen,self.right_widget)

    @listener("j")
    def down(self):
        sm = min([Application.height, self.height])
        if self.py >= sm -1 and self.cursor < sm -1:
            if self.height > Application.height:
                self.cursor += 1
        else:
            #infoShow(self.screen, self)
            self.py += 1
            self.screen.move(self.py ,self.px)
            infoShow(self.screen, self)

    def update(self, screen, y, x, pad_width,ch=None, draw=True):
        if not self.screen:
            self.screen = screen
        max_heigh,max_width = screen.getmaxyx()
        if self.py is None:
            self.py,self.px = screen.getyx()
        datas = self.datas
        #if self.focus:
        #    self.action_listener(ch)
        cursor = self.cursor
        datas = datas[cursor:cursor+ max_heigh - y]

        if draw:
            self.draw(datas, screen, y,x , pad_width)
        #self.datas.append("%d, %d, %d, %d" %(y,x, self.height, self.width))

    def draw(self,datas,screen,y,x, max_width):
        #print("asf")
        self.pad = curses.newpad(len(datas), max_width)

        #infoShow(screen, self)
        go_y = self.py if self.py < self.height -1 else self.height -2
        try:
            #self.pad.move(go_y,self.px)
            pass
        except Exception as e:
            print(go_y)
            raise e
        for row, content in enumerate(datas):
            if row == self.py and self.focus:
                msg = content + ' '*  (max_width - len(content) -1 )
                self.pad.addstr(row,0, msg, curses.A_REVERSE)
            else:
                self.pad.addstr(row,0, content)
        self.pad.noutrefresh(0,0,y,x+1, y+len(datas) - 1,x+ max_width -1)
        #time.sleep(0.5)




if __name__ =="__main__":
    main = Application()
    r1 = Stack(["s"+str(i) for i in range(10)], id='1')
    r2 = Stack(["s2"+str(i) for i in range(10)], id='2')
    r3 = Stack(["s3"+str(i) for i in range(10)], id='3')
    r4 = Stack(["s3"+str(i) for i in range(10)], id='4')
    main.add_widget(r1, weight=0.5)
    main.add_widget(r2)
    main.add_widget(r3)
    curses.wrapper(main.loop)



