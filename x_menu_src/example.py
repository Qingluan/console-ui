import os
import curses
from .menu import Tree, Text
from .menu import msgBox, Application

class FileTree(Tree):

    def get_left_cursor(self):
        p = self.cursor if not self.cursor.endswith("/") else self.cursor[:-1]
        p = os.path.dirname(p)
        return p
    
    def get_right_cursor(self):
        item = self.m.datas[self.m.ix]
        return os.path.join(self.cursor, item)
  
    def get_parent(self, cursor):
        p = self.get_left_cursor()
        return os.listdir(p)
    
    def get_sub(self, cursor, item=None):
        i = self.get_right_cursor()
        if os.path.isdir(i):
            d = os.listdir(i)
            if not d:
                d.append("")
            return  d
        return  ['']
    
    def get_current(self, cursor):
        return  os.listdir(cursor)

    def update_when_cursor_change(self, item, ch):
        s = self.get_sub(self.cursor, item)
        self.r.datas = s

        msgBox(msg="%d/%d%% %s" % (self.m.ix, self.m.height, self.cursor))

if __name__ == "__main__":
    main = Application()
    # r1 = Stack(["s"+str(i) for i in range(28)], id='1')
    # r2 = Stack(["s2"+str(i) for i in range(10)], id='2')
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
    t = FileTree(os.path.expanduser("~/Documents"))
    main.focus("middle")
    main.add_widget(e)
    curses.wrapper(main.loop)
    curses.endwin()



