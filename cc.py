import shutil
import os

source = r'C:\Users\Public\Documents\Zeiss\CALYPSO\workarea\inspections\Data_Compress'
target = r'C:\Users\ZCFJIAN1\Desktop\target\asbder'
shutil.copytree(source, target)
#print(os.path.samefile(source, target))
