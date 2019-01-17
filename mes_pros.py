import codecs
import os
import csv
import json
import sys
import threading
import shutil
import argparse
import logging
import socket

from tkinter import *
import tkinter.filedialog
import tkinter.messagebox
from tkinter.filedialog import askdirectory
from subprocess import run
#from tkinter import ttk

class system_config():
    """
    1.获取程序运行的路径位置，并推导出其他常用路径的位置作为变量输出
    2.获取config.json的配置信息
    """
    CONFIG = 'config.json'
    #PARENT_FOLDER = 'Documents'#'Contract_Measurement_Process'
    def __init__(self):
        self.system_dir()
        #config.json的路径
        self.config_dir = os.path.join(self.rela_dir, self.CONFIG)

    def system_dir(self):
        """
        读取可执行文件当前的路径
        """
        paths = sys.path[0]
        self.exe_dir = paths
        self.para_dir = os.path.join(paths, 'temp')
        self.rela_dir = os.path.join(paths, 'relative_files')
        #while path.split(paths)[1] != self.PARENT_FOLDER:
        #    paths = path.split(paths)[0]
        #self.parent_dir = paths

    def config_path_reader(self):
        """
        读取config.json文件中的内容
        """
        with open(self.config_dir, 'r') as js:
            json_f = json.load(js)
        self.ai = json_f['autoimporter']
        self.data = json_f['data']
        self.server = json_f['server']

class netaccess(system_config):
    def __init__(self):
        system_config.__init__(self)
        self.config_path_reader()
        self.ai_ping = self.ai['parent'][0]
        self.ai_dir = self.ai['parent'][1]
        self.ai_user = self.ai['parent'][2]
        self.ai_pwd = self.ai['parent'][3]
        self.data_ping = self.data['parent'][0]
        self.data_dir = self.data['parent'][1]
        self.data_user = self.data['parent'][2]
        self.data_pwd = self.data['parent'][3]

    def autoimporter_access(self):
        """
        1.检查Auto Importer使用的文件夹所在服务器的连接情况
        2.使用用户名和密码登录该服务器
        """
        #ping一次地址的command
        ping_ai = 'Ping.exe -n 1 '+self.ai_ping
        #运行command并返回状态信息
        status = run(ping_ai, shell=True)
        if 'returncode=0' not in str(status):
            warn = False
        else:
            #ping通之后，使用用户名和密码登录服务器
            access = 'net use '+self.ai_dir+' /user:'+self.ai_user+' '+self.ai_pwd
            run(access, shell=True)
            warn = True
        return warn

    def fileserver_access(self):
        """
        1.检查文件服务器的连接情况
        2.使用用户名和密码登录该服务器
        """
        ping_server = 'Ping.exe -n 1 '+self.data_ping
        status = run(ping_server, shell=True)
        if 'returncode=0' not in str(status):
            warn = False
        else:
            access = 'net use '+self.data_dir+' /user:'+self.data_user+' '+self.data_pwd
            run(access, shell=True)
            warn = True
        return warn

class piwebconfig(system_config):
    def __init__(self, pi_txt):
        """
        1.输入：
            (1)pi_txt:PiWeb模板中输出的txt或para文件
            (2)max_attribute:创建的csv文件应用配置的测量特性数
            (3)example:msel的模板
        """
        system_config.__init__(self)
        self.txt = os.path.join(self.para_dir, pi_txt)
        self.piweb_txt_parser()

    def piweb_txt_parser(self):
        """
        将创建实例时输入的txt或para文件中的信息转换成字典，并输出
        1.输入：None
        2.输出：字典
        """
        txt_data = {}
        with open(self.txt, 'r') as piweb:
            for line in piweb:
                key = line.split('=')[0].strip()
                value = line.split('=')[1].strip()
                if key != '':
                    txt_data[key] = value
        os.remove(self.txt)
        self.txt_data = txt_data

    def msel(self, example='example.msel', search='search.msel'):
        """
        将模板msel文件中的序列号值修改为criteria.para中包含的序列号
        1.输入：
            (1)example:msel的模板
            (2)search:输出的msel
        2.输出：search.msel
        """
        #创建输入和输出msel文件的完整路径
        example = os.path.join(self.para_dir, example)
        search = os.path.join(self.para_dir, search)
        #获得txt或para文件中的序列号
        serial = self.txt_data['Serial_Number']
        #将txt或para文件中的序列号写入输出的msel文件中
        ex = codecs.open(example, 'r', 'utf-8')
        sr = codecs.open(search, 'w', 'utf-8')
        for line in ex:
            if 'SH00000000000000' in line:
                line = line.replace('SH00000000000000', serial)
            sr.write(line)
        ex.close()
        sr.close()

    def csv_generate(self, csv_data=None, ctl_info=None, max_attribute=30):
        """
        创建csv文件，准备上传到PiWeb Auto Importer中
        1.输入:
            (1)csv_data:字典，包含需要生成csv中测量特性的内容，
                        默认None，如果为None则使用创建实例时输入的txt或para文件生成的字典
            (2)ctl_info:字典，包含需要创建探针的信息
        2.输出:
            输出一个保存在Local_Temp中的csv文件
        """
        #csv文件的保存路径(config.json中的temp路径)
        #如果没有输入就读取创建实例时选择的文件来生成csv_data字典
        if csv_data==None:
            csv_data = self.txt_data
        #如果文件中存在‘Serial_Number’,则使用序列号作为csv的文件名
        csv_name = csv_data['Serial_Number']+'.csv'
        self.config_path_reader()
        target_dir = self.data['temp'] #csv文件的保存路径(config.json中的temp路径)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        self.csv_dir = os.path.join(target_dir, csv_name)
        #为了获取统一配置，设置足够多的Measurement Attribute,不足的数量填入空值
        empty_number = max_attribute - len(csv_data)
        #将txt或para文件的内容转换成csv的格式
        with open(self.csv_dir, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for key, value in csv_data.items():
                writer.writerow([key,value])
            #如果Measurement Attribute数量不足，则自动补充
            while empty_number > 0:
                writer.writerow(['Empty', 'None'])
                empty_number -= 1
            #添加Measurement Value Attribute
            writer.writerow(['Mes_Info', 0])
            #添加储存探针信息的Measurement Value Attribute
            if ctl_info != None:
                for key, value in ctl_info.items():
                    if key != "fixture":
                        writer.writerow(["Probe_Info", key, value[2]])


class UI(Tk, system_config):
    def __init__(self):
        super().__init__()
        system_config.__init__(self)
        #设置窗体参数：大小不可改变、长宽根据内容变化、使用ico
        self.resizable(0, 0)
        self.geometry()
        self.iconbitmap(os.path.join(self.rela_dir,'flow.ico'))
        self.process = StringVar()  #设置一个显示状态的动态变量

    def selectFile(self, path):
        """
        浏览选择一个文件
        """
        path__ = []
        path_ = tkinter.filedialog.askopenfilenames()
        for pa in path_:
            if '/' in pa:
                path__.append(pa.replace('/','\\'))
        path.set(';'.join(path__))

    def ErrorShow(self):
        """
        出现一个显示错误信息的窗口
        需要在调用之前修改self.process的内容作为报错内容
        """
        self.title('错误信息')
        Label(self,text="",width=5,height=2).grid(row=0,column=0)
        Label(self,textvariable=self.process,width=40).grid(row=1,column=1)
        Label(self,text="",width=5,height=2).grid(row=2,column=2)

    def UI_Create(self):
        self.report_path = StringVar()
        self.report_path.set("")
        Label(self,text="",width=2).grid(row=0,column=0)
        Label(self,text="请选择测量报告(可多选):",height=1).grid(row=1,column=1,sticky=W)
        Entry(self,textvariable=self.report_path,width=60).grid(row=2,column=1,sticky=W)
        Label(self,text="",width=1).grid(row=2,column=2)
        Button(self,text="浏览",command=lambda :self.selectFile(self.report_path), relief=GROOVE, width=6, height=1).grid(row=2,column=3,sticky=E)
        Label(self,text="",width=2).grid(row=2,column=4)
        Label(self,text="",width=2).grid(row=3,column=0)


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def thread_it(func, *args):
    """
    Start a new thread for Fuction
    """
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)
    t.start()
    # t.join()

def msel_change():
    msel_gen = piwebconfig('criteria.para')
    msel_gen.msel()

def get_input_args():
    parser = argparse.ArgumentParser(description='Retrieve some parameters')
    #设置数据目录:
    parser.add_argument('step', type=str,
                        help='获取PiWeb输出的arguments')
    return parser.parse_args()

def assignment_data():
    """
    第一步：派工
    """
    logger1 = logging.getLogger('Assignment')
    logger1.setLevel(logging.DEBUG)
    fh = logging.FileHandler('test.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger1.addHandler(fh)
    try:
        #将assignment.para转换成csv文件
        assign = piwebconfig('assignment.para')
        assign.csv_generate()
        logger1.info('assignment.para成功转换并保存为{}'.format(assign.csv_dir))
        #检查Auto Importer使用的文件夹所在服务器的连接情况
        net = netaccess()
        if True:#net.autoimporter_access():
            #连接成功后，检查Auto Importer文件夹是否存在，不存在则创建
            logger1.info('({})网络连接成功'.format(net.ai_ping))
            mkdir(assign.ai['userlist'])
            mkdir(assign.ai['server'])
            #将csv发送到Auto Importer文件夹
            shutil.copy(assign.csv_dir, assign.ai['userlist'])
            logger1.info('{}成功上传至{}'.format(assign.csv_dir, assign.ai['userlist']))
            shutil.copy(assign.csv_dir, assign.ai['server'])
            logger1.info('{}成功上传至{}'.format(assign.csv_dir, assign.ai['server']))
        else:
            #如果连接不成功，则将csv复制到import failure文件夹
            mkdir(assign.data['failure'])
            shutil.copy(assign.csv_dir, os.path.join(assign.data['failure']))
            #显示网络连接不成功的信息
            logger1.error("({})网络连接失败,请检查网络后再试".format(net.ai_ping))
            ui = UI()
            ui.process.set("({})网络连接失败,请检查网络后再试".format(net.ai_ping))
            ui.ErrorShow()
            ui.mainloop()
    except FileNotFoundError:
        logger1.error("没有检测到PiWeb生成的数据")
        ui = UI()
        ui.process.set("没有检测到PiWeb生成的数据")
        ui.ErrorShow()
        ui.mainloop()
    except shutil.Error as e:
        logger1.error('文件传输出现异常\n{}'.format(e))
        ui = UI()
        ui.process.set('文件传输出现异常\n{}'.format(e))
        ui.ErrorShow()
        ui.mainloop()
    except KeyError:
        logger1.error('PiWeb文件格式错误，不包含序列号信息')
        ui = UI()
        ui.process.set('PiWeb文件格式错误，不包含序列号信息')
        ui.ErrorShow()
        ui.mainloop()
    else:
        os.remove(assign.csv_dir)
    finally:
        temp_dir = system_config()
        file_list = os.listdir(temp_dir.para_dir)
        if len(file_list) != 0:
            for file in file_list:
                os.remove(os.path.join(temp_dir.para_dir, file))

def json_config():
    a = {
        'autoimporter':
        {
            'parent': ['10.202.0.200', r'\\10.202.0.200\shcc', 'shcc', 'Sh@12345'],
            'userlist': r'C:\Temp\UserList',
            'server': r'C:\Temp\Contract_Measurement'
        },
        'data':
        {
            'parent': ['10.202.0.200', r'\\10.202.0.200\shcc', 'shcc', 'Sh@12345'],
            'backup': r'C:\Demo_Data\Contract_Measurement',
            'temp': r'C:\Demo_Data\Local_Temp',
            'failure': r'C:\Demo_Data\Import_Failure'
        },
        'server':
        {
            'userlist': r'C:\Server\User_List.dfm',
            'programlist': r'C:\Server\Program_List.dfm',
            'main': r'http://10.202.0.200:8088'
        }
        }
    with open(r'relative_files\config.json', 'w') as j:
        json.dump(a, j, sort_keys=False, indent=2)

def main():
    logger0 = logging.getLogger('Arguments')
    logger0.setLevel(logging.DEBUG)
    fh = logging.FileHandler('test.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger0.addHandler(fh)
    #开始读取Monitor传输的
    in_arg = get_input_args()
    if in_arg.step == 'assignment':
        logger0.info("Argument获取正确，运行派工程序")
        assignment_data()
        #shutil.copyfile('assignment.para', r'temp\assignment.para')
    elif in_arg.step == 'handover':
        logger0.info("Argument获取正确，运行交接程序")
        pass

    else:
        logger0.error("Argument获取不正确: {}".format(in_arg.step))
        ui = UI()
        ui.process.set("Argument获取不正确: {}".format(in_arg.step))
        ui.ErrorShow()
        ui.mainloop()

if __name__ == "__main__":
    #main()
    hostname = socket.gethostname()
    addrs = socket.getaddrinfo(hostname,None)
    for item in addrs:
        print(item)
    pass
