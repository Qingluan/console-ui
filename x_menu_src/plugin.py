# -*- encoding: utf-8 -*-
from curses.textpad import Textbox
from x_menu_src.log import log
from x_menu_src.text import TextSave, COLOR_SCAN2
from functools import wraps
from termcolor import colored
import time
import re

Methods = {}
def regist(comd,exp=StopIteration):
    global Methods
    def _a(method):
        Methods[comd] = method
        @wraps(method)
        def __do(*args, **kargs):
            try:
                return method(*args, **kargs)
            except exp as e:
                log('in book err:',e)
        return __do
    return _a

SYMBOLS = {
    'doing':'½',
    'done':'●'
}


class TextEditorPlugin:
    old_command = ''
    _method = {}
    _delay = 0.5 
    _last_type_time = time.time() 
    def extend_do(self, ch):
        if time.time() - self._last_type_time > self._delay:
            self.old_command = ''
        self.cursor = self._win.getyx()
        t = self.gather().split('\n')
        self._win.move(*self.cursor)
        log(len(t),"run l: ",self.cursor[0])
        self.this_line = t[self.cursor[0]]
        self.this_line_raw = TextSave.load()

        if ch < 128:
            self.old_command += chr(ch)
        old_command = self.old_command
        self._acitons(old_command)
        if len(self.old_command) > 2:
            self.old_command = ''
        self._last_type_time = time.time() 

    def _acitons(self, old_command):
        m = Methods.get(old_command)
        if m:
            m(self)

    def get_now_word(self):
        now = self.cursor[1]
        line = self.this_line
        rawline = self.this_line_raw
        pad = sum([i.span()[1] - i.span()[0] for i in COLOR_SCAN2.finditer(line[:now])])

        if re.search(r'[\w\-\.]',line[now]):
            try:
                sp = next(re.finditer(r'([\w\-\.]+)',line[now:]))
                return [i+pad for i in sp.span()]
            except StopIteration:
                return
        else:
            try:
                sp = next(re.finditer(r'\W+?([\w\-\.]+)',line[now:]))
                return [i+pad for i in sp.span()]
            except StopIteration:
                return

    def change_color_this_word(self,color):
        line = self.this_line
        rawline = self.this_line_raw
        old_c = self.cursor
        now = old_c[1]
        location = self.get_now_word() 
        wo = rawline[location[0]+now:location[1]+now]
        self.msg(wo)
        line = rawline[:location[0]+now] + colored(wo, color) +  rawline[location[1]+now:]
        self.print_line(line, row=self.cursor[0])
        self._win.move(*old_c)
        return line

    @regist('r')
    def to_red(self):
        self.change_color_this_word('red')

    @regist('b')
    def to_blue(self):
        self.change_color_this_word('blue')
    
    @regist('y')
    def to_yellow(self):
        self.change_color_this_word('yellow')

    @regist('g')
    def to_green(self):
        self.change_color_this_word('green')
    
    @regist( "dd" )
    def do_delete_line(self):
        y,x = self._win.getyx()
        self._win.move(y,0)
        Textbox.do_command(self, 11)
        log("delete")

    @regist('w',exp=StopIteration)
    def do_jumpt_word(self):
        now = self.cursor[1]
        line = self.this_line
        if re.search(r'\w',line[now]):
            try:
                sp = next(re.finditer(r'\W',line[now:]))
            except StopIteration:
                return
            if sp:
                ss = sp.span()[0] + now
                self._win.move(self.cursor[0], ss)

        else:
            try:
                sp = next(re.finditer(r'\w',line[now:]))
            except StopIteration:
                return
            if sp:
                ss = sp.span()[0] + now
                self._win.move(self.cursor[0], ss)
        
    @regist( "dd" )
    def do_delete_line(self):
        y,x = self._win.getyx()
        self._win.move(y,0)
        Textbox.do_command(self, 11)
        log("delete")

    @regist('w',exp=StopIteration)
    def do_jumpt_word(self):
        now = self.cursor[1]
        line = self.this_line
        if re.search(r'\w',line[now]):
            try:
                sp = next(re.finditer(r'\W',line[now:]))
            except StopIteration:
                return
            if sp:
                ss = sp.span()[0] + now
                self._win.move(self.cursor[0], ss)

        else:
            try:
                sp = next(re.finditer(r'\w',line[now:]))
            except StopIteration:
                return
            if sp:
                ss = sp.span()[0] + now
                self._win.move(self.cursor[0], ss)
        

    @regist("tt")
    def run_task(self):
        line = self.this_line
        self.do_delete_line()

        if line.startswith(" [O]"):
            msg = line[5:]
        elif line.startswith(" [=]"):
            line = line[5:]
            prefix = colored(" [%s] " % SYMBOLS['done'],"green") 
            msg = prefix + colored(line, 'green', attrs=['bold'])
        else:
            prefix = colored(" [%s] " % SYMBOLS['doing'],"yellow") 
            msg = prefix + colored(line, attrs=['underline'])
        self.print_line(msg, row=self.cursor[0])
