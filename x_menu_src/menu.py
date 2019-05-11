import curses
import os, sys
from .event import EventMix, listener
from curses.textpad import Textbox, rectangle
import time


def msgBox(screen=None, msg='None'):
    if not screen:
        screen = curses.initscr()
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
    widgets = {}
    instance = None
    editor = None

    def __init__(self, top_margin=1):
        self.border = 1
        self.borders = []
        self.screen = None#curses.initscr()
        # self.widgets = {}
        self.widgets_opts = {}
        self.top = top_margin
        self.ids = []
        if Application.instance is None:
            Application.instance = self

    @property
    def weight(self):
        return float(self.size[1]) / sum([self.widgets_opts[i]['weight'] for i in self.widgets_opts])
    
    @classmethod
    def Size(cls):
        screen = curses.initscr()
        Application.height, Application.width = screen.getmaxyx()
        return Application.height, Application.width


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
            widget.left_widget = self.__class__.widgets[self.ids[-1]]
            self.__class__.widgets[self.ids[-1]].right_widget = widget
        self.ids.append(id)
        self.__class__.widgets[id] = widget
        self.widgets_opts[id] = kargs
    
    def clear_widget(self):
        self.widgets_opts[id] = {}
        self.ids = []
        self.__class__.widgets = {}


    def update_all(self, top=2,ch=None):
        height, width = self.size
        width_weight = self.weight
        now_x = 0
        is_not_first = False
        for widget in self.widgets.values():
            if widget.focus:
                widget.action_listener(ch)

        for id, widget in self.widgets.items():
            if isinstance(widget, Text):continue
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
    
    @classmethod
    def Focus(cls, idx):
        cls.widgets[idx].focus = True

    def draw_extra(self, y ,x):
        if self.border:
            # self.draw_border(y, x)
            pass

    def draw_border(self, y ,x):
        h,w = self.size
        for r in range(self.top,h):
            self.screen.addch(r,x-1, ord('|'))

    def refresh(self, k=0, clear=False, focus=None):
        if self.screen == None:
            return
        if clear:
            self.screen.clear()
        
        if focus:
            self.focus(focus)
        self.update_all(self.top, ch=k)
        curses.doupdate()
        self.screen.refresh()
        # self.screen.refresh()


    def loop(self, stdscr):
        k = 0
        if not self.screen:
            self.screen = stdscr

        self.refresh(clear=True, focus=self.ids[0])
        #curses.doupdate()
        #self.screen.move(0,0)
        while k != ord('q'):
            msgBox(stdscr, "type: %d " % k)
            self.refresh(k=k)
            k = self.screen.getch()
            

    @classmethod
    def get_widget_by_id(cls, id):
        return cls.widgets.get(id)

class _Textbox(Textbox):

    def __init__(self, win, insert_mode=True):
        super(_Textbox, self).__init__(win, insert_mode)

    # def do_command(self, ch):
    #     if ch == 10: # Enter
    #         return 0
    #     if ch == 127: # Enter
    #         return 8
    #     return Textbox.do_command(self, ch)
    def do_command(self, ch):
        if ch == 127:  # BackSpace
            Textbox.do_command(self, 8)

        return Textbox.do_command(self, ch)

class Text(EventMix):

    def __init__(self, id=None, **ops):
        self.screen = None
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
        self.Spy, self.Spx = None, None

        
        
        height, width  =  Application.Size()
        self.height = height // 3 
        self.width = width -3
        
        self.rect = [self.height * 2 , 0, height-2, width -3]
        self.loc = [self.height - 3 , self.width -1 , self.height * 2 + 1, 1]
        self.msg = None
        self.title = "Ctrl-G to exit "
        if not Application.editor:
            Application.editor = self

    def update(self, screen, pad_width=30,pad_height=30,ch=None, draw=True, title=None):
        if not self.screen:
            self.screen = screen
        if title:
            self.title = title
        stdscr = self.screen
        stdscr.addstr(self.rect[0]-1, 0, self.title)
        editwin = curses.newwin(*self.loc)
        
        rectangle(stdscr, *self.rect)
        stdscr.refresh()

        box = _Textbox(editwin)

        # Let the user edit until Ctrl-G is struck.
        box.edit()

        # Get resulting contents
        message = box.gather()
        self.msg = message
        Application.instance.refresh(clear=True)


class Stack(EventMix):

    def __init__(self, datas,id=None,mode='chains', **opts):
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
        self.ix = 0
        self.px = None
        self.py = None
        self.Spy, self.Spx = None, None
        self.mode = mode

    @property
    def width(self):
        return max([len(i) for i in self.datas])
    @property
    def height(self):
        return len(self.datas)

    def update_when_cursor_change(self, item, ch=None):
        pass

    @listener("k")
    def up(self):
        if self.cursor > 0 and self.py == self.Spy:
            self.cursor -= 1
        elif self.cursor == 0 and self.py == self.Spy:
            self.py = min([Application.height, self.height]) -1
            if self.height > Application.height:
                self.cursor = self.height -  Application.height
        else:
            if self.py > 0:
               self.py -= 1
               self.screen.move(self.py ,self.px)
               infoShow(self.screen, self)

            #self.py -= 1
        self.ix -= 1 
        if self.ix < 0:
            self.ix = 0
        self.update_when_cursor_change(self.datas[self.ix], ch="k")

    @listener('h')
    def left(self):
        if self.left_widget and self.mode == 'chains':
            self.focus = False
            self.left_widget.focus = True
            infoShow(self.screen,self.left_widget)
        self.update_when_cursor_change(self.datas[self.ix], ch="h")

    @listener('l')
    def right(self):
        # invoid right and right and right, 
        # only right -> id's window
        if self.right_widget and self.mode == 'chains':
            self.focus = False
            self.right_widget.focus = True
            infoShow(self.screen,self.right_widget)
        self.update_when_cursor_change(self.datas[self.ix], ch="l")

    @listener("j")
    def down(self):
        sm = min([Application.height, self.height])
        if self.py >= sm -1 and self.cursor < sm:
            if self.height > Application.height:
                self.cursor += 1
            else:
                self.cursor = 0
                self.py = self.Spy
        else:
            #infoShow(self.screen, self)
            self.py += 1
            self.screen.move(self.py ,self.px)
            infoShow(self.screen, self)
        self.ix += 1 
        if self.ix >= self.height:
            self.ix = self.height - 1 
        self.update_when_cursor_change(self.datas[self.ix], ch="j")
    
    @listener(10)
    def enter(self):
        msgBox(self.screen," hello world")
        r_x = self.width
        r_y = self.py
        text = Application.get_widget_by_id("text")
        if text:
            text.update(self.screen, pad_width=Application.width -8, pad_height=Application.height//3)


    def update(self, screen, y, x, pad_width,ch=None, draw=True):
        if not self.screen:
            self.screen = screen
        max_heigh,max_width = screen.getmaxyx()
        if self.py is None:
            self.py,self.px = screen.getyx()
            self.Spy, self.Spx = screen.getyx()
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


class Tree(Stack):

    l_stack = None
    r_stack = None
    m_stack = None

    def __init__(self, datas, id='middle', **kargs):
        super().__init__(datas, id=id, **kargs)
        self.l_stack =  Stack([], id='left')
        self.r_stack = Stack([], id='right')
        self.m_stack = self
    

    def get_parent(self):
        raise NotImplementedError("")
    def get_sub(self):
        raise NotImplementedError("must implement")
    
    def update_widgets(self):
        Application.instance.clear_widget()

        Application.instance.add_widget(self.l_stack, id='left')
        Application.instance.add_widget(self, id='meddle')
        Application.instance.add_widget(self.r_stack, id='right')




    @listener('h')
    def left(self):
        p = self.get_parent()
        self.m_stack.datas = self.l_stack.datas
        self.r_stack.datas = self.datas
        self.l_stack.datas = p
        if self.ix >= self.height:
            self.ix = self.height - 1

        self.update_when_cursor_change(self.datas[self.ix], ch="h")

    @listener('l', use=1)
    def right(self):
        # invoid right and right and right, 
        # only right -> id's window
        
        self.m_stack.datas = self.r_stack.datas
        self.l_stack.datas = self.datas
        self.r_stack.datas = self.get_sub()
        
        if self.ix >= self.height:
            self.ix = self.height - 1
        self.update_when_cursor_change(self.datas[self.ix], ch="l")
    
        

if __name__ =="__main__":
    main = Application()
    r1 = Stack(["s"+str(i) for i in range(10)], id='1')
    r2 = Stack(["s2"+str(i) for i in range(10)], id='2')
    r3 = Stack(["s3"+str(i) for i in range(10)], id='3')
    r4 = Stack(["s3"+str(i) for i in range(10)], id='4')
    t= Text(id='text')
    main.add_widget(r1, weight=0.5)
    main.add_widget(r2)
    main.add_widget(r3)
    main.add_widget(t)
    curses.wrapper(main.loop)



