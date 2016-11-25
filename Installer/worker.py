import requests
import sys
import os

password = os.environ['QSPASSWORD']

zips = [
    'compute-shell.zip',
    'onrack-shell.zip',
    'site_manager_shell.zip',
    'NFV Build Environment.zip'
]
for fn in zips:
    print "Importing %s..." % fn
    token = requests.put('http://localhost:9000/Api/Auth/Login',
                         {"username": "admin", "password": password, "domain": "Global"}).text.strip().replace('"', '')
    fileobj = open(fn, 'rb')
    r = requests.post('http://localhost:9000/API/Package/ImportPackage', headers={"Authorization": "Basic " + token},
                      files={"file": fileobj})
    fileobj.close()

import os

logdir = r'c:\program files (x86)\qualisystems\cloudshell\server\packaging logs'
logs = os.listdir(logdir)

logs.sort(key=lambda x: os.stat(os.path.join(logdir, x)).st_mtime)

for log in logs[-len(zips):]:
    if 'failed' in log.lower():
        print 'Package import failed, check %s' % os.path.join(logdir, log)