import codecs
import os
import time
import datetime
import csv
import json
import sys
import threading
import multiprocessing
import shutil
import argparse
import logging
import getpass
from collections import Counter

import ctypes
import inspect

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
        # 返回exe所在路径的上一层路径
        program_files = os.path.split(paths)[0]
        self.qFlow = os.path.split(program_files)[0]
        self.machine_interface_dir = os.path.join(program_files, 'Machine_Interface')
        self.para_dir = os.path.join(program_files, 'temp')
        self.rela_dir = os.path.join(program_files, 'relative_files')
        self.assign_dir = os.path.join(self.qFlow, 'Task_Assgin')

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
            intial = 'net use {} /delete /y'.format(self.ai_dir)
            run(intial, shell=True)
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
            intial = 'net use {} /delete /y'.format(self.data_dir)
            run(intial, shell=True)
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
    def __init__(self, pi_txt, keep=False, empty_dump=True):
        """
        1.输入：
            (1)pi_txt:PiWeb模板中输出的txt或para文件
            (2)max_attribute:创建的csv文件应用配置的测量特性数
            (3)example:msel的模板
        """
        system_config.__init__(self)
        self.keep = keep
        self.empty_dump = empty_dump
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
                if self.empty_dump:
                    if key != '' and value !='':
                        txt_data[key] = value
                else:
                    txt_data[key] = value
        self.txt_data = txt_data
        if not self.keep:
            os.remove(self.txt)
        

    def msel(self, example='example.msel', search='search.msel'):
        """
        将模板msel文件中的序列号值修改为criteria.para中包含的序列号
        1.输入：
            (1)example:msel的模板
            (2)search:输出的msel
        2.输出：search.msel
        """
        # 创建输入和输出msel文件的完整路径
        example = os.path.join(self.rela_dir, example)
        search = os.path.join(self.para_dir, search)
        # 获得txt或para文件中的序列号
        serial = self.txt_data['22250']
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
    RAW = '/rawDataServiceRest/rawData'
    PART = '/parts'
    CHAR = '/characteristics'
    MES = '/measurements'
    VAL = '/values'

    def __init__(self, host):
        self.host = host
        # http://10.202.120.59:8888/dataServiceRest/measurements
        self.meas_post = self.host + self.REST + self.MES
        self.value_post = self.host + self.REST + self.VAL

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

    def chars_url(self, partPath=None):
        endpoints = self.REST + self.CHAR
        para = []
        if partPath != None:
            partPath = 'partPath={}'.format(partPath)  # partPath=/jfy/
            para.append(partPath)
        parameter = '?'+'&'.join(para)
        self.char_url = self.host + endpoints + parameter

    def ValueRawData_url(self, mes_uuid, char_uuid):
        endpoints = self.RAW + '/value/'
        val_uuid = mes_uuid+'|'+char_uuid
        self.valRaw_url = self.host + endpoints + val_uuid
        print(self.valRaw_url) ###################

    def GET(self, url):
        req = requests.get(url)
        self.GET_code = req.status_code
        self.GET_Text = json.loads(req.text)

    def Val_POST(self, mes_data, value_data={}):
        """
        mes_data:输入一个字典型
        """
        self.newuuid = str(uuid.uuid1())
        body = \
            [
                {
                    'uuid': self.newuuid,
                    'partUuid': self.partUuid,
                    'attributes': mes_data,
                    'characteristics': value_data
                }
            ]
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        r = requests.post(self.value_post, headers=headers,
                          data=json.dumps(body))
        self.Mes_POST_code, self.Mes_POST_text = r.status_code, r.text

    def Mes_POST(self, mes_data, value_data=None):
        """
        mes_data:输入一个字典型
        """
        self.newuuid = str(uuid.uuid1())
        body = \
            [
                {
                    'uuid': self.newuuid,
                    'partUuid': self.partUuid,
                    'attributes': mes_data
                }
            ]
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        r = requests.post(self.meas_post, headers=headers,
                          data=json.dumps(body))
        self.Mes_POST_code, self.Mes_POST_text = r.status_code, r.text

    def Mes_PUT(self, mes_data, uuid):
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
        self.Mes_PUT_code, self.Mes_PUT_text = r.status_code, r.text

    def GetMeasurementAttribute(self, getattribute=[], partPath=None, order=None, serCon=None, limitResult=None, attributes=[]):
        # 根据筛选条件设置url
        self.measurements_url(partPath, order, serCon, limitResult, attributes)
         # 通过url GET数据
        self.GET(self.mes_url)
        if self.GET_code == 200 and len(self.GET_Text) != 0:
            self.Mes_GET_code = 200
            all_data = self.GET_Text
            # 可能会修改多条数据，将每一条数据逐一拆分
            self.MeaAtt = {}
            for att in getattribute:
                self.MeaAtt[att] = []
                for data in all_data:
                    # 获取现有的特性
                    if att in data['attributes'].keys():
                        attributes = data['attributes'][att]
                        self.MeaAtt[att].append(attributes)
        elif self.GET_code == 200 and len(self.GET_Text) == 0:
            self.Mes_GET_code = 300
            self.Mes_GET_text = 'GET: No measurements was found.'
        else:
            self.Mes_GET_code = 404

    def Mes_DELETE(self, uuid):
        url = os.path.join(self.meas_post, uuid)
        r = requests.delete(url)
        self.Mes_DEL_code, self.Mes_DEL_text = r.status_code, r.text

    def GetMeasurementUuid(self, partPath=None, order=None, serCon=None, limitResult=None, attributes=[]):
        # 根据筛选条件设置url
        self.measurements_url(partPath, order, serCon, limitResult, attributes)
        # 通过url GET数据
        self.GET(self.mes_url)
        if self.GET_code == 200 and len(self.GET_Text) != 0:
            self.GetUuid_code = 200
            all_data = self.GET_Text
            self.uuid_list = []
            # 可能会修改多条数据，将每一条数据逐一拆分
            for data in all_data:
                # 获取测量的uuid
                uuid = data['uuid']
                self.uuid_list.append(uuid)
        elif self.GET_code == 200 and len(self.GET_Text) == 0:
            self.GetUuid_code = 300
            self.GetUuid_text = 'DELETE: No measurements was found.'
        else:
            self.GetUuid_code = 404

    def CreateNewMeasurement(self, mes_data, partPath=None, order=None, serCon=None, limitResult=None, attributes=[]):
        self.parts_url(partPath)
        self.GET(self.part_url)
        self.partUuid = self.GET_Text[0]['uuid']
        self.Mes_POST(mes_data)

    def CreateNewMeasurementwithRaw(self, mes_data, value_data, writeKey='1', partPath=None):
        """
        value_data:{'PPC:/Process/Inspection_List/Inspection_Info/': ['C:\\Users\\ZCFJIAN1\\Pictures\\connecting.png', 'fixture']}
        扩展后：{'PPC:/Process/Inspection_List/Inspection_Info/': ['C:\\Users\\ZCFJIAN1\\Pictures\\connecting.png', 'fixture', 'a0dd372d-091d-4129-ba57-260ee01c38cd']}
        """
        self.CNR_code = 404
        self.CNR_text = 'Fatal Error'
        self.parts_url(partPath)
        self.GET(self.part_url)
        self.partUuid = self.GET_Text[0]['uuid']
        self.chars_url(partPath)
        self.GET(self.char_url)
        if self.GET_code == 200 and len(self.GET_Text) != 0:
            v_data = {}
            for data in self.GET_Text:
                # 如果获取的数据库路径在传输的字典键值中的话，则将这个uuid放入字典中
                if data['path'] in value_data.keys():
                    uuid = data['uuid']
                    value_data[data['path']].append(uuid)
                    v_data[uuid] = {writeKey: value_data[data['path']][1]}
            # 准备更新测量值
            self.Val_POST(mes_data, v_data)
            if self.Mes_POST_code == 201 and len(v_data) != 0:
                # 准备上传附件
                mes_uuid = self.newuuid
                for value in value_data.values():
                    char_uuid = value[2]
                    file_path = value[0]
                    self.ValueRawData_url(mes_uuid, char_uuid)
                    self.RawDataPost(self.valRaw_url, file_path)
                    if self.RDP_code == 201:
                        self.CNR_code = 200
                    else:
                        self.CNR_code = 404
                        self.CNR_text = 'Raw Data Post Failed in {}'.format(file_path)
                        break
            elif self.Mes_POST_code == 201 and len(v_data) == 0:
                self.CNR_code = 200
            else:
                self.CNR_code = 404
                self.CNR_text = 'New Measurement POST Failed'
        else:
            self.CNR_code = 404
            self.CNR_text = 'Characteristic Info GET Failed'
        

    def UpdateMeasurementwithRaw(self, mes_data, value_data, writeKey='1', partPath=None):
        pass

    def UpdateMeasurementbyUuid(self, mes_data, uuid):
        uuid_url = self.meas_post + r'/' + uuid
        self.GET(uuid_url)
        if self.GET_code == 200 and len(self.GET_Text) != 0:
            # 获取part的uuid
            self.partUuid = self.GET_Text[0]['partUuid']
            attributes = self.GET_Text[0]['attributes']
            attributes.update(mes_data)
            self.Mes_PUT(attributes, uuid)
        elif self.GET_code == 200 and len(self.GET_Text) == 0:
            self.Mes_PUT_code = 300
            self.Mes_PUT_text = 'PUT: No measurements was found.'
        else:
            self.Mes_PUT_code = 404

    def UpdateMeasurement(self, mes_data, partPath=None, order=None, serCon=None, limitResult=None, attributes=[]):
        # 根据筛选条件设置url
        self.measurements_url(partPath, order, serCon, limitResult, attributes)
        # 通过url GET数据
        self.GET(self.mes_url)
        if self.GET_code == 200 and len(self.GET_Text) != 0:
            all_data = self.GET_Text
            # 可能会修改多条数据，将每一条数据逐一拆分
            for data in all_data:
                # 获取测量的uuid
                uuid = data['uuid']
                # 获取part的uuid
                self.partUuid = data['partUuid']
                # 获取现有的特性
                attributes = data['attributes']
                # 将要修改的特性输入到新特性中
                attributes.update(mes_data)
                # PUT特性和uuid
                self.Mes_PUT(attributes, uuid)
        elif self.GET_code == 200 and len(self.GET_Text) == 0:
            self.Mes_PUT_code = 300
            self.Mes_PUT_text = 'PUT: No measurements was found.'
        else:
            self.Mes_PUT_code = 404

    def DeleteMeasurement(self, partPath=None, order=None, serCon=None, limitResult=None, attributes=[]):
        # 根据筛选条件设置url
        self.measurements_url(partPath, order, serCon, limitResult, attributes)
        # 通过url GET数据
        self.GET(self.mes_url)
        if self.GET_code == 200 and len(self.GET_Text) != 0:
            all_data = self.GET_Text
            # 可能会修改多条数据，将每一条数据逐一拆分
            for data in all_data:
                # 获取测量的uuid
                uuid = data['uuid']
                self.Mes_DELETE(uuid)
        elif self.GET_code == 200 and len(self.GET_Text) == 0:
            self.Mes_DEL_code = 300
            self.Mes_DEL_text = 'DELETE: No measurements was found.'
        else:
            self.Mes_DEL_code = 404

    def CheckKeyDuplicate(self, partPath=None, order=None, serCon=None, limitResult=None, attributes=[], duplicate=None, compareSerCon=None):
        self.duplicateValue = []
        self.dumped_key = ()
        # 根据筛选条件设置url
        self.measurements_url(partPath, order, serCon, limitResult, attributes)
        dup_url = self.mes_url
        # 通过url GET数据
        self.GET(dup_url)
        # print(self.GET_code)
        if self.GET_code == 200 and len(self.GET_Text) != 0:
            self.Mes_DUP_code = 200
            all_data = self.GET_Text
            # 可能会修改多条数据，将每一条数据逐一拆分
            key_list = [data['attributes'][duplicate] for data in all_data]
            key_dict = dict(Counter(key_list))
            self.duplicateValue = [key for key, value in key_dict.items() if value > 1]
            if compareSerCon != None:
                self.measurements_url(partPath, order, compareSerCon, limitResult, attributes)
                compare_url = self.mes_url
                self.GET(compare_url)
                compare_data = self.GET_Text
                compare_list = [data['attributes'][duplicate] for data in compare_data]
                compare_unique = set(compare_list)
                key_unique = set(key_list)
                if len(compare_unique) > len(key_unique):
                    self.dumped_key = [key for key in compare_unique if key not in key_unique]
        elif self.GET_code == 200 and len(self.GET_Text) == 0:
            self.Mes_DUP_code = 300
            self.Mes_DUP_text = 'DUPLICATE: No measurements was found.'
        else:
            self.Mes_DUP_code = 404

    def RawDataPost(self, url, file_path):
        file_name = os.path.basename(file_path)
        file_name = file_name.replace(' ', '_')
        extension = os.path.splitext(file_name)[1]
        files = open(file_path, 'rb')
        headers = {}
        headers['Content-Disposition'] = 'attachment;filename={}'.format(
            file_name)
        if extension in self.MIME.keys():
            headers['Content-Type'] = self.MIME[extension]
        r = requests.post(url, data=files, headers=headers)
        self.RDP_code = r.status_code #201
        self.RDP_text = r.text

##################------------------交互界面UI显示------------------##################

class UI(Tk, system_config):
    def __init__(self):
        super().__init__()
        system_config.__init__(self)
        self.ico_dir = os.path.join(self.rela_dir, 'ico')
        self.process = StringVar()  # 设置一个显示状态的动态变量
        self.close = StringVar()
        self.close.set('open')

    def selectPath(self, path):
        """
        Show selectPath into input box.
        """
        path_ = askdirectory()
        if '/' in path_:
            path_ = path_.replace('/', '\\')
        path.set(path_)

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

    def ErrorShow(self, error_info):
        self.withdraw()
        self.errorform = tkinter.messagebox.showerror('错误', error_info)

    def InfoShow(self, info):
        self.withdraw()
        self.infoform = tkinter.messagebox.showinfo('提示', info)

    def AskQuestion(self, info):
        self.withdraw()
        self.askqform = tkinter.messagebox.askquestion('提示', info)

    def Loading(self):
        self.wm_attributes('-topmost',1)
        self.resizable(0, 0)
        self.title('质量流 Quality Flow')
        self.geometry('550x100')
        self.iconbitmap(os.path.join(self.ico_dir, 'qFlow.ico'))
        bg = Canvas(self, width=550, height=100,bg="white")
        bg.place(x=0, y=0)
        bg.config(highlightthickness = 0)
        self.canvas = Canvas(self, width=410, height=10, bg="white")
        self.canvas.place(x=70, y=45)
        #self.canvas.config(highlightthickness = 0)
        Label(self, text="正在打开...", bg='white').place(x=70, y=15)
        self.protocol("WM_DELETE_WINDOW", self.do_nothing)
        l = threading.Thread(target=self.loop)
        l.setDaemon(True)
        l.start()

    def loop(self):
        self.fill_line = self.canvas.create_rectangle(1.5, 1.5, 150, 25, width=0, fill="#228B22")
        n = 0
        while self.close.get() == 'open':
            n = n + 3
            if n <= 150:
                self.canvas.coords(self.fill_line, (0, 0, n, 60))
            elif 150 < n <= 600:
                self.canvas.coords(self.fill_line, (n-150, 0, n, 60))
            else:
                n = 0
                continue
            self.update()
            time.sleep(0.01)  # 控制进度条流动的速度

    def do_nothing(self):
        pass

    def Drawing_upload(self):
        self.wm_attributes('-topmost',1)
        self.resizable(0, 0)
        self.title('质量流 Quality Flow')
        self.iconbitmap(os.path.join(self.ico_dir, 'qFlow.ico'))
        self.geometry()
        self.drawing_path = StringVar()
        self.drawing_path.set("")
        self.process.set("点击“创建工件并上传图纸”开始保存")
        Label(self, text="",  width=3).grid(row=0, column=0) #左边
        Label(self, text="选择需要上传的工件图纸").grid(row=1, column=1, sticky=W)
        Entry(self, textvariable=self.drawing_path, width=60).grid(row=2, column=1, sticky=W)
        Label(self, text="",  width=1).grid(row=2, column=3) #中间
        Button(self, text="浏览", command=lambda: self.selectFile(self.drawing_path),
               relief=GROOVE, width=6, height=1).grid(row=2, column=4, sticky=E)
        Label(self, text="",  width=3).grid(row=2, column=5) #右边
        Label(self, text="",  width=3).grid(row=3, column=5) #右边
        Label(self, textvariable=self.process).grid(row=3, column=1, sticky=W)

    def Dynamic_process(self, content):
        while True:
            self.process.set(content)
            time.sleep(0.5)
            self.process.set(content+'.')
            time.sleep(0.5)
            self.process.set(content+'..')
            time.sleep(0.5)
            self.process.set(content+'...')
            time.sleep(0.5)

    def Inspection_upload(self, software, program_path, log_path, program_data, target_dir):
        self.wm_attributes('-topmost',1)
        self.resizable(0, 0)
        self.title('质量流 Quality Flow')
        self.iconbitmap(os.path.join(self.ico_dir, 'qFlow.ico'))
        self.geometry()
        self.fixture_path = StringVar()
        self.probe_path = StringVar()
        self.fixture_path.set("")
        self.probe_path.set("")
        self.process.set("点击“上传测量程序及附件”开始上传")
        self.software = software
        if program_path != '' and os.path.exists(program_path) and len(os.listdir(program_path)) != 0:
            if software == 'CALYPSO':
                Label(self, text="",  width=3).grid(row=0, column=0) #左边
                Label(self, text="请选择该测量程序工装夹具的照片").grid(row=1, column=1, sticky=W)
                Entry(self, textvariable=self.fixture_path, width=80).grid(row=2, column=1, sticky=W)
                Label(self, text="",  width=1).grid(row=2, column=3) #中间
                Button(self, text="浏览", command=lambda: self.selectFile(self.fixture_path),
                        relief=GROOVE, width=6, height=1).grid(row=2, column=4, sticky=E)
                Label(self, text="",  width=3).grid(row=2, column=5) #右边
                inspset = os.path.join(program_path, r'inspset')
                if os.path.exists(inspset):
                    self.probe_pa = []
                    with open(inspset, 'r') as ins:
                        for line in ins:
                            if "#usedProbeConfigs ' ->'" in line:
                                ins.readline()
                                self.probe_list = ins.readline().strip()[6:-2].replace("'","").split(" ")
                                break
                    for i, probe in enumerate(self.probe_list):
                        txt_row = 3 + i*2
                        entry_row = txt_row + 1
                        self.probe_pa.append(StringVar())
                        self.probe_pa[i].set("")
                        Label(self,text="请选择探针组\""+probe+"\"照片",height=1).grid(row=txt_row,column=1,sticky=W)
                        Entry(self,textvariable=self.probe_pa[i],width=80).grid(row=entry_row,column=1,sticky=W)
                        Button(self,text="浏览",command=lambda i = i:self.selectFile(self.probe_pa[i]), relief=GROOVE, width=6, height=1).grid(row=entry_row,column=4,sticky=E)
                        if i == len(self.probe_list)-1:
                            Label(self,textvariable=self.process).grid(row=entry_row+1,column=1,sticky=W)
                            Button(self,text="上传测量程序及附件", command=lambda :thread_it(empty_path_check, log_path, program_path, program_data, target_dir), width=18, height=2,relief=GROOVE).grid(row=entry_row+2, column=1, columnspan=4, sticky=E)
                            Label(self,text="",width=2).grid(row=entry_row+3,column=0)
                else:
                    self.software = 'Not CALYPSO'
                    Label(self, text="",  width=3).grid(row=0, column=0) #左边
                    Label(self, text="请选择该测量程序工装夹具的照片").grid(row=1, column=1, sticky=W)
                    Entry(self, textvariable=self.fixture_path, width=80).grid(row=2, column=1, sticky=W)
                    Label(self, text="",  width=1).grid(row=2, column=3) #中间
                    Button(self, text="浏览", command=lambda: self.selectFile(self.fixture_path),
                            relief=GROOVE, width=6, height=1).grid(row=2, column=4, sticky=E)
                    Label(self, text="",  width=3).grid(row=2, column=5) #右边
                    Label(self, text="请选择该测量程序所用探针的照片(可多选)").grid(row=3, column=1, sticky=W)
                    Entry(self, textvariable=self.probe_path, width=80).grid(row=4, column=1, sticky=W)
                    Button(self, text="浏览", command=lambda: self.selectFile(self.probe_path),
                            relief=GROOVE, width=6, height=1).grid(row=4, column=4, sticky=E)
                    Label(self, textvariable=self.process).grid(row=5, column=1,sticky=W)
                    Button(self, text="上传测量程序及附件", command=lambda :thread_it(empty_path_check, log_path, program_path, program_data, target_dir), relief=GROOVE, width=18, height=2).grid(row=6, column=1, columnspan=4, sticky=E)
                    # Button(self, text="上传测量程序及附件", command=lambda :thread_it(inspection_backup, log_path, program_path, program_data, target_dir), relief=GROOVE, width=18, height=2).grid(row=6, column=1, columnspan=4, sticky=E)
                    Label(self, text="").grid(row=7, column=0)
            elif software == 'MANUAL':
                pass
            else:
                Label(self, text="",  width=3).grid(row=0, column=0) #左边
                Label(self, text="请选择该测量程序工装夹具的照片").grid(row=1, column=1, sticky=W)
                Entry(self, textvariable=self.fixture_path, width=80).grid(row=2, column=1, sticky=W)
                Label(self, text="",  width=1).grid(row=2, column=3) #中间
                Button(self, text="浏览", command=lambda: self.selectFile(self.fixture_path),
                        relief=GROOVE, width=6, height=1).grid(row=2, column=4, sticky=E)
                Label(self, text="",  width=3).grid(row=2, column=5) #右边
                Label(self, text="请选择该测量程序所用探针的照片(可多选)").grid(row=3, column=1, sticky=W)
                Entry(self, textvariable=self.probe_path, width=80).grid(row=4, column=1, sticky=W)
                Button(self, text="浏览", command=lambda: self.selectFile(self.probe_path),
                    relief=GROOVE, width=6, height=1).grid(row=4, column=4, sticky=E)
                Label(self, textvariable=self.process).grid(row=5, column=1,sticky=W)
                Button(self, text="上传测量程序及附件", command=lambda :thread_it(empty_path_check, log_path, program_path, program_data, target_dir), relief=GROOVE, width=18, height=2).grid(row=6, column=1, columnspan=4, sticky=E)
                # Button(self, text="上传测量程序及附件", command=lambda :thread_it(inspection_backup, log_path, program_path, program_data, target_dir), relief=GROOVE, width=18, height=2).grid(row=6, column=1, columnspan=4, sticky=E)
                Label(self, text="").grid(row=7, column=0)
        elif program_path == '':
            self.ErrorShow("请选择测量程序路径后再试！")
            self.destroy()
        elif not os.path.exists(program_path):
            self.ErrorShow("所填写的测量程序路径不存在！")
            self.destroy()
        elif len(os.listdir(program_path)) == 0:
            self.ErrorShow("所填写的程序目录下没有文件！")
            self.destroy()

    def UI_Create(self, log_path, key_data):
        self.resizable(0, 0)
        self.geometry()
        self.iconbitmap(os.path.join(self.rela_dir, 'flow.ico'))
        self.report_path = StringVar()
        self.report_path.set("")
        Label(self, text="", width=2).grid(row=0, column=0)
        Label(self, text="请选择测量报告(可多选):", height=1).grid(
            row=1, column=1, sticky=W)
        Entry(self, textvariable=self.report_path,
              width=60).grid(row=2, column=1, sticky=W)
        Label(self, text="", width=1).grid(row=2, column=2)
        Button(self, text="浏览", command=lambda: thread_it(create_new_part, (log_path, key_data)), relief=GROOVE, width=7, height=2).grid(row=2, column=3, sticky=E)
        Label(self, text="", width=2).grid(row=2, column=4)
        Label(self, text="", width=2).grid(row=3, column=0)

##################------------------Calypso测量程序备份------------------##################

class InspectionBackup(system_config):
    def __init__(self, program_path, target_dir):
        system_config.__init__(self)
        self.target_dir = target_dir
        self.program_path = program_path
        self.program_name = os.path.basename(self.program_path)
        # Fileserver上的文件夹名称，用来检查有没有同名程序
        self.program_dir = os.path.join(self.target_dir, self.program_name)
        # 获得测量程序中inspection文件的路径
        #self.new_inspection = os.path.join(self.program_path, 'inspection')
        #self.exist_inspection = os.path.join(self.target_dir, 'inspection')

    def history_dir(self):
        # 获取当前时间作为备份程序的后缀名
        #modi_time = os.path.getmtime(self.exist_inspection)
        time_suffix = time.strftime(
            '_%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
        self.history_name = self.program_name + time_suffix
        # 设置历史版本的路径
        self.history_path = os.path.join(
            self.target_dir, 'history_version', self.history_name)
        
    def backup(self, uuid):
        # 在备份程序前，先检查原有的程序是否存在，如果存在，则将原有的程序删除
        if os.path.exists(self.program_dir):
            shutil.rmtree(self.program_dir)
        #将新程序从本地复制到文件服务器
        shutil.copytree(self.program_path, self.program_dir)
        with open(os.path.join(self.program_dir, 'versionid.ini'), 'w') as v:
            v.writelines(uuid)

# Method
##################------------------通用方法------------------##################

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

def _async_raise(tid, exctype):
   """raises the exception, performs cleanup if needed"""
   tid = ctypes.c_long(tid)
   if not inspect.isclass(exctype):
      exctype = type(exctype)
   res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
   if res == 0:
      raise ValueError("invalid thread id")
   elif res != 1:
      # """if it returns a number greater than one, you're in trouble,  
      # and you should call it again with exc=NULL to revert the effect"""  
      ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
      raise SystemError("PyThreadState_SetAsyncExc failed")

def stop_thread(thread):
   _async_raise(thread.ident, SystemExit)

def msel_change(para_file):
    msel_gen = piwebconfig(para_file, keep=True)
    msel_gen.msel()

def showError(errorInfo):
    """
    用来弹出错误信息的窗口，窗口中显示的提示内容为：errorInfo
    """
    load_ui.ErrorShow(errorInfo)

def showInfo(info):
    load_ui.InfoShow(info)

def askQuestion(info):
    load_ui.AskQuestion(info)

def window(rela_dir, cmd):
    form = os.path.join(rela_dir, 'qFlowForm.exe')
    command_line = 'start "" "{}" {}'.format(form, cmd)
    run(command_line, shell=True)

def parafile_delete(path):
    """
    在流程运行中放弃本次操作，需要把PiWeb生成的数据删除时
    使用这个方法
    """
    # 检查Temp文件夹下是否存在指定名字的数据文件
    para_list = os.listdir(path)
    for para in para_list:
        para_path = os.path.join(path, para)
        os.remove(para_path)

def decode_url(url):
    return url.replace("%20", " ")

def filter_key_parser(filterkey):
    key_list = filterkey.split(',')
    key_data = {}
    for key in key_list:
        keys = str(key.split('=')[0].strip())
        value = str(key.split('=')[1].strip())
        key_data[keys] = value
    return key_data

def mesl_making(key_data):
    # '<AttributeConditionDescription SpecialOperation="Undefined" Operation="Equal" Value="%%%%%%">'.format()
    # r'</AttributeConditionDescription>'
    msel = system_config()
    master_dir = os.path.join(msel.rela_dir, 'master.msel')
    search_dir = os.path.join(msel.para_dir, 'search.msel')
    filter_data = {
                    '22030':r'  <Definition xsi:type="q1:AttributeDefinition" key="22030" description="Product ident" queryEfficient="false" type="AlphaNumeric" length="40" xmlns:q1="http://www.daimlerchrysler.com/DataService" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" />',
                    '10030':r'  <Definition xsi:type="q1:CatalogueAttributeDefinition" key="10030" description="Software" queryEfficient="false" catalogue="ea22a526-6e81-4690-a6db-200aeaad4dda" xmlns:q1="http://www.daimlerchrysler.com/DataService" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" />',
                    '10031':r'  <Definition xsi:type="q2:AttributeDefinition" key="10031" description="Software Revision" queryEfficient="false" type="AlphaNumeric" length="200" xmlns:q2="http://www.daimlerchrysler.com/DataService" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" />',
                    '22250':r'  <Definition xsi:type="q3:AttributeDefinition" key="22250" description="Job number" queryEfficient="false" type="AlphaNumeric" length="25" xmlns:q3="http://www.daimlerchrysler.com/DataService" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" />',
                    '22253':r'  <Definition xsi:type="q4:AttributeDefinition" key="22253" description="Task number" queryEfficient="false" type="Integer" length="0" xmlns:q4="http://www.daimlerchrysler.com/DataService" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" />',
                    '22200':r'  <Definition xsi:type="q5:AttributeDefinition" key="22200" description="Inspection name" queryEfficient="false" type="AlphaNumeric" length="200" xmlns:q5="http://www.daimlerchrysler.com/DataService" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" />',
                    '96':r'  <Definition xsi:type="q6:CatalogueAttributeDefinition" key="96" description="Approval" queryEfficient="false" catalogue="57b758ff-89a0-40eb-b21b-fe5780592e68" xmlns:q6="http://www.daimlerchrysler.com/DataService" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" />'
                    }
    with codecs.open(master_dir, 'r', 'utf8') as master:
        with codecs.open(search_dir, 'w', 'utf8') as search:
            for line in master:
                if '<ThisIsThePlaceToInsert>' not in line:
                    search.writelines(line)
                else:
                    for key, value in key_data.items():
                        firstline = '<AttributeConditionDescription SpecialOperation="Undefined" Operation="Equal" Value="{}">\r\n'.format(value)
                        search.writelines(firstline)
                        search.writelines(filter_data[key] + '\r\n')
                        search.writelines('</AttributeConditionDescription>\r\n')

def run_cmd(command_line):
    run(command_line, shell=True)

def catalog_transfer(para_file):
    cata = piwebconfig(para_file, empty_dump=False)
    para_path = os.path.join(cata.para_dir, para_file)
    with open(para_path, 'w') as p:
        for key, value in cata.txt_data.items():
            if ' - ' in value:
                value = value.split(' - ')[0].strip()
            p.writelines(key + ' = ' + value + '\n')

def dictToserCon(mes_data):
    serCon_list = ['{}In[{}]'.format(key, value) for key, value in mes_data.items()]
    serCon = '%2B'.join(serCon_list)
    return serCon
    
def empty_path_check(log_path, program_path, program_data, target_dir):
    ctl_info = {}
    if load_ui.fixture_path.get() != "":
        # {'fixture': [fixture_path, 0]}
        ctl_info['PPC:/Process/Inspection_List/Inspection_Info/'] = [load_ui.fixture_path.get(), 'fixture']
    if 'update' not in program_data.keys():
        if load_ui.software == 'CALYPSO':
            for idx, probe in enumerate(load_ui.probe_list):
                if load_ui.probe_pa[idx].get() != "":
                    # {'probe_name': [probe_path, 1]}
                    ctl_info['PPCC:/Process/Inspection_List/Inspection_Info/Probe{}/'.format(idx+1)] =  [load_ui.probe_pa[idx].get(), probe]
            if len(ctl_info) < 1+len(load_ui.probe_list):
                asq = Toplevel()
                asq.withdraw()
                asq.askqform = tkinter.messagebox.askquestion('提示', "探针组照片/工件装夹方式未上传\n不上传附件将不会生成知识库文件\n是否确定不上传上述附件？")
                if asq.askqform == 'yes':
                    program_data.update({'9':'No_File'})
                    inspection_backup(log_path, program_path, program_data, target_dir, ctl_info)
                else:
                    load_ui.destroy()
            else:
                inspection_backup(log_path, program_path, program_data, target_dir, ctl_info)
        else:
            probe_pa = load_ui.probe_path.get().split(';')
            for idx, probe_path in enumerate(probe_pa):
                probe = os.path.basename(probe_path)
                probe = os.path.splitext(probe)[0]
                ctl_info['PPCC:/Process/Inspection_List/Inspection_Info/Probe{}/'.format(idx+1)] =  [probe_path, probe]
            if len(ctl_info) < 2:
                asq = Toplevel()
                asq.withdraw()
                asq.askqform = tkinter.messagebox.askquestion('提示', "探针组照片/工件装夹方式未上传\n不上传附件将不会生成知识库文件\n是否确定不上传上述附件？")
                if asq.askqform == 'yes':
                    program_data.update({'9':'No_File'})
                    inspection_backup(log_path, program_path, program_data, target_dir, ctl_info)
                else:
                    load_ui.destroy()
            else:
                inspection_backup(log_path, program_path, program_data, target_dir, ctl_info)
    else:
        program_data.pop('update')
        if load_ui.software == 'CALYPSO':
            for idx, probe in enumerate(load_ui.probe_list):
                if load_ui.probe_pa[idx].get() != "":
                    # {'probe_name': [probe_path, 1]}
                    ctl_info['PPCC:/Process/Inspection_List/Inspection_Info/Probe{}/'.format(idx+1)] =  [load_ui.probe_pa[idx].get(), probe]
            if len(ctl_info) < 1+len(load_ui.probe_list):
                asq = Toplevel()
                asq.withdraw()
                asq.askqform = tkinter.messagebox.askquestion('提示', "探针组照片/工件装夹方式未上传\n不上传附件将不会生成知识库文件\n是否确定不上传上述附件？")
                if asq.askqform == 'yes':
                    program_data.update({'9':'No_File'})
                    inspection_update(log_path, program_path, program_data, target_dir, ctl_info)
                else:
                    load_ui.destroy()
            else:
                inspection_update(log_path, program_path, program_data, target_dir, ctl_info)
        else:
            probe_pa = load_ui.probe_path.get().split(';')
            for idx, probe_path in enumerate(probe_pa):
                probe = os.path.basename(probe_path)
                probe = os.path.splitext(probe)[0]
                ctl_info['PPCC:/Process/Inspection_List/Inspection_Info/Probe{}/'.format(idx+1)] =  [probe_path, probe]
            if len(ctl_info) < 2:
                asq = Toplevel()
                asq.withdraw()
                asq.askqform = tkinter.messagebox.askquestion('提示', "探针组照片/工件装夹方式未上传\n不上传附件将不会生成知识库文件\n是否确定不上传上述附件？")
                if asq.askqform == 'yes':
                    program_data.update({'9':'No_File'})
                    inspection_update(log_path, program_path, program_data, target_dir, ctl_info)
                else:
                    load_ui.destroy()
            else:
                inspection_update(log_path, program_path, program_data, target_dir, ctl_info)


##################------------------系统流程方法------------------##################

# 派工
def job_number_create(log_path, para_dir):
    """
    在创建测量任务时创建一个初始的测量任务号
    """
    # 设置logger
    logger1 = logging.getLogger('Assign')
    logger1.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                          - %(message)s')
    fh.setFormatter(formatter)
    logger1.addHandler(fh)
    logger1.info("成功进入job_number_create子程序")
    # 创建一个新的测量任务号
    with open(os.path.join(para_dir, 'assignment.para'), 'w') as ass:
        current_time = time.strftime('%y%m%d%H%M%S', time.localtime(time.time()))
        job_number = 'JOB' + current_time
        ass.writelines('22250 = '+job_number+'\n22253 = 1')
        logger1.info("成功创建Job Number:{}, Task Number:1".format(job_number))
    # 将Job Number加入mesl文件，作为搜索条件
    create = piwebconfig('assignment.para', keep=True)
    create.msel()
    # 设置Command Line语句,更换Assign_Status.ptx的搜索条件
    cmdmon = r'"C:\Program Files\Zeiss\PiWeb\Cmdmon.exe" -open "'
    ptx_dir = os.path.join(create.assign_dir, 'Assign_Status.ptx')
    searchCriteria = r'" -searchCriteria "'
    msel_dir = os.path.join(create.para_dir, 'search.msel')
    save = r'" -save "'
    commandline = cmdmon + ptx_dir + searchCriteria + msel_dir + save + ptx_dir + r'"'
    # 运行Command Line
    run(commandline, shell=True)
    logger1.info("成功同步{}筛选条件到Assign_Status".format(job_number))

def job_assignment(log_path):
    """
    目的：完成qFlow中的简单派工功能
    """
    # 设置logger
    logger1 = logging.getLogger('Assign')
    logger1.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                          - %(message)s')
    fh.setFormatter(formatter)
    logger1.addHandler(fh)
    logger1.info("成功进入job_assignment子程序")
    try:
        # 检查本机与PiWeb服务器的网络链接
        net = netaccess()
        if net.piwebserver_access():
            logger1.info('PiWeb数据库({})连接成功'.format(net.host['main']))
            assign = piwebconfig('assignment.para')
            logger1.info("成功读取assignment.para中的信息")
            # 获取当前测量工单号和任务号
            job_number = assign.txt_data['22250']
            task_number = int(assign.txt_data['22253']) + 1
            # 设置下一个测量工单号和任务号
            with open(os.path.join(assign.para_dir, 'assignment.para'), 'w') as ass:
                ass.writelines('22250 = ' + job_number)
                ass.writelines('\n22253 = ' + str(task_number))
                ass.writelines('\n22032 = ' + assign.txt_data['22032'])
                ass.writelines('\n22033 = ' + assign.txt_data['22033'])
                ass.writelines('\n22034 = ' + assign.txt_data['22034'])
                ass.writelines('\n22030 = ' + assign.txt_data['22030'])
                ass.writelines('\n22031 = ' + assign.txt_data['22031'])
                ass.writelines('\n22035 = ' + assign.txt_data['22035'])
                ass.writelines('\n22037 = ' + assign.txt_data['22037'])
                ass.writelines('\n22258 = ' + assign.txt_data['22258'])
                ass.writelines('\n22038 = ' + assign.txt_data['22038'])
                if '22050' in assign.txt_data.keys():
                    ass.writelines('\n22050 = ' + assign.txt_data['22050'])
            # 上传派工信息
            # 如果测量类型为首件，则默认优先级为特急
            if assign.txt_data['22258'] == "首件":
                assign.txt_data.update({'22252': 1})
            # 设置当前时间
            current_time = datetime.datetime.now()
            change_time = current_time + datetime.timedelta(hours=-8)
            assign.txt_data['4'] = change_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            # 写入数据库
            API = PiWebAPI(net.host['main'])
            API.CreateNewMeasurement(assign.txt_data, partPath='/Process/Job_Management/')
            if API.Mes_POST_code != 201:
                logger1.error(API.Mes_POST_text)
                showError("Status Code:{} 详细信息请查看log文件".format(API.Mes_POST_code))
            elif API.Mes_POST_code == 201:
                logger1.info("派工信息POST成功")
        else:
            message = "({})网络连接失败,请检查网络后再试".format(net.host['ip'])
            logger1.error(message)
            showError(message)
    except FileNotFoundError:
        message = "没有检测到PiWeb生成的数据"
        logger1.error(message)
        showError(message)

def job_adjustment(log_path):
    """
    修改现有的派工信息
    """
    # 设置logger
    logger1 = logging.getLogger('Assign')
    logger1.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                          - %(message)s')
    fh.setFormatter(formatter)
    logger1.addHandler(fh)
    logger1.info("成功进入job_adjustment子程序")
    try:
        adjust = piwebconfig('adjustment.para')
        logger1.info("成功读取adjustment.para中的信息")
        # 检查本机与PiWeb服务器的网络链接
        net = netaccess()
        if net.piwebserver_access():
            logger1.info('PiWeb数据库({})连接成功'.format(net.host['main']))
            # 获取当前测量工单号和任务号
            job_number = adjust.txt_data['22250']
            task_number = adjust.txt_data['22253']
            # 如果测量类型为首件，则默认优先级为特急
            if adjust.txt_data['22258'] == "首件":
                adjust.txt_data.update({'22252': 1})
            # 设置更新测量的参数
            serCon = '22250In[{}]%2B22253In[{}]'.format(job_number, task_number)
            partPath = '/Process/Job_Management/'
            API = PiWebAPI(net.host['main'])
            API.UpdateMeasurement(adjust.txt_data, partPath=partPath, serCon=serCon)
            if API.GET_code == 200:
                logger1.info("成功获取数据库信息")
                if API.Mes_PUT_code == 200:
                    logger1.info("成功修改{} {}".format(job_number, task_number))
                elif API.Mes_PUT_code == 300:
                    logger1.warn(API.Mes_PUT_text)
                else:
                    logger1.error(API.Mes_PUT_text)
                    showError("Status Code: PUT {} 详细信息请查看log文件".format(API.Mes_PUT_code))
            else:
                logger1.error(API.GET_Text)
                showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
        else:
            message = "({})网络连接失败,请检查网络后再试".format(net.host['ip'])
            logger1.error(message)
            showError(message)
    except FileNotFoundError:
        message = "没有检测到PiWeb生成的数据"
        logger1.error(message)
        showError(message)

def job_delete(log_path):
    """
    删除该测量工单下所有的测量任务
    """
    logger1 = logging.getLogger('Assign')
    logger1.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                          - %(message)s')
    fh.setFormatter(formatter)
    logger1.addHandler(fh)
    try:
        delete = piwebconfig('assignment.para', keep=True)
        logger1.info("成功读取assignment.para中的信息")
        # 检查本机与PiWeb服务器的网络链接
        net = netaccess()
        if net.piwebserver_access():
            logger1.info('PiWeb数据库({})连接成功'.format(net.host['main']))
            # 获取当前测量工单号和任务号
            job_number = delete.txt_data['22250']
            # 设置更新测量的参数
            serCon = '22250In[{}]'.format(job_number)
            partPath = '/Process/Job_Management/'
            API = PiWebAPI(net.host['main'])
            # 删除指定的Measurement
            API.DeleteMeasurement(partPath=partPath, serCon=serCon)
            if API.GET_code == 200:
                logger1.info("成功获取数据库信息")
                if API.Mes_DEL_code == 200:
                    logger1.info("成功删除{}".format(job_number))
                elif API.Mes_DEL_code == 300:
                    logger1.warn(API.Mes_DEL_text)
                else:
                    logger1.error(API.Mes_DEL_text)
                    showError("Status Code: DELETE {} 详细信息请查看log文件".format(API.Mes_DEL_code))
            else:
                logger1.error(API.GET_Text)
                showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
        else:
            message = "({})网络连接失败,请检查网络后再试".format(net.host['ip'])
            logger1.error(message)
            showError(message)
        # 删除数据库中该工单后，删除所有临时文件
        parafile_delete(delete.para_dir)
    except FileNotFoundError:
        message = "没有检测到PiWeb生成的数据"
        logger1.error(message)
        showError(message)
    
def change_job_quantity(log_path):
    """
    修改测量任务中待测工件的数量
    """
    logger1 = logging.getLogger('Assign')
    logger1.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                          - %(message)s')
    fh.setFormatter(formatter)
    logger1.addHandler(fh)
    try:
        qty = piwebconfig('quantity.para')
        logger1.info("成功读取quantity.para中的信息")
        if '22250' in qty.txt_data.keys() and '22035' in qty.txt_data.keys():
            # 检查本机与PiWeb服务器的网络链接
            net = netaccess()
            if net.piwebserver_access():
                logger1.info('PiWeb数据库({})连接成功'.format(net.host['main']))
                # 获取当前测量工单号和任务号
                job_number = qty.txt_data['22250']
                part_qty = qty.txt_data['22035']
                # 设置更新测量的参数
                serCon = '22250In[{}]'.format(job_number)
                partPath = '/Process/Job_Management/'
                mes_data = {'22035': part_qty}
                API = PiWebAPI(net.host['main'])
                API.UpdateMeasurement(mes_data, partPath=partPath, serCon=serCon)
                if API.GET_code == 200:
                    logger1.info("成功获取数据库信息")
                    if API.Mes_PUT_code == 200:
                        rewrite = piwebconfig('assignment.para')
                        content = rewrite.txt_data
                        content.update(mes_data)
                        ass_dir = os.path.join(rewrite.para_dir, 'assignment.para')
                        with open(ass_dir, 'w') as ass:
                            for key, value in content.items():
                                ass.writelines(key+' = '+value+'\n')
                        logger1.info("成功修改{}的待测工件数量{}".format(job_number, part_qty))
                        showInfo("工件数量修改成功！")
                    elif API.Mes_PUT_code == 300:
                        logger1.warn(API.Mes_PUT_text)
                    else:
                        logger1.error(API.Mes_PUT_text)
                        showError("Status Code: PUT {} 详细信息请查看log文件".format(API.Mes_PUT_code))
                else:
                    logger1.error(API.GET_Text)
                    showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
        else:
            logger1.info("quantity.para中信息缺失，可能没有数据")
    except FileNotFoundError:
        message = "没有检测到PiWeb生成的数据"
        logger1.error(message)
        showError(message)

def job_publish(log_path):
    """
    将待发布的测量结果的状态更行为：assignment_done
    
    """
    logger1 = logging.getLogger('Assign')
    logger1.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                          - %(message)s')
    fh.setFormatter(formatter)
    logger1.addHandler(fh)
    try:
        publish = piwebconfig('assignment.para', keep=True)
        logger1.info("成功读取publish.para中的信息")
        # 检查本机与PiWeb服务器的网络链接
        net = netaccess()
        if net.piwebserver_access():
            logger1.info('PiWeb数据库({})连接成功'.format(net.host['main']))
            # 获取当前测量工单号和任务号
            job_number = publish.txt_data['22250']
            # 设置更新测量的参数
            serCon = '22250In[{}]'.format(job_number)
            partPath = '/Process/Job_Management/'
            mes_data = {'22251': 1}
            API = PiWebAPI(net.host['main'])
            API.UpdateMeasurement(mes_data, partPath=partPath, serCon=serCon)
            if API.GET_code == 200:
                logger1.info("成功获取数据库信息")
                if API.Mes_PUT_code == 200:
                    logger1.info("成功发布{}".format(job_number))
                elif API.Mes_PUT_code == 300:
                    logger1.warn(API.Mes_PUT_text)
                else:
                    logger1.error(API.Mes_PUT_text)
                    showError("Status Code: PUT {} 详细信息请查看log文件".format(API.Mes_PUT_code))
            else:
                logger1.error(API.GET_Text)
                showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
        # 发布该工单后，删除所有临时文件
        parafile_delete(publish.para_dir)
    except FileNotFoundError:
        message = "没有检测到PiWeb生成的数据"
        logger1.error(message)
        showError(message)

def assignment_data(log_path):
    """
    第一步：派工
    """
    logger1 = logging.getLogger('Assign')
    logger1.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                          - %(message)s')
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

# 测量程序
def inspection_download(log_path, rela_dir, source_dir, target_dir, base_dir, inspection_name, machine_interface_dir):
    try:
        # 打开loading窗口
        #window(rela_dir, 'start connecting')
        # 设置logger
        logger2 = logging.getLogger('Inspection')
        logger2.setLevel(logging.DEBUG)
        fh = logging.FileHandler(log_path, encoding='UTF-8')
        formatter = logging.Formatter(
            '[              ] %(asctime)s %(levelname)s   %(name)s                      - %(message)s')
        fh.setFormatter(formatter)
        logger2.addHandler(fh)
        logger2.info("成功进入inspection_download子程序")
        # 设置目标文件的路径位置
        # 测量程序的本地存储位置
        inspection = os.path.join(target_dir, inspection_name)
        # CALYPSO的位置
        calypso = base_dir
        # vphead.gra的本地存储位置
        vphead = os.path.join(calypso, r'protocol\protform\default\vphead.gra')
        # userfield.ini的本地存储位置
        userfield = os.path.join(calypso, r'protocol\protform\userfields.ini')
        # out.sconf的本地存储位置
        user_name = getpass.getuser()
        out = os.path.join(r'C:\Users', user_name, r'out.sconf')
        # startfile的本地存储位置
        startfile = os.path.join(target_dir, r'startfile')
        # 设置来源文件的位置
        rela_ins_dir = os.path.join(rela_dir, 'inspection')
        # 从系统中复制标准vphead.gra到calypso中
        if os.path.exists(vphead):
            os.remove(vphead)
        shutil.copyfile(os.path.join(rela_ins_dir, 'vphead.gra'), vphead)
        # 从系统中复制标准userfields.ini到calypso中
        if os.path.exists(userfield):
            os.remove(userfield)
        shutil.copyfile(os.path.join(rela_ins_dir, 'userfields.ini'), userfield)
        # 从系统中复制标准out.sconf到用户文件夹中
        if os.path.exists(out):
            os.remove(out)
        shutil.copyfile(os.path.join(rela_ins_dir, 'out.sconf'), out)
        # 修改startfile
        startfile_list = []
        with open(startfile, 'r') as start:
            for line in start:
                if 'planid' in line:
                    line = 'planid\t'+inspection_name+'\n'
                startfile_list.append(line)
        with open(startfile, 'w') as s:
            for line in startfile_list:
                s.writelines(line)
        # 从文件服务器下载测量程序
        # 检查网络连接
        net = netaccess()
        if net.fileserver_access():
            # 打开downloading窗口
            if os.path.exists(os.path.join(target_dir, inspection_name)):
                logger2.info('本地发现已存在测量程序：{}，删除本地测量程序'.format(inspection_name))
                shutil.rmtree(inspection)
            else:
                logger2.info('本地未发现测量程序：{}，开始下载测量程序'.format(inspection_name))
            # 下载测量程序
            shutil.copytree(source_dir, inspection)
            logger2.info('成功下载测量程序{}'.format(inspection_name))
            # 读取job_number.para文件
            download = piwebconfig('job_number.para', keep=True)
            if os.path.exists(os.path.join(inspection, 'job_number.para')):
                os.remove(os.path.join(inspection, 'job_number.para'))
            shutil.copyfile(os.path.join(download.para_dir, 'job_number.para'), os.path.join(inspection, 'job_number.para'))
            # 复制inspection_start.bat文件
            inspection_start = os.path.join(inspection, 'inspection_start.bat')
            if os.path.exists(inspection_start):
                os.remove(inspection_start)
            with open(inspection_start, 'w') as start:
                start.writelines('@echo off\ncd \"{}\"\n'.format(machine_interface_dir))
                start.writelines('start MachineInterface.exe Start')
            # 复制report_end.bat文件
            report_end = os.path.join(inspection, 'report_end.bat')
            if os.path.exists(report_end):
                os.remove(report_end)
            with open(report_end, 'w') as start:
                start.writelines('@echo off\ncd \"{}\"\n'.format(machine_interface_dir))
                start.writelines('start MachineInterface.exe Stop')
            # 设置prothead参数
            customer = download.txt_data['22037']
            u_User = download.txt_data['8']
            u_MachiningEquipment = download.txt_data['22038']
            u_TaskNumber = download.txt_data['22253']
            u_JobNumber = download.txt_data['22250']
            u_Batch = ''
            partid = download.txt_data['22031']
            if '9' in download.txt_data.keys():
                u_Rework = download.txt_data['9']
            else:
                u_Rework = ''
            if os.path.exists(os.path.join(inspection, 'protheadpara')):
                pro_list = []
                with open(os.path.join(inspection, 'protheadpara'), 'r') as pro:
                    for line in pro:
                        if 'customer' in line or 'u_' in line or 'partid' in line:
                            break
                        else:
                            pro_list.append(line)
                with open(os.path.join(inspection, 'protheadpara'), 'w') as pro:
                    for line in pro_list:
                        pro.writelines(line)
                    pro.writelines('customer,'+customer+'\n')
                    pro.writelines('u_User,'+u_User+'\n')
                    pro.writelines('u_MachiningEquipment,'+u_MachiningEquipment+'\n')
                    pro.writelines('u_TaskNumber,'+u_TaskNumber+'\n')
                    pro.writelines('u_JobNumber,'+u_JobNumber+'\n')
                    pro.writelines('u_Batch,'+u_Batch+'\n')
                    pro.writelines('partid,'+partid+'\n')
                    pro.writelines('u_Rework,'+u_Rework)
            # 打开calypso 2017
            thread_it(run_cmd, r'"C:\Program Files (x86)\Zeiss\CALYPSO 6.4\bin\scalypso.exe" "C:\Program Files (x86)\Zeiss\CALYPSO 6.4\bin\vwnt.exe" -logo "C:\Program Files (x86)\Zeiss\CALYPSO 6.4\pictures\cal.bmp" "C:\Program Files (x86)\Zeiss\CALYPSO 6.4\calypso.im"')
            # 打开本地程序的下载路径
            #os.startfile(inspection)
            # 检查服务器网络连接
            if net.piwebserver_access():
                logger2.info('PiWeb数据库({})连接成功'.format(net.host['main']))
                # 设置更新测量的参数
                serCon = '22250In[{}]%2B22253In[{}]'.format(u_JobNumber, u_TaskNumber)
                partPath = '/Process/Job_Management/'
                mes_data = {'22251':2, '22200':inspection_name}
                API = PiWebAPI(net.host['main'])
                API.UpdateMeasurement(mes_data, partPath=partPath, serCon=serCon)
                if API.GET_code == 200:
                    logger2.info("成功获取数据库信息")
                    if API.Mes_PUT_code == 200:
                        logger2.info("成功修改{} {}".format(u_JobNumber, u_TaskNumber))
                    elif API.Mes_PUT_code == 300:
                        logger2.warn(API.Mes_PUT_text)
                    else:
                        logger2.error(API.Mes_PUT_text)
                        showError("Status Code: PUT {} 详细信息请查看log文件".format(API.Mes_PUT_code))
                else:
                    logger2.error(API.GET_Text)
                    showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
            else:
                message = "({})网络连接失败,请检查网络后再试".format(net.host['ip'])
                logger2.error(message)
                showError(message)
        else:
            message = "({})网络连接失败,请检查网络后再试".format(net.data_ping)
            logger2.error(message)
            showError(message)
    except FileNotFoundError as f:
        logger2.error('FileNotFoundError: {}'.format(f))
        showError("系统文件缺失！")
    except KeyError as k:
        logger2.error('KeyError: 未找到K{}数据'.format(k))
        showError('KeyError: 未找到K{}数据'.format(k))
    except Exception as e:
        logger2.error('Error: {}'.format(e))
        showError('运行出现错误，详情请查看log文件')
    else:
        showInfo("测量程序加载成功，请在测量软件中选择测量程序")

def create_new_part(log_path, mes_data):
    # 设置logger
    logger5 = logging.getLogger('Maintain')
    logger5.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                        - %(message)s')
    fh.setFormatter(formatter)
    logger5.addHandler(fh)
    logger5.info("成功进入create_new_part子程序")
    try:
        load_ui.process.set("开始保存新建工件数据...")
        load_ui.process.set("正在检查网络连接...")
        net = netaccess()
        # 检查本机与PiWeb服务器的网络链接
        if net.piwebserver_access():
            logger5.info('PiWeb数据库({})连接成功'.format(net.host['main']))
            # 检查本机与文件服务器的网络链接
            if net.fileserver_access():
                logger5.info('文件服务器({})连接成功'.format(net.data_ping))
                # 如果图纸的地址不为空，上传图纸
                if load_ui.drawing_path.get() != '':
                    file_list = load_ui.drawing_path.get().split(';')
                    dstpath = os.path.join(net.data_dir, mes_data['22031'], 'Drawing')
                    for file in file_list:
                        t = threading.Thread(target=load_ui.Dynamic_process, args=("正在上传{}".format(file.split('\\')[-1]),))
                        t.setDaemon(True)
                        t.start()
                        srcfile = file
                        mkdir(dstpath)
                        dstfile = os.path.join(dstpath, file.split('\\')[-1])
                        shutil.copyfile(srcfile, dstfile)
                        mes_data.update({'22239':dstfile})
                        stop_thread(t)
                # 设置更新测量的参数
                API = PiWebAPI(net.host['main'])
                mes_data.update({'22252':3,'22258':"常规"})
                API.CreateNewMeasurement(mes_data, partPath='/Process/Product_List/')
                if API.Mes_POST_code != 201:
                    logger5.error(API.Mes_POST_text)
                    showError("Status Code:{} 详细信息请查看log文件".format(API.Mes_POST_code))
                    load_ui.process.set("新建失败")
                elif API.Mes_POST_code == 201:
                    logger5.info("新建工件POST成功")
                    load_ui.process.set("新建成功")
                    showInfo("新建工件 {} {} 成功！\n点击左上角\"后退\"返回\"工件信息管理页面\"查看".format(mes_data['22030'], mes_data['22031']))
            else:
                message = "({})网络连接失败,请检查网络后再试".format(net.data_ping)
                load_ui.process.set(message)
                logger5.error(message)
                showError(message)
        else:
            message = "({})网络连接失败,请检查网络后再试".format(net.host['ip'])
            load_ui.process.set(message)
            logger5.error(message)
            showError(message)
    except FileNotFoundError as f:
        logger5.error(f)
        showError(f)
    except PermissionError:
        message = "图纸文件处于打开状态，请关闭后重试"
        logger5.error(message)
        showError(message)
    except Exception as e:
        logger5.error(e)
        showError(e)
    finally:
        load_ui.destroy()

def get_uuid(log_path, key_data, para_dir):
    # 设置logger
    logger5 = logging.getLogger('Maintain')
    logger5.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                        - %(message)s')
    fh.setFormatter(formatter)
    logger5.addHandler(fh)
    logger5.info("成功进入get_uuid子程序")
    # 检查本机与PiWeb服务器的网络链接
    net = netaccess()
    if net.piwebserver_access():
        logger5.info('PiWeb数据库({})连接成功'.format(net.host['main']))
        # 设置更新测量的参数
        API = PiWebAPI(net.host['main'])
        API.measurements_url(partPath='/Process/Product_List/',serCon=key_data)
        # 通过url GET数据
        API.GET(API.mes_url)
        if API.GET_code == 200 and len(API.GET_Text) != 0:
            uuid = API.GET_Text[0]['uuid']
            with open(os.path.join(para_dir, 'modifiedpart.para'), 'w') as ass:
                ass.writelines('uuid = '+uuid)
                logger5.info("成功获取uuid:{}".format(uuid))
        elif API.GET_code == 200 and len(API.GET_Text) == 0:
            showError("没有获取uuid")
        else:
            showError(API.GET_code)

def update_part(log_path, mes_data):
    # 设置logger
    logger5 = logging.getLogger('Maintain')
    logger5.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                        - %(message)s')
    fh.setFormatter(formatter)
    logger5.addHandler(fh)
    logger5.info("成功进入create_new_part子程序")
    try:
        part = piwebconfig('modifiedpart.para', keep=True)
        logger5.info("成功读取modifiedpart.para中的信息")
        if 'uuid' not in part.txt_data.keys():
            logger5.error("没有正确获取工件信息的uuid")
            showError("没有正确获取工件更新信息")
        else:
            uuid = part.txt_data.pop('uuid')
            # 检查本机与PiWeb服务器的网络链接
            net = netaccess()
            if net.piwebserver_access():
                logger5.info('PiWeb数据库({})连接成功'.format(net.host['main']))
                # 设置更新测量的参数
                API = PiWebAPI(net.host['main'])
                API.UpdateMeasurementbyUuid(mes_data, uuid)
                if API.GET_code == 200:
                    logger5.info("成功获取数据库信息")
                    if API.Mes_PUT_code == 200:
                        logger5.info("成功修改工件{}".format(mes_data['22030']))
                        showInfo("修改成功！\n点击左上角\"后退\"返回\"工件信息管理页面\"查看")
                    elif API.Mes_PUT_code == 300:
                        logger5.warn(API.Mes_PUT_text)
                    else:
                        logger5.error(API.Mes_PUT_text)
                        showError("Status Code: PUT {} 详细信息请查看log文件".format(API.Mes_PUT_code))
                else:
                    logger5.error(API.GET_Text)
                    showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
            else:
                message = "({})网络连接失败,请检查网络后再试".format(net.host['ip'])
                logger5.error(message)
                showError(message)
    except FileNotFoundError:
        message = "没有检测到PiWeb生成的数据"
        logger5.error(message)
        showError(message)

def update_drawing(log_path, mes_data):
    # 设置logger
    logger5 = logging.getLogger('Maintain')
    logger5.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                        - %(message)s')
    fh.setFormatter(formatter)
    logger5.addHandler(fh)
    logger5.info("成功进入create_new_part子程序")
    try:
        # 读取工件uuid信息
        part = piwebconfig('modifiedpart.para', keep=True)
        logger5.info("成功读取modifiedpart.para中的信息")
        if 'uuid' not in part.txt_data.keys():
            logger5.error("没有正确获取工件信息的uuid")
            showError("没有正确获取工件更新信息")
        else:
            uuid = part.txt_data.pop('uuid')
            net = netaccess()
            if net.piwebserver_access():
                logger5.info('PiWeb数据库({})连接成功'.format(net.host['main']))
                if net.fileserver_access():
                    logger5.info('文件服务器({})连接成功'.format(net.data_ping))
                    # 上传图纸
                    if load_ui.drawing_path.get() != '':
                        dstpath = os.path.join(net.data_dir, mes_data['22031'], 'Drawing')
                        file_list = load_ui.drawing_path.get().split(';')
                        for file in file_list:
                            t = threading.Thread(target=load_ui.Dynamic_process, args=("正在上传{}".format(file.split('\\')[-1]),))
                            t.setDaemon(True)
                            t.start()
                            srcfile = file
                            mkdir(dstpath)
                            dstfile = os.path.join(dstpath, file.split('\\')[-1])
                            shutil.copyfile(srcfile, dstfile)
                            mes_data.update({'22239':dstfile})
                            stop_thread(t)
                    # 设置更新测量的参数
                    API = PiWebAPI(net.host['main'])
                    API.UpdateMeasurementbyUuid(mes_data, uuid)
                    if API.GET_code == 200:
                        logger5.info("成功获取数据库信息")
                        if API.Mes_PUT_code == 200:
                            logger5.info("工件{}上传图纸成功".format(mes_data['22031']))
                            showInfo("上传图纸成功！\n点击左上角\"后退\"返回\"工件信息管理页面\"查看")
                        elif API.Mes_PUT_code == 300:
                            logger5.warn(API.Mes_PUT_text)
                        else:
                            logger5.error(API.Mes_PUT_text)
                            showError("Status Code: PUT {} 详细信息请查看log文件".format(API.Mes_PUT_code))
                    else:
                        logger5.error(API.GET_Text)
                        showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
                else:
                    message = "({})网络连接失败,请检查网络后再试".format(net.data_ping)
                    load_ui.process.set(message)
                    logger5.error(message)
                    showError(message)
            else:
                message = "({})网络连接失败,请检查网络后再试".format(net.host['ip'])
                load_ui.process.set(message)
                logger5.error(message)
                showError(message)
    except FileNotFoundError as f:
        logger5.error(f)
        showError(f)
    except PermissionError:
        message = "图纸文件处于打开状态，请关闭后重试"
        logger5.error(message)
        showError(message)
    except Exception as e:
        logger5.error(e)
        showError(e)
    finally:
        load_ui.destroy()

def inspection_backup(log_path, program_path, program_data, target_dir, ctl_info):
    """
    为工件新建一个测量程序，并上传至文件服务器和PiWeb服务器
    """
    logger2 = logging.getLogger('Inspection')
    logger2.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                      - %(message)s')
    fh.setFormatter(formatter)
    logger2.addHandler(fh)
    try:
        # 检查文件服务器和PiWeb服务器的网络连接
        c = threading.Thread(target=load_ui.Dynamic_process, args=("正在连接数据库,请稍候",))
        c.setDaemon(True)
        c.start()
        net = netaccess()
        if net.fileserver_access():
            logger2.info('文件服务器连接成功')
            if net.piwebserver_access():
                logger2.info('PiWeb服务器连接成功')
                stop_thread(c)
                load_ui.process.set("网络连接成功！")
                # 网络连接ok，准备需要更新到PiWeb服务器的数据
                ins = InspectionBackup(program_path, target_dir)
                # 设置当前时间
                current_time = datetime.datetime.now()
                change_time = current_time + datetime.timedelta(hours=-8)
                time_str = change_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                program_data.update({'22200':ins.program_name, '10031':'latest'}) # '22202':'创建程序', '22201':ins.program_dir, '10031':'latest'
                # 1.检查PiWeb服务器是否存在这个程序的信息
                API = PiWebAPI(net.host['main'])
                ser_data = {}
                ser_data.update(program_data)
                if '9' in ser_data:
                    ser_data.pop('9')
                if '22202' in ser_data:
                    ser_data.pop('22202')
                if '22007' in ser_data:
                    ser_data.pop('22007')
                if '22008' in ser_data:
                    ser_data.pop('22008')
                serCon = dictToserCon(ser_data)
                API.GetMeasurementUuid(partPath='/Process/Inspection_List/', serCon=serCon)
                # 2.1 如果没有获得当前需要添加的uuid,则继续更新信息，并传入附件
                if API.GetUuid_code == 300:
                    program_data.update({'22201':ins.program_dir, '4':time_str})
                    API.CreateNewMeasurementwithRaw(program_data, ctl_info, writeKey='23001', partPath='/Process/Inspection_List/')
                    # 2.1.1 如果创建成功，开始复制测量程序
                    if API.CNR_code == 200:
                        logger2.info("在PiWeb服务器中创建新测量程序成功，开始复制测量程序")
                        load_ui.process.set("在数据库中新建测量程序信息成功,开始上传附件")
                        # 获取新创建的uuid
                        mes_uuid = API.newuuid
                        # 开始复制程序
                        # 因为数据库中没有该测量程序的信息，所以直接复制，如果目标路径中有该程序，直接干掉
                        up = threading.Thread(target=load_ui.Dynamic_process, args=("正在上传测量程序",))
                        up.setDaemon(True)
                        up.start()
                        # 同步复制测量程序
                        ins.backup(mes_uuid)
                        stop_thread(up)
                        logger2.info('新程序{}备份成功'.format(ins.program_name))
                        showInfo('新程序 {} 备份成功\n点击左上角\"后退\"返回\"测量程序管理页面\"查看'.format(ins.program_name))
                    # 2.1.2 如果创建失败
                    else:
                        logger2.error(API.CNR_text)
                        load_ui.process.set("在PiWeb服务器中新建测量程序信息失败")
                        showError("Status Code:404 详细信息请查看log文件")
                # 2.2 如果测量程序的信息已经存在了,但是文件服务器没有新程序，直接复制程序
                elif API.GetUuid_code == 200 and not os.path.exists(ins.program_dir):
                    mes_uuid = API.uuid_list[0]
                    logger2.info("PiWeb数据库中已有信息，文件服务器中没有新程序，准备复制程序")
                    load_ui.process.set("在数据库中新建测量程序信息成功,开始上传附件")
                    up = threading.Thread(target=load_ui.Dynamic_process, args=("正在上传测量程序",))
                    up.setDaemon(True)
                    up.start()
                    # 同步复制测量程序
                    ins.backup(mes_uuid)
                    stop_thread(up)
                    logger2.info('新程序{}备份成功'.format(ins.program_name))
                    showInfo('新程序 {} 备份成功\n点击左上角\"后退\"返回\"测量程序管理页面\"查看'.format(ins.program_name))
                # 2.3 如果测量程序的信息已经存在了,而且文件服务器也有新程序，提示使用更新功能
                elif API.GetUuid_code == 200 and os.path.exists(ins.program_dir):
                    showInfo('检测到系统中已经存在测量程序 {} \n点击左上角\"后退\"返回\"测量程序管理页面\"，使用列表中的\"更新\"功能来更新程序'.format(ins.program_name))
            else:
                stop_thread(c)
                message = "({})网络连接失败,请检查网络后再试".format(net.host['ip'])
                logger2.error(message)
                showError(message)
        else:
            stop_thread(c)
            message = "({})网络连接失败,请检查网络后再试".format(net.data_ping)
            logger2.error(message)
            showError(message)
    except FileNotFoundError as f:
        logger2.error(f)
        showError(f)
    except shutil.Error as e:
        message = "文件传输出现异常"
        logger2.error(message+':'+e)
        showError(message)
    except Exception as e:
        logger2.error(e)
        showError("程序运行终止，请查看log文件")
    finally:
        load_ui.destroy()
                        
def inspection_update(log_path, program_path, program_data, target_dir, ctl_info):
    """
    """
    logger2 = logging.getLogger('Inspection')
    logger2.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                      - %(message)s')
    fh.setFormatter(formatter)
    logger2.addHandler(fh)
    try:
        # 检查文件服务器和PiWeb服务器的网络连接
        c = threading.Thread(target=load_ui.Dynamic_process, args=("正在连接数据库,请稍候",))
        c.setDaemon(True)
        c.start()
        net = netaccess()
        if net.fileserver_access():
            logger2.info('文件服务器连接成功')
            if net.piwebserver_access():
                logger2.info('PiWeb服务器连接成功')
                stop_thread(c)
                load_ui.process.set("网络连接成功！")
                # 网络连接ok，准备需要更新到PiWeb服务器的数据
                ins = InspectionBackup(program_path, target_dir)
                # 1.检查程序名和现有程序是否相同
                if ins.program_name != program_data['22200']:
                    logger2.warn("新上传程序名与先有程序名不符，请检查!如果为新程序，请使用\"新建程序\"功能")
                    showInfo("新上传程序名与先有程序名不符，请检查!\n如果为新程序，请使用\"新建程序\"功能")
                # 2.如果程序名称相同，查找数据库中该程序最新的一条记录
                else:
                    # 设置当前时间
                    current_time = datetime.datetime.now()
                    change_time = current_time + datetime.timedelta(hours=-8)
                    time_str = change_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    program_data.update({'10031':'latest'}) # '22202':'创建程序', '22201':ins.program_dir, '10031':'latest'
                    # 1.检查PiWeb服务器是否存在这个程序的信息
                    API = PiWebAPI(net.host['main'])
                    ser_data = {}
                    ser_data.update(program_data)
                    if '9' in ser_data:
                        ser_data.pop('9')
                    if '22202' in ser_data:
                        ser_data.pop('22202')
                    if '22007' in ser_data:
                        ser_data.pop('22007')
                    if '22008' in ser_data:
                        ser_data.pop('22008')
                    serCon = dictToserCon(ser_data)
                    API.GetMeasurementUuid(partPath='/Process/Inspection_List/', serCon=serCon)
                    
                    # 如果PiWeb服务器中没有找到这条数据
                    if API.GetUuid_code == 300:
                        logger2.warn("检测到该程序为新程序，请使用\"新建程序\"功能")
                        showInfo("检测到该程序为新程序，请使用\"新建程序\"功能")
                    # 如果PiWeb服务器中找到这条数据
                    else:
                        current_uuid = API.uuid_list[0]
                        # 检查当前文件服务器中的程序的versionid.ini是否存在
                        # 如果不存在，说明上次更新程序的是否发生异常，直接删除原程序，备份新程序至该文件夹
                        if not os.path.exists(os.path.join(ins.program_dir, 'versionid.ini')):
                            logger2.info("PiWeb数据库中已有信息，文件服务器中没有新程序，准备复制程序")
                            up = threading.Thread(target=load_ui.Dynamic_process, args=("正在上传测量程序",))
                            up.setDaemon(True)
                            up.start()
                            # 同步复制测量程序
                            ins.backup(current_uuid)
                            stop_thread(up)
                            logger2.info('新程序{}备份成功'.format(ins.program_name))
                            showInfo('新程序 {} 备份成功\n点击左上角\"后退\"返回\"测量程序管理页面\"查看'.format(ins.program_name))
                        # 如果存在，则继续检查version.ini中存储的uuid和当前的uuid是否一致
                        else:
                            with open(os.path.join(ins.program_dir, 'versionid.ini'), 'r') as v:
                                file_uuid = v.readline()
                            if file_uuid != current_uuid:
                                pass
                            # 如果找到PiWeb服务器中的最新记录和文件服务器中的最新记录一致，一切正常，备份该程序并上传最新程序
                            else:
                                # 创建历史版本的路径
                                ins.history_dir()
                                logger2.info('成功创建版本管理路径')
                                if not os.path.exists(ins.history_path):
                                    # 在PiWeb服务器中，将原有的最近结果更新为历史版本
                                    API.UpdateMeasurementbyUuid({'10031':'old', '22201':ins.history_path}, current_uuid)
                                    # 在文件服务器中，将原有的最近结果更新为历史版本
                                    up = threading.Thread(target=load_ui.Dynamic_process, args=("正在将测量程序{}保存为历史版本".format(ins.program_name),))
                                    up.setDaemon(True)
                                    up.start()
                                    shutil.copytree(ins.program_dir, ins.history_path)
                                    with open(os.path.join(ins.history_path, 'versionid.ini'), 'w') as v:
                                        v.writelines(current_uuid)
                                    stop_thread(up)
                                    # 在PiWeb服务器中，创建新程序信息
                                    logger2.info("在PiWeb数据库中更新程序信息")
                                    load_ui.process.set("正在更新数据库...")
                                    program_data.update({'22201':ins.program_dir, '4':time_str})
                                    API.CreateNewMeasurementwithRaw(program_data, ctl_info, writeKey='23001', partPath='/Process/Inspection_List/')
                                    mes_uuid = API.newuuid
                                    new = threading.Thread(target=load_ui.Dynamic_process, args=("正在上传测量程序",))
                                    new.setDaemon(True)
                                    new.start()
                                    ins.backup(mes_uuid)
                                    stop_thread(new)
                                    logger2.info('新程序{}备份成功'.format(ins.program_name))
                                    showInfo('新程序 {} 备份成功\n点击左上角\"后退\"返回\"测量程序管理页面\"查看'.format(ins.program_name))
                                else:
                                    message = "备份时间重合，请稍后再试"
                                    logger2.error(message)
                                    showError(message)
            else:
                stop_thread(c)
                message = "({})网络连接失败,请检查网络后再试".format(net.host['ip'])
                logger2.error(message)
                showError(message)
        else:
            stop_thread(c)
            message = "({})网络连接失败,请检查网络后再试".format(net.data_ping)
            logger2.error(message)
            showError(message)
    except FileNotFoundError as f:
        logger2.error(f)
        showError(f)
    except shutil.Error as e:
        message = "文件传输出现异常"
        logger2.error(message+':'+e)
        showError(message)
    except Exception as e:
        logger2.error(e)
        showError("程序运行终止，请查看log文件")
    finally:
        load_ui.destroy()

def filter_change(log_path, ptx_path, openptx, delay, splash):
    # 打开loading窗口
    fil = system_config()
    logger3 = logging.getLogger('Filter')
    logger3.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                          - %(message)s')
    fh.setFormatter(formatter)
    logger3.addHandler(fh)
    logger3.info("成功进入更改筛选条件子程序")
    # 设置exe的路径
    monitor = r'C:\Program Files\Zeiss\PiWeb\Monitor.exe'
    cmdmon = r'C:\Program Files\Zeiss\PiWeb\Cmdmon.exe'
    ptx_path = os.path.join(fil.qFlow, ptx_path)
    msel_path = os.path.join(fil.para_dir, 'search.msel')
    if os.path.exists(ptx_path):
        if openptx:
            command_line = '"{}" -open "{}" -searchCriteria "{}" -nosplash -maximize'.format(monitor, ptx_path, msel_path)
        else:
            command_line = '"{}" -open "{}" -searchCriteria "{}" -save "{}"'.format(cmdmon, ptx_path, msel_path, ptx_path)
        thread_it(run_cmd, command_line)
        time.sleep(delay)
    else:
        logger3.error("没有找到{}".format(ptx_path))
        showError("没有找到{}".format(ptx_path))
    if splash == 'big':
        window(fil.rela_dir, 'stop')
    elif splash == 'bar':
        load_ui.close.set('close')
        load_ui.destroy()
        logger3.info("成功关闭进度条")

def change_common_part(log_path, common_part, ptx_path, master_path, delay):
    logger3 = logging.getLogger('Filter')
    logger3.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                          - %(message)s')
    fh.setFormatter(formatter)
    logger3.addHandler(fh)
    logger3.info("成功进入更改common part子程序")
    common = system_config()
    monitor = r'C:\Program Files\Zeiss\PiWeb\Monitor.exe'
    cmdmon = r'C:\Program Files\Zeiss\PiWeb\Cmdmon.exe'
    ptx_path = os.path.join(common.qFlow, ptx_path)
    master_ptx = os.path.join(common.qFlow, master_path)
    msel_path = os.path.join(common.para_dir, 'search.msel')
    command_line_1 = '"{}" -open "{}" -changeCommonParentPartPath "{}" -save "{}"'.format(cmdmon, master_ptx, common_part, ptx_path)
    run_cmd(command_line_1)
    window(common.rela_dir, 'switch opening')
    command_line_2 = '"{}" -open "{}" -searchCriteria "{}" -nosplash -maximize'.format(monitor, ptx_path, msel_path)
    thread_it(run_cmd, command_line_2)
    time.sleep(delay)
    window(common.rela_dir, 'stop')

def approve_measurement(log_path, checkPartPath=None, checkSerCon=None, duplicate=None, update=False, partPath=None, serCon=None, compareSerCon=None, jobStatus=None):
    logger4 = logging.getLogger('Self_Check')    
    logger4.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                      - %(message)s')
    fh.setFormatter(formatter)
    logger4.addHandler(fh)
    logger4.info("成功进入更改approve_measurement子程序")
    go_status = None
    net = netaccess()
    if net.piwebserver_access():
        API = PiWebAPI(net.host['main'])
        API.CheckKeyDuplicate(partPath=checkPartPath, serCon=checkSerCon, duplicate=duplicate, compareSerCon=compareSerCon)
        # 如果同一个Part ID存在多个结果发布
        if len(API.duplicateValue) != 0:
            errorInfo = ",".join(API.duplicateValue)
            showInfo("工件编号: {} 有多个测量结果\n请检查是否正确！".format(errorInfo))
            logger4.info("工件编号: {} 有多个测量结果".format(errorInfo))
        # 如果有测量过的Part ID没有结果发布
        elif len(API.dumped_key) != 0:
            errorInfo = ",".join(API.dumped_key)
            askQuestion("工件编号: {} 没有测量结果\n是否放弃该工件所有测量结果?".format(errorInfo))
            if load_ui.askqform == 'yes':
                logger4.warn("工件编号: {} 的所有测量结果被放弃".format(errorInfo))
                go_status = 'go'
                if update:
                    mes_data = {'22251':jobStatus}
                    API.UpdateMeasurement(mes_data, partPath=partPath, serCon=serCon)
                    if API.GET_code == 200:
                        logger4.info("成功获取数据库信息")
                        if API.Mes_PUT_code == 200:
                            logger4.info("成功修改{}".format(serCon))
                            showInfo("测量结果发布成功，请关闭页面返回任务看板！")
                        elif API.Mes_PUT_code == 300:
                            logger4.warn(API.Mes_PUT_text)
                        else:
                            logger4.error(API.Mes_PUT_text)
                            showError("Status Code: PUT {} 详细信息请查看log文件".format(API.Mes_PUT_code))
                    else:
                        logger4.error(API.GET_Text)
                        showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
        # 如果没有测量结果被发布
        elif API.Mes_DUP_code == 300:
            askQuestion("没有测量结果被发布\n是否确定?")
            if load_ui.askqform == 'yes':
                logger4.warn("没有测量结果被发布")
                go_status = 'go'
                if update:
                    mes_data = {'22251':jobStatus}
                    API.UpdateMeasurement(mes_data, partPath=partPath, serCon=serCon)
                    if API.GET_code == 200:
                        logger4.info("成功获取数据库信息")
                        if API.Mes_PUT_code == 200:
                            logger4.info("成功修改{}".format(serCon))
                            showInfo("测量结果发布成功，请关闭页面返回任务看板！")
                        elif API.Mes_PUT_code == 300:
                            logger4.warn(API.Mes_PUT_text)
                        else:
                            logger4.error(API.Mes_PUT_text)
                            showError("Status Code: PUT {} 详细信息请查看log文件".format(API.Mes_PUT_code))
                    else:
                        logger4.error(API.GET_Text)
                        showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
        elif API.Mes_DUP_code == 404:
            showError("网络状态异常！")
            logger4.error('Duplicate Check Error 404')
        elif len(API.duplicateValue) == 0 and len(API.dumped_key) == 0 and API.Mes_DUP_code == 200:
            # 设置更新测量的参数
            logger4.info(API.Mes_DUP_code)
            go_status = 'go'
            if update:
                mes_data = {'22251':jobStatus}
                API.UpdateMeasurement(mes_data, partPath=partPath, serCon=serCon)
                if API.GET_code == 200:
                    logger4.info("成功获取数据库信息")
                    if API.Mes_PUT_code == 200:
                        logger4.info("成功修改{}".format(serCon))
                        showInfo("测量结果发布成功，请关闭页面返回任务看板！")
                    elif API.Mes_PUT_code == 300:
                        logger4.warn(API.Mes_PUT_text)
                    else:
                        logger4.error(API.Mes_PUT_text)
                        showError("Status Code: PUT {} 详细信息请查看log文件".format(API.Mes_PUT_code))
                else:
                    logger4.error(API.GET_Text)
                    showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
    else:
        message = "({})网络连接失败,请检查网络后再试".format(net.data_ping)
        logger4.error(message)
        showError(message)
    return go_status

def remeasurement(log_path, checkPartPath=None, checkSerCon=None, partPath=None, serCon=None):
    logger4 = logging.getLogger('Job_Close')
    logger4.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                       - %(message)s')
    fh.setFormatter(formatter)
    logger4.addHandler(fh)
    logger4.info("成功进入更改remeasurement子程序")
    # 检查网络连接
    net = netaccess()
    if net.piwebserver_access():
        API = PiWebAPI(net.host['main'])
        # 获得测量数据中的url
        API.GetMeasurementAttribute(getattribute=['14'], partPath=checkPartPath, serCon=checkSerCon)
        # 获取需要复测的Part ID
        if API.Mes_GET_code == 200 and API.MeaAtt['14'] != []:
            # 将获得的Part ID转换为字符串
            partid = ','.join(API.MeaAtt['14'])
            logger4.info("成功获取需要复测的Part ID")
            # 从K9中获取现有复测次数的状态
            API.GetMeasurementAttribute(getattribute=['9'], partPath=partPath, serCon=serCon)
            if API.Mes_GET_code == 200 and API.MeaAtt['9'] != []:
                re_list = [int(r[1:]) for r in API.MeaAtt['9']]
                revision = 'R{}'.format(max(re_list) + 1)
            elif API.Mes_GET_code == 200 and API.MeaAtt['9'] == []:
                revision = 'R1'
            elif API.Mes_GET_code == 300:
                logger4.warn(API.Mes_GET_text)
            elif API.Mes_GET_code == 404:
                logger4.error(API.Mes_GET_code)
                showError("Status Code: GET {} 详细信息请查看log文件".format(API.Mes_GET_code))
            # 更新复测状态到Job Management中
            mes_data = {'14': partid, '9': revision, '22251': 1.2, '22254': 0}
            API.UpdateMeasurement(mes_data, partPath=partPath, serCon=serCon)
            if API.GET_code == 200:
                logger4.info("成功获取数据库信息")
                if API.Mes_PUT_code == 200:
                    logger4.info("成功修改{}".format(serCon))
                    # showInfo("测量任务已经进入复测状态，请关闭页面返回任务看板")
                elif API.Mes_PUT_code == 300:
                    logger4.warn(API.Mes_PUT_text)
                    showInfo("本页没有测量数据")
                else:
                    logger4.error(API.Mes_PUT_text)
                    showError("Status Code: PUT {} 详细信息请查看log文件".format(API.Mes_PUT_code))
            else:
                logger4.error(API.GET_Text)
                showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
            # 更新Rework enable为2
            new_data = {'22259': 2}
            API.UpdateMeasurement(new_data, partPath=checkPartPath, serCon=checkSerCon)
            if API.GET_code == 200:
                logger4.info("成功获取数据库信息")
                if API.Mes_PUT_code == 200:
                    logger4.info("成功修改{}".format(serCon))
                    showInfo("测量任务已经进入复测状态，请关闭页面返回任务看板")
                elif API.Mes_PUT_code == 300:
                    logger4.warn(API.Mes_PUT_text)
                    showInfo("本页没有测量数据")
                else:
                    logger4.error(API.Mes_PUT_text)
                    showError("Status Code: PUT {} 详细信息请查看log文件".format(API.Mes_PUT_code))
            else:
                logger4.error(API.GET_Text)
                showError("Status Code: GET {} 详细信息请查看log文件".format(API.GET_code))
        # 如果没有获取到需要复测的Part ID
        elif API.Mes_GET_code == 200 and API.MeaAtt['14'] == []:
            logger4.info("没有获得复测的工件ID，请选择需要复测的工件后再试")
            showError("没有获得复测的工件ID，请选择需要复测的工件后再试")
        elif API.Mes_GET_code == 300:
            logger4.warn(API.Mes_GET_text)
            showError("没有获得复测的工件ID，请选择需要复测的工件后再试")
        elif API.Mes_GET_code == 404:
            logger4.error(API.Mes_GET_code)
            showError("Status Code: GET {} 详细信息请查看log文件".format(API.Mes_GET_code))
    else:
        message = "({})网络连接失败,请检查网络后再试".format(net.data_ping)
        logger4.error(message)
        showError(message)

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
            'parent': ['10.202.0.9', r'\\10.202.0.9\shcc\qFlow_Project\File_Server', 'shcc', 'Sh@12345'],
            'backup': r'\\10.202.0.9\shcc\qFlow_Project\File_Server',
            'temp': r'C:\Demo_Data\Local_Temp',
            'failure': r'C:\Demo_Data\Import_Failure',
            'calypso': r'C:\Users\Public\Documents\Zeiss\CALYPSO\workarea\inspections',
            'calypso_base': r'C:\Users\Public\Documents\Zeiss\CALYPSO'
        },
        'host':
        {
            'ip': '10.202.120.59',
            'main': r'http://10.202.120.59:8888'
        }
    }
    with open(r'C:\Users\ZCFJIAN1\Documents\Python Scripts\GitHub\Mes_Process\Program_Files\relative_files\config.json', 'w') as j:
        json.dump(a, j, sort_keys=False, indent=2)

def get_input_args():
    """
    设置程序Argument。
    强制argument：step(用来获取运行那一部分程序)
    """
    parser = argparse.ArgumentParser(description='Retrieve some parameters')
    # 设置数据目录:
    parser.add_argument('step', type=str,
                        help='获取希望调用的功能:\
                            create:创建新的测量任务\
                            assign:预发布测量任务\
                            adjust:修改测量任务信息\
                            delete:删除所有预发布的测量任务\
                            changequantity:修改预发布的测量任务中的待测数量\
                            publish:发布预发布的测量任务\
                            download -path <absolute path> -inspection <inspection name>:下载选中的测量程序\
                            filter -filterkey <filter key and value> -filterptx <relative path> -openptx <True> -delay <3>:修改模板的筛选条件，并支持直接打开模板')
    parser.add_argument('-para', type=str, default=None)
    parser.add_argument('-level', type=str, default=None,
                        help='配合download使用,测量程序备份目录的最大层级数')
    parser.add_argument('-software', type=str, default=None)
    parser.add_argument('-path', type=str, default=None,
                        help='配合download使用,获取文件服务器上测量程序的路径')
    parser.add_argument('-inspection', type=str, default=None,
                        help='配合download使用,获取测量程序的名称')
    parser.add_argument('-filterkey', type=str, default=None,
                        help='配合filter使用,获取筛选用的key值和筛选条件,eg.-filterkey 22030=030-1700-050-12,10030=latest')
    parser.add_argument('-filterptx', type=str, default=None,
                        help='配合filter使用，输入需要更改筛选条件的ptx与主目录的相对路径')
    parser.add_argument('-openptx', action ='store_true',
                        help='更改筛选条件之后是否直接打开模板')
    parser.add_argument('-delay', type=float, default=7,
                        help='更改筛选条件之后是否直接打开模板')
    parser.add_argument('-splash', type=str, default=None,
                        help='是否显示qFlow图标')
    parser.add_argument('-commonpart', type=str, default=None,
                        help='修改common part')
    parser.add_argument('-masterptx', type=str, default=None,
                        help='用来修改common part的标准模板')
    parser.add_argument('-checkPartPath', type=str, default=None)
    parser.add_argument('-checkSerCon', type=str, default=None)
    parser.add_argument('-duplicatekey', type=str, default=None)
    parser.add_argument('-compareSerCon', type=str, default=None)
    parser.add_argument('-update', action ='store_true',
                        help='检查重复项目后，是否更新数据库内容')
    parser.add_argument('-partPath', type=str, default=None)
    parser.add_argument('-serCon', type=str, default=None)
    parser.add_argument('-jobStatus', type=int, default=None)
    return parser.parse_args()

def main():
    # 读取配置文件中的信息和程序路径
    sys_info = system_config()
    sys_info.config_path_reader()
    # 设置log文件存储的位置
    current_time = time.strftime('%Y%m%d', time.localtime(time.time()))
    log_name = current_time + '.log'
    log_path = os.path.join(sys_info.rela_dir, 'log_file', log_name)
    mkdir(sys_info.rela_dir + r'\log_file')
    # 设置主程序的logger
    logger0 = logging.getLogger('Mes_Pros_Main')
    logger0.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding='UTF-8')
    formatter = logging.Formatter(
        '[              ] %(asctime)s %(levelname)s   %(name)s                   - %(message)s')
    fh.setFormatter(formatter)
    logger0.addHandler(fh)
    # 开始读取Monitor传输的arguments
    in_arg = get_input_args()
    # 创建工单
    if in_arg.step == 'create':
        logger0.info("Argument:'{}'获取正确，运行创建工单程序".format(in_arg.step))
        job_number_create(log_path, sys_info.para_dir)
    # catalog类型输出，从Index中获取Entry
    elif in_arg.step == 'catalog':
        logger0.info("Argument:'{}'获取正确，运行catalog程序".format(in_arg.step))
        catalog_transfer(in_arg.para)
    # 预派工
    elif in_arg.step == 'assign':
        logger0.info("Argument:'{}'获取正确，运行派工程序".format(in_arg.step))
        job_assignment(log_path)
    # 修改测量任务
    elif in_arg.step == 'adjust':
        logger0.info("Argument:'{}'获取正确，运行测量任务修改程序".format(in_arg.step))
        job_adjustment(log_path)
    # 删除测量工单
    elif in_arg.step == 'delete':
        logger0.info("Argument:'{}'获取正确，运行测量任务删除程序".format(in_arg.step))
        job_delete(log_path)
    # 修改测量零件数量
    elif in_arg.step == 'changequantity':
        logger0.info("Argument:'{}'获取正确，运行测量工件数量修改程序".format(in_arg.step))
        change_job_quantity(log_path)
    # 正式发布工单
    elif in_arg.step == 'publish':
        logger0.info("Argument:'{}'获取正确，运行工单发布程序".format(in_arg.step))
        job_publish(log_path)
    # 在系统基础信息中创建新工件信息
    elif in_arg.step == 'newpart':
        logger0.info("Argument:'{}'获取正确，运行创建新工件程序".format(in_arg.step))
        if in_arg.filterkey == None:
            logger0.error('未设置filterkey参数')
            showError('未设置filterkey参数')
        else:
            filterkey = decode_url(in_arg.filterkey)
            key_data = filter_key_parser(filterkey)
            key_check = [value for value in key_data.values() if value != '']
            if len(key_check) < 5:
                showError("请完整填写数据后重试！")
                logger0.error("数据填写不完整")
                load_ui.destroy()
            elif len(key_check) == 5:
                Button(load_ui, text="创建新工件并上传图纸", command=lambda: thread_it(create_new_part, log_path, key_data),relief=GROOVE, width=18, height=2).grid(row=4, column=1, columnspan=4, sticky=E)
                Label(load_ui, text="",  width=3).grid(row=5, column=5) #右边
                load_ui.Drawing_upload()
                load_ui.mainloop()
    # 在列表中获取本次测量的uuid
    elif in_arg.step == 'getuuid':
        logger0.info("Argument:'{}'获取正确，运行获取uuid程序".format(in_arg.step))
        if in_arg.filterkey == None:
            logger0.error('未设置filterkey参数')
            showError('未设置filterkey参数')
        else:
            filterkey = decode_url(in_arg.filterkey)
            key_data = filter_key_parser(filterkey)
            serCon_list = ['{}In[{}]'.format(key,value) for key,value in key_data.items()]
            serCon = '%2B'.join(serCon_list)
            get_uuid(log_path, serCon, sys_info.para_dir)
    # 在基础信息中修改工件信息
    elif in_arg.step == 'updatepart':
        logger0.info("Argument:'{}'获取正确，运行创建新工件程序".format(in_arg.step))
        if in_arg.filterkey == None:
            logger0.error('未设置filterkey参数')
            showError('未设置filterkey参数')
        else:
            filterkey = decode_url(in_arg.filterkey)
            key_data = filter_key_parser(filterkey)
            key_check = [value for value in key_data.values() if value != '']
            if len(key_check) < 5:
                showError("请完整填写数据后重试！")
                logger0.error("数据填写不完整")
                load_ui.destroy()
            elif len(key_check) == 5:
                update_part(log_path, key_data)
    elif in_arg.step == 'uploaddwg':
        logger0.info("Argument:'{}'获取正确，运行创建新工件程序".format(in_arg.step))
        if in_arg.filterkey == None:
            logger0.error('未设置filterkey参数')
            showError('未设置filterkey参数')
        else:
            filterkey = decode_url(in_arg.filterkey)
            key_data = filter_key_parser(filterkey)
            if key_data['22239'] == '':
                Button(load_ui, text="上传图纸", command=lambda: thread_it(update_drawing, log_path, key_data),relief=GROOVE, width=18, height=2).grid(row=4, column=1, columnspan=4, sticky=E)
                Label(load_ui, text="",  width=3).grid(row=5, column=5) #右边
                load_ui.Drawing_upload()
                load_ui.mainloop()
            else:
                Button(load_ui, text="更新图纸", command=lambda: thread_it(update_drawing, log_path, key_data),relief=GROOVE, width=18, height=2).grid(row=4, column=1, columnspan=4, sticky=E)
                Label(load_ui, text="",  width=3).grid(row=5, column=5) #右边
                load_ui.Drawing_upload()
                load_ui.mainloop()
    # 下载存储在文件服务器中的测量程序，并修改表头信息
    elif in_arg.step == 'download':
        logger0.info("Argument:'{}'获取正确，运行下载测量程序程序".format(in_arg.step))
        target_dir = sys_info.data['calypso']
        base_dir = sys_info.data['calypso_base']
        source_dir = decode_url(in_arg.path)
        logger0.info("成功解码Argument: -path {}".format(source_dir))
        inspection_name = decode_url(in_arg.inspection)
        logger0.info("成功解码Argument: -inspection {}".format(inspection_name))
        t = threading.Thread(target=inspection_download, args=(log_path, sys_info.rela_dir, source_dir, target_dir, base_dir, inspection_name, sys_info.machine_interface_dir))
        t.setDaemon(True)
        t.start()
        load_ui.Loading()
        logger0.info('成功打开progress bar窗口')
        load_ui.mainloop()
    # 备份新编写的测量程序
    elif in_arg.step == 'backup':
        logger0.info("Argument:'{}'获取正确，运行测量程序备份程序".format(in_arg.step))
        catalog_transfer('inspection.para')
        inspection = piwebconfig('inspection.para')
        inspection.config_path_reader()
        target_dir = os.path.join(inspection.data['parent'][1], in_arg.level)
        if 'program_path' in inspection.txt_data.keys():
            program_path = inspection.txt_data.pop('program_path')
        else:
            program_path = ''
        load_ui.Inspection_upload(in_arg.software, program_path, log_path, inspection.txt_data, target_dir)
        load_ui.mainloop()
        # inspection_backup(in_arg.level, log_path)
    elif in_arg.step == 'inspectionupdate':
        logger0.info("Argument:'{}'获取正确，运行测量程序备份程序".format(in_arg.step))
        catalog_transfer('inspection.para')
        inspection = piwebconfig('inspection.para')
        inspection.config_path_reader()
        target_dir = os.path.join(inspection.data['parent'][1], in_arg.level)
        if 'program_path' in inspection.txt_data.keys():
            program_path = inspection.txt_data.pop('program_path')
        else:
            program_path = ''
        if inspection.txt_data['update'] == 'unchecked':
            load_ui.Inspection_upload(in_arg.software, program_path, log_path, inspection.txt_data, target_dir)
            load_ui.mainloop()
        elif inspection.txt_data['update'] == 'checked':
            pass
    # 修改PTX文件的筛选条件
    elif in_arg.step == 'filter':
        logger0.info("Argument:'{}'获取正确，运行更改筛选条件程序".format(in_arg.step))
        if in_arg.filterkey == None:
            logger0.error('未设置filterkey参数')
            showError('未设置filterkey参数')
        elif in_arg.filterptx == None:
            logger0.error('未设置filterptx参数')
            showError('未设置filterptx参数')
        else:
            key_data = filter_key_parser(in_arg.filterkey)
            if os.path.exists(os.path.join(sys_info.rela_dir, 'master.msel')):
                mesl_making(key_data)
                logger0.error('成功修改search.msel')
                t = threading.Thread(target=filter_change, args=(log_path, in_arg.filterptx, in_arg.openptx, in_arg.delay, in_arg.splash))
                t.setDaemon(True)
                t.start()
                if in_arg.splash == 'big':
                    window(sys_info.rela_dir, 'start loading')
                    logger0.info('成功打开qFlow loading窗口')
                    t.join()
                elif in_arg.splash == 'bar':
                    load_ui.Loading()
                    logger0.info('成功打开progress bar窗口')
                    load_ui.mainloop()
            else:
                logger0.error('没有找到master.msel')
                showError("没有找到master.msel")
    # 修改PTX文件的common part和筛选条件
    elif in_arg.step == 'commonpart':
        if in_arg.filterkey == None:
            logger0.error('未设置filterkey参数')
            showError('未设置filterkey参数')
        elif in_arg.filterptx == None:
            logger0.error('未设置filterptx参数')
            showError('未设置filterptx参数')
        else:
            key_data = filter_key_parser(in_arg.filterkey)
            if os.path.exists(os.path.join(sys_info.rela_dir, 'master.msel')):
                mesl_making(key_data)
                logger0.error('成功修改search.msel')
                common_part = decode_url(in_arg.commonpart)
                t = threading.Thread(target=change_common_part, args=(log_path, common_part, in_arg.filterptx, in_arg.masterptx, in_arg.delay))
                t.setDaemon(True)
                t.start()
                window(sys_info.rela_dir, 'start loading')
                logger0.info('成功打开qFlow loading窗口')
                t.join()
    # 发布测量结果时，检查测量结果是否有重复或未发布项目
    elif in_arg.step == 'checkduplicate':
        if in_arg.duplicatekey == None:
            logger0.error('未输入duplicatekey参数')
            showError('未输入duplicatekey参数')
        else:
            checkPartPath = decode_url(in_arg.checkPartPath)
            checkSerCon = decode_url(in_arg.checkSerCon)
            partPath = decode_url(in_arg.partPath)
            serCon = decode_url(in_arg.serCon)
            compareSerCon = decode_url(in_arg.compareSerCon)
            approve_measurement(log_path, checkPartPath, checkSerCon, in_arg.duplicatekey, in_arg.update, partPath, serCon, compareSerCon, in_arg.jobStatus)
    # 工程师传递复测信息
    elif in_arg.step == 'remeasurement':
        checkPartPath = decode_url(in_arg.checkPartPath)
        checkSerCon = decode_url(in_arg.checkSerCon)
        partPath = decode_url(in_arg.partPath)
        serCon = decode_url(in_arg.serCon)
        go_status = approve_measurement(log_path, checkPartPath=checkPartPath, checkSerCon=serCon+'%2B22259In[0,1]', duplicate='14', update=False, partPath=None, serCon=None, compareSerCon=serCon, jobStatus=None)
        if go_status == 'go':
            remeasurement(log_path, checkPartPath, checkSerCon, partPath, serCon)
    # 软件参数调试用
    elif in_arg.step == 'output':
        p = [in_arg.checkPartPath, in_arg.checkSerCon, in_arg.duplicatekey, in_arg.partPath, in_arg.serCon, in_arg.compareSerCon]
        ps = ";".join(p)
        showError(ps)
    # 报错
    else:
        message = "Argument获取不正确: {}".format(in_arg.step)
        logger0.error(message)
        showError(message)

if __name__ == "__main__":
    load_ui = UI()
    #load_ui.Inspection_upload('CALYPSO')
    main()
    #decode_url(r'\\10.202.0.9\shcc\qFlow_Project\CMM%20Programs\8')
    #api = PiWebAPI('http://10.202.120.59:8888')
    #url = 'http://10.202.120.59:8888/rawDataServiceRest/rawData/characteristic/a0dd372d-091d-4129-ba57-260ee01c38cd'
    #url_m = 'http://10.202.120.59:8888/rawDataServiceRest/rawData/measurement/a24d63a8-5559-11e9-b4ec-14abc5a15d02'
    #url_v = 'http://10.202.120.59:8888/rawDataServiceRest/rawData/value/a24d63a8-5559-11e9-b4ec-14abc5a15d02|a0dd372d-091d-4129-ba57-260ee01c38cd'
    #file_path = 'part.PNG'
    #api.RawDataPost(url_v, file_path)
    # /rawDataServiceRest/rawData/part/b8f5d3fe-5bd5-406b-8053-67f647f09dc7
    #api.GetMeasurementAttribute(getattribute=['9'], partPath='/Process/Job_Management/', serCon='22250In[JOB190325103023]')
    #print(api.MeaAtt['9']==[])
    #api.CreateNewMeasurement({'22253': 2}, partPath='/Process/Job_Management/')
    #api.measurements_url(partPath='/Process/Job_Management/', serCon='22250In[JOB190301143103]')
    #api.DeleteMeasurement(partPath='/Process/Job_Management/', serCon='22250In[JOB190305185355]')
    #print(api.GET_Text)
    # print(uuid.uuid1())
    #api.CreateNewMeasurement(mes_data={'12':'Prismo'}, partPath='/Machine_List/')
    #api.CreateNewMeasurement(mes_data={'12':'Acura'}, partPath='/Machine_List/')
    #api.CreateNewMeasurement(mes_data={'12':'Contura'}, partPath='/Machine_List/')
