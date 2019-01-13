import codecs
from os import path
import csv
import sys

#import tkinter
#from tkinter import ttk


class piwebconfig():
    MAX_ATTRIBUTE = 30
    def __init__(self, file_dir, pi_txt, example='example.msel'):
        self.example = path.join(file_dir, example)
        self.search = path.join(file_dir, 'search.msel')
        self.txt = path.join(file_dir, pi_txt)
    
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

    def csv_generate(self, target_dir, csv_data=None, ctl_info=None):
        """
        创建CSV文件
        (1)输入: The directory of config file which store the failure_path ,server_path and backup_path.
        (2)Format of config file:   failure_path=<directory>
                                    server_path=<directory>
                                    backup_path=<directory>
        (3)输出: 3 PATHS in failure_path ,server_path and backup_path as string
        """
        #如果没有输入就读取创建实例时选择的文件来生成csv_data字典
        process_status = None
        if csv_data==None:
            csv_data = self.piweb_txt_parser()
        #如果文件中存在‘Serial_Number’,则使用序列号作为csv的文件名
        if 'Serial_Number' in csv_data.keys():
            csv_name = csv_data['Serial_Number']+'.csv'
            #为了获取统一配置，设置足够多的Measurement Attribute,不足的数量填入空值
            empty_number = self.MAX_ATTRIBUTE - len(csv_data)
            #将txt或para文件的内容转换成csv的格式
            with open(path.join(target_dir, csv_name), 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for key, value in csv_data.items():
                    writer.writerow([key,value])
                #如果Measurement Attribute数量不足，则自动补充
                if empty_number > 0:
                    for i in range(empty_number):
                        writer.writerow(['Empty', 'None'])
                #添加Measurement Value Attribute
                writer.writerow(['Mes_Info', 0])
                #添加储存探针信息的Measurement Value Attribute
                if ctl_info != None:
                    for key, value in ctl_info.items():
                        if key != "fixture":
                            writer.writerow(["Probe_Info", key, value[2]])
        else:
            process_status = "模板中输出的信息缺失，请联系管理员或重新安装模板"
        return process_status


class system_config():
    CONFIG = 'directory.config'
    PARENT_FOLDER = 'Documents'#'Contract_Measurement_Process'
    def __init__(self):
        self.system_dir()
        self.config_dir = path.join(self.exe_dir, self.CONFIG)
        #self.config_path_reader()

    def system_dir(self):
        paths = sys.path[0]
        self.exe_dir = paths
        self.para_dir = path.join(paths, 'temp')
        self.rela_dir = path.join(paths, 'relative_files')
        while path.split(paths)[1] != self.PARENT_FOLDER:
            paths = path.split(paths)[0]
        self.parent_dir = paths

    def config_path_reader(self):
        """
        (1)Input: The directory of config file which store the failure_path ,server_path and backup_path.
        (2)Format of config file:   failure_path=<directory>
                                    server_path=<directory>
                                    backup_path=<directory>
        (3)Return: 3 PATHS in failure_path ,server_path and backup_path as string
        """
        with open(self.config_dir, 'r') as con:
            failure_path = con.readline().strip().split('=')[1]
            server_path = con.readline().strip().split('=')[1]
            backup_path = con.readline().strip().split('=')[1]
        return failure_path, server_path, backup_path

def msel_change():
    msel_para_dir = ''
    msel_gen = piwebconfig(msel_para_dir, 'criteria.para')
    msel_gen.msel()

def assignment_data():
    assignment = piwebconfig('', 'assignment.para')
    assignment.csv_generate('')
        
if __name__ == "__main__":
    pass
    #a = system_config()
    #with open('record.txt', 'w') as r:
    #    r.write(a.parent_dir)