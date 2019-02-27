import codecs
import os
import time
import csv
import json
import sys
import threading
import shutil
import argparse
import logging

import uuid
import requests
import base64

from tkinter import *
import tkinter.filedialog
import tkinter.messagebox
from tkinter.filedialog import askdirectory
from subprocess import run
#from tkinter import ttk

# CLASS
##################------------------读取系统配置信息------------------##################


class system_config():
    """
    1.获取程序运行的路径位置，并推导出其他常用路径的位置作为变量输出
    2.获取config.json的配置信息
    """
    CONFIG = 'config.json'
    # PARENT_FOLDER = 'Documents'#'Contract_Measurement_Process'

    def __init__(self):
        self.system_dir()
        # config.json的路径
        self.config_dir = os.path.join(self.rela_dir, self.CONFIG)

    def system_dir(self):
        """
        读取可执行文件当前的路径
        """
        paths = sys.path[0]
        self.exe_dir = paths
        self.para_dir = os.path.join(paths, 'temp')
        self.rela_dir = os.path.join(paths, 'relative_files')
        # while path.split(paths)[1] != self.PARENT_FOLDER:
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
        self.host = json_f['host']

##################------------------检查网络连接------------------##################


class netaccess(system_config):
    def __init__(self):
        system_config.__init__(self)
        self.config_path_reader()

    def autoimporter_access(self):
        """
        1.检查Auto Importer使用的文件夹所在服务器的连接情况
        2.使用用户名和密码登录该服务器
        """
        self.ai_ping = self.ai['parent'][0]
        self.ai_dir = self.ai['parent'][1]
        self.ai_user = self.ai['parent'][2]
        self.ai_pwd = self.ai['parent'][3]
        # ping一次地址的command
        ping_ai = 'Ping.exe -n 1 '+self.ai_ping
        # 运行command并返回状态信息
        status = run(ping_ai, shell=True)
        if 'returncode=0' not in str(status):
            warn = False
        else:
            # ping通之后，使用用户名和密码登录服务器
            access = 'net use '+self.ai_dir+' /user:'+self.ai_user+' '+self.ai_pwd
            run(access, shell=True)
            warn = True
        return warn

    def fileserver_access(self):
        """
        1.检查文件服务器的连接情况
        2.使用用户名和密码登录该服务器
        """
        self.data_ping = self.data['parent'][0]
        self.data_dir = self.data['parent'][1]
        self.data_user = self.data['parent'][2]
        self.data_pwd = self.data['parent'][3]
        # ping一次文件服务器的IP地址
        ping_server = 'Ping.exe -n 1 '+self.data_ping
        status = run(ping_server, shell=True)
        # 检查返回状态
        if 'returncode=0' not in str(status):
            warn = False
        else:
            access = 'net use '+self.data_dir+' /user:'+self.data_user+' '+self.data_pwd
            run(access, shell=True)
            warn = True
        return warn

    def piwebserver_access(self):
        # Ping一次PiWeb服务器的地址
        ping_piweb = 'Ping.exe -n 1 ' + self.host['ip']
        status = run(ping_piweb, shell=True)
        # 检查返回状态
        print(str(status))
        if 'returncode=0' not in str(status):
            warn = False
        else:
            warn = True
        return warn


##################------------------PiWeb模板导出信息读取和转换------------------##################


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
        # 创建输入和输出msel文件的完整路径
        example = os.path.join(self.para_dir, example)
        search = os.path.join(self.para_dir, search)
        # 获得txt或para文件中的序列号
        serial = self.txt_data['Serial_Number']
        # 将txt或para文件中的序列号写入输出的msel文件中
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
        # csv文件的保存路径(config.json中的temp路径)
        # 如果没有输入就读取创建实例时选择的文件来生成csv_data字典
        if csv_data == None:
            csv_data = self.txt_data
        # 使用序列号作为csv的文件名
        csv_name = csv_data['Serial_Number']+'.csv'
        self.config_path_reader()
        target_dir = self.data['temp']  # csv文件的保存路径(config.json中的temp路径)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        self.csv_dir = os.path.join(target_dir, csv_name)
        # 为了获取统一配置，设置足够多的Measurement Attribute,不足的数量填入空值
        empty_number = max_attribute - len(csv_data)
        # 将txt或para文件的内容转换成csv的格式
        with open(self.csv_dir, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for key, value in csv_data.items():
                writer.writerow([key, value])
            # 如果Measurement Attribute数量不足，则自动补充
            while empty_number > 0:
                writer.writerow(['Empty', 'None'])
                empty_number -= 1
            # 添加Measurement Value Attribute
            writer.writerow(['Mes_Info', 0])
            # 添加储存探针信息的Measurement Value Attribute
            if ctl_info != None:
                for key, value in ctl_info.items():
                    if key != "fixture":
                        writer.writerow(["Probe_Info", key, value[2]])

##################------------------PiWeb API调用------------------##################


class PiWebAPI():
    MIME = {'.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.meshModel': 'application/x-zeiss-piweb-meshmodel',
            '.json': 'application/json;charset=utf-8'}
    REST = '/dataServiceRest'
    RAW = 'rawDataServiceRest/rawData'
    PART = '/parts'
    MES = '/measurements'
    VAL = '/values'

    def __init__(self, host):
        self.host = host
        self.meas_post = self.host + self.REST + self.MES

    def authentication(self, auth='Administrator:adm!n!strat0r'):
        access = base64.b64encode(auth.encode())
        return access.decode()

    def measurements_url(self, partPath=None, order=None, serCon=None, limitResult=None, attributes=[]):
        """
        partPath: 最终格式：'partPath=/partname/' 输入格式：/partname/
        order: 最终格式：'orderBy=4 asc(desc)' 输入格式：4 asc
        """
        # 设置measurement的endpoints
        endpoints = self.REST + self.MES
        para = []
        if partPath != None:
            partPath = 'partPath={}'.format(partPath)  # partPath=/jfy/
            para.append(partPath)
        if order != None:
            order = 'orderBy={}'.format(order)
            para.append(order)
        if serCon != None:
            serCon = 'searchCondition={}'.format(serCon)
            para.append(serCon)
        if limitResult != None:
            limitResult = 'limitResult={}'.format(limitResult)
            para.append(limitResult)
        if len(attributes) != 0:
            rMA = 'requestedMeasurementAttributes={' + \
                ','.join(attributes) + '}'
            para.append(rMA)
        parameter = '?'+'&'.join(para)
        self.mes_url = self.host + endpoints + parameter

    def parts_url(self, partPath=None, depth=1, requestedPartAttributes=None):
        endpoints = self.REST + self.PART
        para = []
        if partPath != None:
            partPath = 'partPath={}'.format(partPath)  # partPath=/jfy/
            para.append(partPath)
        depth = 'depth={}'.format(depth)
        if requestedPartAttributes != None:
            requestedPartAttributes = 'requestedPartAttributes={' + \
                requestedPartAttributes+'}'
        parameter = '?'+'&'.join(para)
        self.part_url = self.host + endpoints + parameter

    def GET(self, url):
        req = requests.get(url)
        if req.status_code == 200:
            return json.loads(req.text)

    def Mes_POST(self, mes_data):
        """
        mes_data:输入一个字典型
        """
        body = \
            [
                {
                    'uuid': str(uuid.uuid1()),
                    'partUuid': self.partUuid,
                    'attributes': mes_data
                }
            ]
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        r = requests.post(self.meas_post, headers=headers,
                          data=json.dumps(body))
        return r.status_code

    def Mes_PUT(self, mes_data):
        """
        mes_data:输入一个字典型
        更新测量属性
        """
        body = \
            [
                {
                    'uuid': uuid,
                    'partUuid': self.partUuid,
                    'attributes': mes_data
                }
            ]
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        r = requests.put(self.meas_post, headers=headers,
                          data=json.dumps(body))
        print(r.status_code)

    def mes_uuid(self):
        data = self.GET(self.mes_url)
        if len(data) == 1:
            self.uuid = data['uuid']
            self.partUuid = data['partUuid']
        elif len(data) > 1:
            uuid = []
            for d in data:
                uuid.append(d['uuid'])
        print(uuid)

    def CreateNewMeasurement(self, mes_data, partPath=None, order=None, serCon=None, limitResult=None, attributes=[]):
        self.parts_url(partPath)
        self.partUuid = self.GET(self.part_url)[0]['uuid']
        result = self.Mes_POST(mes_data)
        return result

    def UpdateMeasurement(self, mes_data, partPath=None):
        # 获得part的uuid
        # 获得这个part下需要更新的那次测量的uuid
        # put这个uuid
        pass

    def RawDataPost(self, url, file_path):
        file_name = os.path.basename(file_path)
        extension = os.path.splitext(file_name)
        files = open(file_path, 'rb')
        headers = {}
        headers['Content-Disposition'] = 'attachment;filename={}'.format(
            file_name)
        if extension in self.MIME.keys():
            headers['Content-Type'] = self.MIME[extension]
        r = requests.post(url, data=files, headers=headers)
        if r.status_code == 201:
            print("附件上传成功")
        else:
            print(r.text)

##################------------------交互界面UI显示------------------##################


class UI(Tk, system_config):
    def __init__(self):
        super().__init__()
        system_config.__init__(self)
        # 设置窗体参数：大小不可改变、长宽根据内容变化、使用ico
        self.resizable(0, 0)
        self.geometry()
        self.iconbitmap(os.path.join(self.rela_dir, 'flow.ico'))
        self.process = StringVar()  # 设置一个显示状态的动态变量

    def selectFile(self, path):
        """
        浏览选择一个文件
        """
        path__ = []
        path_ = tkinter.filedialog.askopenfilenames()
        for pa in path_:
            if '/' in pa:
                path__.append(pa.replace('/', '\\'))
        path.set(';'.join(path__))

    def ErrorShow(self):
        """
        出现一个显示错误信息的窗口
        需要在调用之前修改self.process的内容作为报错内容
        """
        self.title('错误信息')
        Label(self, text="", width=5, height=2).grid(row=0, column=0)
        Label(self, textvariable=self.process, width=40).grid(row=1, column=1)
        Label(self, text="", width=5, height=2).grid(row=2, column=2)

    def UI_Create(self):
        self.report_path = StringVar()
        self.report_path.set("")
        Label(self, text="", width=2).grid(row=0, column=0)
        Label(self, text="请选择测量报告(可多选):", height=1).grid(
            row=1, column=1, sticky=W)
        Entry(self, textvariable=self.report_path,
              width=60).grid(row=2, column=1, sticky=W)
        Label(self, text="", width=1).grid(row=2, column=2)
        Button(self, text="浏览", command=lambda: self.selectFile(self.report_path),
               relief=GROOVE, width=6, height=1).grid(row=2, column=3, sticky=E)
        Label(self, text="", width=2).grid(row=2, column=4)
        Label(self, text="", width=2).grid(row=3, column=0)


##################------------------Calypso测量程序备份------------------##################


class InspectionBackup(system_config):
    def __init__(self, program_data, level):
        system_config.__init__(self)
        self.program_data = program_data
        self.level = level
        self.program_path = self.program_data['Program_Path']
        self.program_name = os.path.basename(self.program_path)
        self.backup_dir()
        # 获得测量程序中inspection文件的路径
        self.new_inspection = os.path.join(self.program_path, 'inspection')
        self.exist_inspection = os.path.join(self.target_dir, 'inspection')

    def backup_dir(self):
        self.config_path_reader()
        self.target_dir = self.data['backup']
        for n in range(self.level):
            key = 'Level{}'.format(n+1)
            value = self.program_data.pop(key)
            if value != '':
                self.target_dir = os.path.join(self.target_dir, value)
        self.program_dir = os.path.join(self.target_dir, self.program_name)

    def content_check(self):
        # 检查程序路径是否未空
        if self.program_path == '':
            message = "未填写测量程序的路径"
        # 检查程序路径是否存在
        elif not os.path.exists(self.program_path):
            message = "所填写的测量程序路径不存在"
        # 检查程序路径是否为空文件夹
        elif len(os.listdir(self.program_path)) == 0:
            message = "所填写的程序目录下没有文件"
        #elif os.path.getmtime(self.new_inspection) == os.path.getmtime(self.exist_inspection):
        #    message = "所备份的测量程序与服务器中的测量程序相同"
        else:
            message = True
        return message

    def history_dir(self):
        # 获取当前时间作为备份程序的后缀名
        #modi_time = os.path.getmtime(self.exist_inspection)
        time_suffix = time.strftime(
            '_%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
        history_name = self.program_name + time_suffix
        # 设置历史版本的路径
        self.history_path = os.path.join(
            self.target_dir, 'history_version', history_name)
        
    def backup(self):
        # 在备份程序前，先检查原有的程序是否存在，如果存在，则将原有的程序删除
        if os.path.exists(self.program_dir):
            shutil.rmtree(self.program_dir)
        #将新程序从本地复制到文件服务器
        shutil.copytree(self.program_path, self.program_dir)


# Method
##################------------------通用方法------------------##################
def job_number():
    """
    创建工单号
    """
    current_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    return 'JOB' + current_time


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
    """
    设置程序Argument。
    强制argument：step(用来获取运行那一部分程序)
    """
    parser = argparse.ArgumentParser(description='Retrieve some parameters')
    # 设置数据目录:
    parser.add_argument('step', type=str,
                        help='获取PiWeb输出的arguments')

    parser.add_argument('--level', type=int, default=6)

    parser.add_argument('--initial', type=str, default='assignment.para')

    parser.add_argument('--gpu', action ='store_true',
                        help='use gpu')
    return parser.parse_args()


def showError(errorInfo):
    """
    用来弹出错误信息的窗口，窗口中显示的提示内容为：errorInfo
    """
    ui = UI()
    ui.process.set(errorInfo)
    ui.ErrorShow()
    ui.mainloop()

##################------------------系统流程方法------------------##################

def parafile_delete(para):
    """
    在流程运行中放弃本次操作，需要把PiWeb生成的数据删除时
    使用这个方法
    """
    # 检查Temp文件夹下是否存在指定名字的数据文件
    if os.path.exists(para):
        # 如果存在，则删除该文件
        os.remove(para)


def job_assignment(log_path):
    """
    目的：完成qFlow中的简单派工功能
    """
    # 设置logger
    logger1 = logging.getLogger('Assignment')
    logger1.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger1.addHandler(fh)
    logger1.info("成功进入派工子程序")
    try:
        assign = piwebconfig('assignment.para')
        logger1.info("成功读取assignment.para文件")
        assign_info = assign.txt_data
        logger1.info("成功读取assignment.para中的信息")
        # 生成测量任务的工单号，并添加到测量Attribute中
        assign_info['22250'] = job_number()
        logger1.info("派工工单号{}获取".format(assign_info['22250']))
        # 检查本机与PiWeb服务器的网络链接
        net = netaccess()
        if net.piwebserver_access():
            logger1.info('PiWeb数据库({})连接成功'.format(net.host['main']))
            API = PiWebAPI(net.host['main'])
            API.CreateNewMeasurement(assign.txt_data, partPath='/Job_Management/')
    except FileNotFoundError:
        message = "没有检测到PiWeb生成的数据"
        logger1.error(message)
        showError(message)


def assignment_data(log_path):
    """
    第一步：派工
    """
    logger1 = logging.getLogger('Assignment')
    logger1.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger1.addHandler(fh)
    try:
        # 将assignment.para转换成csv文件
        assign = piwebconfig('assignment.para')
        assign.csv_generate()
        logger1.info('assignment.para成功转换并保存为{}'.format(assign.csv_dir))
        # 检查Auto Importer使用的文件夹所在服务器的连接情况
        net = netaccess()
        if net.autoimporter_access():
            # 连接成功后，检查Auto Importer文件夹是否存在，不存在则创建
            logger1.info('({})网络连接成功'.format(net.ai_ping))
            mkdir(assign.ai['userlist'])
            mkdir(assign.ai['server'])
            # 将csv发送到Auto Importer文件夹
            shutil.copy(assign.csv_dir, assign.ai['userlist'])
            logger1.info('{}成功上传至{}'.format(
                assign.csv_dir, assign.ai['userlist']))
            shutil.copy(assign.csv_dir, assign.ai['server'])
            logger1.info('{}成功上传至{}'.format(
                assign.csv_dir, assign.ai['server']))
        else:
            # 如果连接不成功，则将csv复制到import failure文件夹
            mkdir(assign.data['failure'])
            shutil.copy(assign.csv_dir, os.path.join(assign.data['failure']))
            # 显示网络连接不成功的信息
            message = "({})网络连接失败,请检查网络后再试".format(net.ai_ping)
            logger1.error(message)
            showError(message)
    except FileNotFoundError:
        message = "没有检测到PiWeb生成的数据"
        logger1.error(message)
        showError(message)
    except shutil.Error as e:
        message = '文件传输出现异常\n{}'.format(e)
        logger1.error(message)
        showError(message)
    except KeyError:
        message = 'PiWeb文件格式错误，不包含序列号信息'
        logger1.error(message)
        showError(message)
    else:
        os.remove(assign.csv_dir)
    finally:
        temp_dir = system_config()
        file_list = os.listdir(temp_dir.para_dir)
        if len(file_list) != 0:
            for file in file_list:
                os.remove(os.path.join(temp_dir.para_dir, file))

def inspection_backup(level):
    """
    备份测量程序
    """
    logger2 = logging.getLogger('Backup')
    logger2.setLevel(logging.DEBUG)
    fh = logging.FileHandler('test.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger2.addHandler(fh)
    try:
        # 读取PiWeb模板中导出的数据文件
        inspection = piwebconfig('inspection.para')
        logger2.info('成功读取inspection.para中的信息')
        # 检查网络连接
        net = netaccess()
        if True:  # net.fileserver_access():
            # 连接成功如果连接成功，则开始执行程序备份功能
            logger2.info('文件服务器连接成功')
            ins = InspectionBackup(inspection.txt_data, level)
            # 检查测量程序的内容是否正确
            if ins.content_check():
                logger2.info('inspection.para信息正确')
                # 检查文件服务器中是否存在已有程序
                if not os.path.exists(ins.program_dir):
                    # 如果不存在，则直接复制程序
                    logger2.info('{}为新程序，开始备份测量程序'.format(os.path.basename(ins.exist_inspection)))
                    ins.backup()
                    logger2.info('新程序备份成功')
                else:
                    # 如果存在，则上传更新程序，并将已有程序存成历史版本
                    logger2.info('备份程序为已存在程序，开始备份测量程序')
                    # 创建历史版本的路径
                    ins.history_dir()
                    logger2.info('成功创建版本管理路径')
                    if not os.path.exists(ins.history_path):
                        #os.makedirs(ins.history_path)
                        shutil.copytree(ins.program_dir, ins.history_path)
                        ins.backup()
                        logger2.info('将原有程序保存为历史版本{}'.format(os.path.basename(ins.history_path)))
                    else:
                        message = "备份时间重合，请稍后再试"
                        logger2.error(message)
                        showError(message)
            else:
                logger2.error(message)
                showError(ins.content_check())
        else:
            message = "({})网络连接失败,请检查网络后再试".format(net.data_ping)
            logger2.error(message)
            showError(message)
    except FileNotFoundError:
        message = "没有检测到PiWeb生成的数据"
        logger2.error(message)
        showError(message)
    except shutil.Error as e:
        message = "文件传输出现异常"
        logger2.error(message+':'+e)
        showError(message)
    except Exception as e:
        logger2.error(e)
        showError("程序崩溃了，请查看log文件")


def json_config():
    a = {
        'autoimporter':
        {
            'parent': ['10.202.0.9', r'\\10.202.0.9\shcc', 'shcc', 'Sh@12345'],
            'userlist': r'C:\Temp\UserList',
            'server': r'C:\Temp\Contract_Measurement'
        },
        'data':
        {
            'parent': ['10.202.0.9', r'\\10.202.0.9\shcc', 'shcc', 'Sh@12345'],
            'backup': r'C:\Demo_Data\Contract_Measurement',
            'temp': r'C:\Demo_Data\Local_Temp',
            'failure': r'C:\Demo_Data\Import_Failure',
            'log': r'C:\Demo_Data\Import_Failure'
        },
        'host':
        {
            'ip': 'localhost',
            'userlist': r'C:\Server\User_List.dfm',
            'main': r'http://localhost:8084'
        }
    }
    with open(r'relative_files\config.json', 'w') as j:
        json.dump(a, j, sort_keys=False, indent=2)


def main():
    # 读取配置文件中的信息和程序路径
    sys_info = system_config()
    sys_info.config_path_reader()
    # 设置log文件存储的位置
    log_path = os.path.join(sys_info.data['log'], 'qFlow.log')
    # 设置主程序的logger
    logger0 = logging.getLogger('Arguments')
    logger0.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger0.addHandler(fh)
    # 开始读取Monitor传输的arguments
    in_arg = get_input_args()
    if in_arg.step == 'assignment':
        logger0.info("Argument:'{}'获取正确，运行派工程序".format(in_arg.step))
        job_assignment(log_path)
        #shutil.copyfile('assignment.para', r'temp\assignment.para')
    elif in_arg.step == 'initialize':
        logger0.info("Argument:'{}'获取正确，运行交接程序".format(in_arg.step))
        file_path = os.path.join(sys_info.para_dir, in_arg.initial)
        logger0.info("获取需要初始化的数据文件路径{}".format(file_path))
        parafile_delete(file_path)
    elif in_arg.step == 'backup':
        logger0.info("Argument:'{}'获取正确，运行测量程序备份程序".format(in_arg.step))
        inspection_backup(in_arg.level)
    else:
        message = "Argument获取不正确: {}".format(in_arg.step)
        logger0.error(message)
        showError(message)


if __name__ == "__main__":
    main()
    #api = PiWebAPI('http://localhost:8084')
    #api.measurements_url(partPath='/Demo/', order='20041 asc', serCon='14In[NB20190103150613]', attributes=['20041', '850'])
    # api.mes_uuid()
    # print(uuid.uuid1())
    #api.CreateNewMeasurement(mes_data={'12':'Prismo'}, partPath='/Machine_List/')
    #api.CreateNewMeasurement(mes_data={'12':'Acura'}, partPath='/Machine_List/')
    #api.CreateNewMeasurement(mes_data={'12':'Contura'}, partPath='/Machine_List/')
    #shutil.copyfile('assignment.para', r'temp\assignment.para')
    # main()
    #hostname = socket.gethostname()
    #addrs = socket.getaddrinfo(hostname,None)
    # for item in addrs:
    #    print(item)
    pass
