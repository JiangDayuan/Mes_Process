import qflow

a = qflow.system_config()
with open('record.txt', 'w') as r:
    r.write(a.parent_dir)