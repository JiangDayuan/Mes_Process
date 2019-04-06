import shutil
import os
from subprocess import run
import time
import getpass
import threading
import multiprocessing
from collections import Counter
import datetime

s = '2017-12-25'
d = datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
print(d)