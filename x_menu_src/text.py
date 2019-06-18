import re
import curses
from termcolor import COLORS, RESET, ATTRIBUTES, HIGHLIGHTS
from .log import log

C_R = {'\x1b[%dm'%v: 'COLOR_%s' % k.upper() for k,v in COLORS.items()}
A_R = {'\x1b[%dm'%v: 'A_%s' % k.upper() for k,v in ATTRIBUTES.items()}
H_R = {'\x1b[%dm'%v: 'COLOR_%s' % k[3:].upper() for k,v in HIGHLIGHTS.items()}
COLORS_R = {'\x1b[%dm'%v:k for k,v in COLORS.items()} 
COLOR_SCAN = re.compile(r'(\x1b\[\d+m)')
delete_sub = re.compile(r'(\x1b\[\d+\w)')

def ascii2filter(words):
    if isinstance(words, list):
        strings = delete_sub.sub('',' '.join(words)).split()
    else:
        strings = delete_sub.sub('',words)
    return strings


def ascii2curses(context,row,col,string, colors=None,now=0, max_width=None):
    attr = None 
    color = None
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


