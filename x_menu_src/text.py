import re
import curses
from termcolor import COLORS, RESET, ATTRIBUTES, HIGHLIGHTS
from .log import log

C_R = {'\x1b[%dm'%v: 'COLOR_%s' % k.upper() for k,v in COLORS.items()}
A_R = {'\x1b[%dm'%v: 'A_%s' % k.upper() for k,v in ATTRIBUTES.items()}
A_R['\x1b[3m'] = 'A_ITALIC'
H_R = {'\x1b[%dm'%v: 'COLOR_%s' % k[3:].upper() for k,v in HIGHLIGHTS.items()}
COLORS_R = {'\x1b[%dm'%v:k for k,v in COLORS.items()} 
COLOR_SCAN = re.compile(r'(\x1b\[\d+m)')
delete_sub = re.compile(r'(\x1b\[\d+\w)')
COLOR_SCAN2 = re.compile(r'(\x1b\[(\d+)\;?\d*m)')


def ascii2filter(words):
    if isinstance(words, list):
        strings = COLOR_SCAN2.sub('',' '.join(words)).split()
    else:
        strings = COLOR_SCAN2.sub('',words)
    return strings

def fgascii2curses(context,row, col, string, colors=None, now=0,max_width=None):
    attr = 0 
    color = 0
    strings = COLOR_SCAN2.split(string.strip())
    first = strings.pop(0)
    if len(first) > 0:
        if colors.last_use_color:
            color = colors.last_use_color 
        if colors.last_use_attr:
            a = colors.last_use_attr
            if a in A_R:
                attr = A_R[a]
            context.addstr(row, col,first[now:now+max_width], attr | colors.get(color))
        else:
            log('Fcol:',col, '\r' in string , 'f len:',len(first), first.encode())
            log("-----")
            context.addstr(row, col,first[now:now+max_width -2])
        col += len(first) % max_width
    for i in range(len(strings)//3):
        color,a, msg = strings[i*3:(i+1)*3]
        msg = delete_sub.sub('',msg)
        color = re.sub(r'\d\;','',color)
        a = '\x1b[%sm' % a
        if a in A_R:
            attr = getattr(curses, A_R[a])
        if color in COLORS_R:
            color = COLORS_R[color]
        else:
            color = 0
        if msg:
            log('row:',row,'col:',col,'now:',now,'msg len:',len(msg), max_width)
            if col >= max_width:
                break
            context.addstr(row,col,msg[now:now+max_width- col - 1], attr |  colors.get(color))
            col += len(msg)
    colors.last_use_color = color
    colors.last_use_attr = attr

def ascii2curses(context,row,col,string, colors=None,now=0, max_width=None):
    attr = None 
    color = None
    if COLOR_SCAN2.search(string):
        fgascii2curses(context,row,col,string, colors=colors,now=now, max_width=max_width)
        return
    strings = COLOR_SCAN.split(string)

    first = strings.pop(0)
    
    attr = 0
    color = 0
    #log('first:',first.encode(),'col:',col, '\r' in string )
    first = delete_sub.sub('',first)
    if len(first) > 0:
        if colors.last_use_color:
            color = colors.last_use_color 
        if colors.last_use_attr:
            a = colors.last_use_attr
            if a in A_R:
                attr = A_R[a]
            context.addstr(row, col,first[now:now+max_width], attr | colors.get(color))
        else:
            log('Fcol:',col, '\r' in string , 'f len:',len(first), first.encode())
            log("-----")
            context.addstr(row, col,first[now:now+max_width -2])
        col += len(first) % max_width
    for i in range(len(strings)//2):
        a,msg = strings[i*2:(i+1)*2]
        msg = delete_sub.sub('',msg)

        if a in A_R and hasattr(curses, A_R[a]):
            attr = getattr(curses, A_R[a])
            #log(attr)
        elif a in COLORS_R:
            color = COLORS_R[a]
        elif a == RESET:
            attr = 0
            color = 0

        if msg:
            log('row:',row,'col:',col,'now:',now,'msg len:',len(msg), max_width)
            if col >= max_width:
                break
            context.addstr(row,col,msg[now:now+max_width- col - 1], attr |  colors.get(color))
            col += len(msg)

    colors.last_use_color = color
    colors.last_use_attr = attr

def text_load_by_width(txt, width):
    lines = txt.split("\n")
    L = []
    for line in lines:
        raw_line = ascii2filter(line)
        #width = Width + ((len(line) - len(raw_line)) % Width)
        #print("use width: ", width)
        if len(raw_line) < width:
            L.append(line)
        else:
            seed = COLOR_SCAN2.finditer(line)
            sum_span = 0
            last_start = 0
            last_prefix = ''
            for c_str in seed:
                span = c_str.span()
                this_span = span[1] - span[0]
                if span[0] - sum_span - last_start >= width:
                    one_line = last_prefix + line[last_start: last_start + width + sum_span]
                    log(one_line)
                    L.append(one_line)
                    last_start = last_start + width + sum_span
                    sum_span = 0
                    continue
                sum_span += this_span
                last_prefix = c_str.group()
            one_line = last_prefix +  line[last_start:]
            if one_line:
                L.append(one_line)
                log(one_line)

    return L

