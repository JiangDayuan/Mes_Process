
from tkinter import *
import tkinter.messagebox as messagebox
 
class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()
 
    def createWidgets(self):
        self.tiplabel = Label(self, text='输入“我爱你”，退出该程序')
        self.tiplabel.pack()
        self.valueInput = Entry(self)
        self.valueInput.pack()
        self.alertButton = Button(self, text='验证', command=self.proof)
        self.alertButton.pack()
 
    def proof(self):
        keyvalue = self.valueInput.get()
        
        if keyvalue == '我爱你':
            messagebox.showinfo('提示', '你的眼光很对')
            root.destroy()
        else:
            messagebox.showerror('错误', '我觉得你可以再说一次')
 
def callback():
    messagebox.showwarning('警告','回答问题')
 
root = Tk()
root.geometry('300x150')
app = Application().pack()
root.protocol("WM_DELETE_WINDOW", callback)
root.mainloop()