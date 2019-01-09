import codecs
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

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


if __name__ == "__main__":
    msel_change()