import curses
from .menu import Application, Stack, CheckBox, msgBox, Text, Menu
from .event import listener
class Test(Stack):

    @listener(10)
    def enter(self):
        res = Menu.Popup(["hello", "world", "这个是什么时代的啊啊啊啊","exit"], context=self)
        msgBox(msg=res)
    
    @listener('i')
    def info_item(self):
        Text.Popup(content="this is a test !!!",context=self, width=40)

if __name__ =="__main__":
    main = Application()
    import random
    
    r1 = CheckBox({"hello for no: "+str(i):random.randint(0,1) for i in range(138)}, id='check')
    r2 = Test(["random test ... s2"+str(i) for i in range(50)], id='2')
    r3 = Test(["you can ? to see"+str(i) for i in range(160)], id='3')
    r4 = Test(["vim keymap to move "+str(i) for i in range(270)], id='4')
    r5 = Test(["s3"+str(i) for i in range(270)], id='5')
    # e = Menu(["a", "b", "c", "exit"], id='s', x=30, y =30)
    main.add_widget(r1)
    main.add_widget(r2)
    main.add_widget(r3)
    main.add_widget(r4)
    main.add_widget(r5, weight=0.5)
    # main.add_widget(t)
    
    # tl = FileTree(os.listdir(os.path.expanduser("~/")), root_path=os.path.expanduser("~/"), id='left')
    # tm = FileTree(os.listdir(os.path.expanduser("~/Documents")), path_root=os.path.expanduser("~/Documents"), id='middle')
    # tr = FileTree([''], id='right')

    # main.add_widget(tl,weight=1)
    # main.add_widget(tm,weight=2)
    # main.add_widget(tr,weight=3)
    
    
    # main.add_widget(e)
    main.focus("2")
    curses.wrapper(main.loop)

