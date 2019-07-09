# -*- encoding: utf-8 -*-
from curses.textpad import Textbox
from x_menu_src.log import log
from x_menu_src.text import TextSave, COLOR_SCAN2, ascii2filter
from functools import wraps
from termcolor import colored
import time
import re, os

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
    
    def extend_do_edit(self, ch):
        self.cursor = self._win.getyx()


    def extend_do(self, ch):
        if time.time() - self._last_type_time > self._delay:
            self.old_command = ''
        self.cursor = self._win.getyx()
        t = self.gather().split('\n')
        self._win.move(*self.cursor)
        try:
            self.this_line = t[self.cursor[0]]
        except IndexError:
            if len(self.old_command) > 2:
                self.old_command = ''
            self._last_type_time = time.time() 
            return
        self.this_line_raw = TextSave.load(row=self.cursor[0])
        if not self.this_line_raw:
            self.this_line_raw = self.this_line

        if ch < 128:
            self.old_command += chr(ch)
        old_command = self.old_command
        self._acitons(old_command)
        if len(self.old_command) > 2:
            self.old_command = ''
        self._last_type_time = time.time() 

        #import pdb;pdb.set_trace()

    def _acitons(self, old_command):
        m = Methods.get(old_command)
        if m:
            m(self)

    def __strage_map(self,raw):
        d = {}
        ll = 0
        last = 0
        l = None
        for i in COLOR_SCAN2.finditer(raw):
            l = i.span()
            
            for i2 in range(last,l[0]):
                d[i2-ll] = i2 
                if last - ll == 0:
                    d[i2-ll] -= ll
            ll += l[1]  - l[0]
            last = l[1]
        if last < len(raw):
            for i2 in range(last,len(raw)+1):
                d[i2 -ll] = i2
        else:
            d[last - ll] = last

        if not d:
            return {i:i for i in range(len(raw)+1)}
        return d

    def get_location(self, sl,sr, raw):
        color_key = self.__strage_map(raw)
        log("color map:",color_key)
        log("l:%d , r:%d ||"% (sl, sr) + raw)
        if sl == 0:
            return color_key[sl],color_key[sr]
        if color_key[sl] - color_key[sl -1] > 1:
            if sr not in color_key:
                sr = list(color_key.keys())[-1]
            return color_key[sl -1] + 1 , color_key[sr]
        else:
            return color_key[sl],color_key[sr]

    def set_save_file(self, path):
        self._file = path if isinstance(path, str) else ''

    def get_now_word(self):
        now = self.cursor[1]
        line = self.this_line
        rawline = self.this_line_raw
        #pad = sum([i.span()[1] - i.span()[0] for i in COLOR_SCAN2.finditer(rawline[:now])])
        #if len(line) < now:
        #    line = self.gather().split('\n')[self.cursor[0]]
        #    rawline = line
        #    log("now line:",self.gather().split('\n')[self.cursor[0]])

        if re.search(r'[\w\-\.]',line[now]):
            try:
                sl,sr = next(re.finditer(r'([\w\-\.]+)',line[now:])).span()
                #log("line:",rawline,now, sl,sr)
                return self.get_location(sl+now, sr+now, rawline)

            except StopIteration:
                return
        else:
            try:
                sl, sr = next(re.finditer(r'\W+?([\w\-\.]+)',line[now:])).span()
                return self.get_location(sl+now, sr+now, rawline)
            except StopIteration:
                return

    def change_color_this_word(self,color):
        line = self.this_line
        rawline = self.this_line_raw
        old_c = self.cursor
        now = old_c[1]
        location = self.get_now_word() 
        if not location:
            return rawline
        wo = rawline[location[0]:location[1]]
        self.msg(str(location) + ":"+ str(self.this_line_raw.encode()))
        #self.msg(wo+str(location))
        line = rawline[:location[0]] + colored(ascii2filter(wo), color) +  rawline[location[1]:]
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
    
    @regist('ss')
    def to_green(self):
        if hasattr(self,"_file") and os.path.exists(self._file):
            with open(self._file, 'w') as fp:
                r = TextSave.load(-1)
                t = self.gather().replace(" \n","\n")

                if ascii2filter(r) not in  t or t in ascii2filter(r):
                    log(r)
                    log(t.encode())
                    log(ascii2filter(r).encode())
                    fp.write(r)
                    self.msg('rule save -> ' + self._file)
                    return
                C = self.__strage_map(r)

                if len(t) > len(C):
                    txt = r + t[len(C):]
                else:
                    txt = r[:C[len(t)]]
                fp.write(txt)
                self.msg('save -> ' + self._file)

    @regist( "dd" )
    def do_delete_line(self):
        y,x = self._win.getyx()
        self._win.move(y,0)
        Textbox.do_command(self, 11)
        del TextSave.text[y]
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
