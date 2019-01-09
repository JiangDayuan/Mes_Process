import codecs
import os
import tkinter
from tkinter import ttk

class piwebconfig():
    def __init__(self, file_dir, pi_txt):
        self.file_dir = file_dir
        self.example = os.path.join(file_dir, 'example.msel')
        self.search = os.path.join(file_dir, 'search.msel')
        self.txt = os.path.join(file_dir, pi_txt)
    
    def piweb_txt_parser(self):
        txt_data = {}
        with open(self.txt, 'r') as piweb:
            for line in piweb:
                key = line.split('=')[0].strip()
                value = line.split('=')[1].strip()
                if key != '':
                    txt_data[key] = value
        return txt_data
    
    def msel(self):
        serial = self.piweb_txt_parser()['SN_Number']
        ex = codecs.open(self.example, 'r', 'utf-8')
        sr = codecs.open(self.search, 'w', 'utf-8')
        for line in ex:
            if 'SH00000000000000' in line:
                line = line.replace('SH00000000000000', serial)
            sr.write(line)
        ex.close()
        sr.close()

def msel_change():
    msel_para_dir = ''
    msel_gen = piwebconfig(msel_para_dir, 'criteria.para')
    msel_gen.msel()

def go(*args):   #处理事件，*args表示可变参数  
        print(comboxlist.get()) #打印选中的值 
        
if __name__ == "__main__":
    #msel_change()
    win=tkinter.Tk() #构造窗体  
    comvalue=tkinter.StringVar()#窗体自带的文本，新建一个值  
    comboxlist=ttk.Combobox(win,textvariable=comvalue) #初始化  
    comboxlist["values"]=("1","2","3","4")  
    comboxlist.current(0)  #选择第一个  
    comboxlist.bind("<<ComboboxSelected>>",go)  #绑定事件,(下拉列表框被选中时，绑定go()函数)  
    comboxlist.pack()  
      
    win.mainloop() #进入消息循环 