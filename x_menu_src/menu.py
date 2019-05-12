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
    ww = win.width
    msgBox(screen, "id:%s yx:%d,%d  py:%d, height:%d, screen_h:%d screen_w:%d cur:%d" % (win.id, cy,cx, win.py, wh, h,ww, win.cursor))


class Application(EventMix):
    height,width = 0,0
    widgets = {}
    instance = None
    editor = None
    top = 0
    def __init__(self, top_margin=1):
        self.border = 1
        self.borders = []
        self.screen = None#curses.initscr()
        # self.widgets = {}
        self.widgets_opts = {}
        self.top = top_margin
        self.ids = []
        Application.top = self.top
        if Application.instance is None:
            Application.instance = self

    def __setitem__(self, id, widget, **kargs):
        self.widgets_opts[id].update(kargs)
        self.__class__.widgets[id] = widget
    
    def __getitem__(self, id):
        return  self.__class__.widgets[id]

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

    def add_widget(self, widget,id=None, weight=1, direct='r', **kargs):
        kargs.update({
            'weight':weight,
        })

        if not id:
            if widget.id:
                id = widget.id
        if not id:
            id = os.urandom(8).hex()
        widget.top = self.top

        #import pdb;pdb.set_trace();
        
        if direct == 'r':
            if len(self.ids) > 0:
                widget.left_widget = self.__class__.widgets[self.ids[-1]]
                self.__class__.widgets[self.ids[-1]].right_widget = widget
            self.ids.append(id)
        else:
            if len(self.ids) > 0:
                widget.right_widget = self.__class__.widgets[self.ids[0]]
                self.__class__.widgets[self.ids[0]].left_widget = widget
            self.ids.insert(0, id)

        self.__class__.widgets[id] = widget
        self.widgets_opts[id] = kargs
    
    def clear_widget(self):
        self.widgets_opts = {}
        self.ids = []
        self.__class__.widgets = {}

    def del_widget(self, id):
        del self.widgets_opts[id]
        self.ids.remove(id)
        del self.__class__.widgets[id]


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
            if hasattr(widget, 'update_widgets'):
                widget.update_widgets()
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
        for v in self.widgets.values():
            v.focux = False
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

    def refresh(self,focus=None, k=0, clear=False):
        if self.screen == None:
            return
        if clear:
            self.screen.clear()
        
        if focus:
            self.focus(focus)
        # import pdb;pdb.set_trace()
        self.update_all(self.top, ch=k)
        curses.doupdate()
        self.screen.refresh()
        # self.screen.refresh()


    def loop(self, stdscr):
        k = 0
        if not self.screen:
            self.screen = stdscr

        self.refresh(clear=True)
        # curses.doupdate()
        #self.screen.move(0,0)
        # ii = ''
        # for ki,v in self.widgets.items():
            # if v.focus == True:
                # ii = ki
        c = 0
        while k != ord('q'):
            if c == 0:
                self.refresh(k=k, clear=False)
                c  = 1
            else:
                self.refresh(k=k, clear=True)
            # msgBox(stdscr, "type: %d " % k)
            
            k = self.screen.getch()
            
            

    @classmethod
    def get_widget_by_id(cls, id):
        return cls.widgets.get(id)

class _Textbox(Textbox):

    def __init__(self, win, insert_mode=True):
        super(_Textbox, self).__init__(win, insert_mode)

    
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
            self.py = min([Application.height, self.height]) - 1 - Application.top
            if self.height > Application.height:
                self.cursor = self.height -  Application.height + Application.top
            infoShow(self.screen, self)
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
        top = Application.top
        if self.py >= Application.height - top -1:
            if self.py + self.cursor >= self.height -1 :
                self.cursor = 0
                self.py = self.Spy
                self.ix = 0
            else:
                # msgBox(msg="if")
                self.cursor += 1
            infoShow(self.screen, self)
        elif self.py > sm -1 - top and self.cursor < sm:
            # msgBox(msg='elif')
            if self.height > Application.height:
                self.cursor += 1
            else:
                self.cursor = 0
                self.py = self.Spy
                self.ix = 0
            infoShow(self.screen, self)
        else:
            # msgBox(msg='else')
            infoShow(self.screen, self)
            self.py += 1
            self.screen.move(self.py ,self.px)
            # infoShow(self.screen, self)
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
            # import pdb; pdb.set_trace();
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
        # self.pad.addstr(0,0, '.zcompdump-user’s MacBook Pro-5.6.2', curses.A_REVERSE)
        for row, content in enumerate(datas):
            # with open("/tmp/s", "w") as fp:
            #     print(content, file=fp)
            if row == self.py and self.focus:
                # import pdb; pdb.set_trace();
                msg = content + ' '*  (max_width - len(content) -2 )
                # with open("/tmp/s", "w") as fp:
                    # print(content, file=fp)
                M = msg[:max_width -2 ] if len(msg) >= max_width else msg
                self.pad.addstr(row,0, M.strip(), curses.A_REVERSE)
            else:
                
                
                M = content[:max_width-1] if len(content) >= max_width -1 else content
                # msgBox(msg="Writing's On The Wall - Sam Smith - James Bond - Spectre - Cover - Let")
                    # print(self.width)
                self.pad.addstr(row,0, M.strip())
                
        self.pad.noutrefresh(0,0,y,x+1, y+len(datas) - 1,x+ max_width -1)
        #time.sleep(0.5)


class TreeStack(Stack):

    l_stack = None
    r_stack = None
    m_stack = None

    def __init__(self, datas, id='middle',controller=None, **kargs):
        super().__init__(datas, id=id, **kargs)
        self.controller = controller


    @listener('h')
    def left(self):
        self.controller.move_left()
    
    def update_when_cursor_change(self, item, ch):
        self.controller.update_when_cursor_change(item, ch)

    @listener('l')
    def right(self):
        self.controller.move_right()

class Tree:

    def __init__(self, cursor):
        self.cursor = cursor
        self.now = None
        self.get_tribble()
        
        
        
        

    def get_parent(self, cursor):
        raise NotImplementedError("")
    def get_sub(self, cursor):
        raise NotImplementedError("must implement")
    
    def get_current(self, cursor):
        raise NotImplementedError("must implement")
    
    def update_when_cursor_change(self, item, ch):
        raise NotImplementedError("must implemnt")
    
    def get_right_cursor(self):
        raise NotImplementedError()
    
    def get_left_cursor(self):
        raise NotImplementedError()

    def get_tribble(self):
        self.l = TreeStack(self.get_parent(self.cursor),controller=self, id='left')
        self.m = TreeStack(self.get_current(self.cursor), controller=self,id='middle')
        self.r = TreeStack(self.get_sub(self.cursor), controller=self,id='right')
        if 'left' not in Application.widgets:
            Application.instance.add_widget(self.l, id='left', weight=1)
        else:
            Application.instance['left'] = self.l

        if 'middle' not in Application.widgets:
            Application.instance.add_widget(self.m, id='middle', weight=2)
        else:
            Application.instance['middle'] = self.m
        
        if 'right' not in Application.widgets:
            Application.instance.add_widget(self.r, id='right', weight=3)
        else:
            Application.instance['right'] = self.r
        
        Application.instance.refresh(clear=True)
        Application.Focus("middle")
        self.now = self.m.datas[self.m.ix]
        


    def move_right(self):
        self.cursor = self.get_right_cursor()
        self.get_tribble()


    def move_left(self):
        self.cursor = self.get_left_cursor()
        self.get_tribble()



if __name__ =="__main__":
    main = Application()
    r1 = Stack(["s"+str(i) for i in range(28)], id='1')
    r2 = Stack(["s2"+str(i) for i in range(10)], id='2')
    # r3 = Stack(["s3"+str(i) for i in range(10)], id='3')
    # # r4 = Stack(["s3"+str(i) for i in range(10)], id='4')
    e = Text(id='text')
    # # main.add_widget(r1, weight=0.5)
    # # main.add_widget(r2)
    # # main.add_widget(r3)
    # # main.add_widget(t)
    
    # tl = FileTree(os.listdir(os.path.expanduser("~/")), root_path=os.path.expanduser("~/"), id='left')
    # tm = FileTree(os.listdir(os.path.expanduser("~/Documents")), path_root=os.path.expanduser("~/Documents"), id='middle')
    # tr = FileTree([''], id='right')

    # main.add_widget(tl,weight=1)
    # main.add_widget(tm,weight=2)
    # main.add_widget(tr,weight=3)
    
    main.focus("middle")
    main.add_widget(e)
    curses.wrapper(main.loop)



