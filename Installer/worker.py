import requests
import sys
import os

password = os.environ['QSPASSWORD']

for fn in ['compute-shell.zip', 'onrack-shell.zip', 'site_manager_shell.zip', 'NFV Build Environment.zip']:
    print "Importing %s..." % fn
    token = requests.put('http://localhost:9000/Api/Auth/Login',
                         {"username": "admin", "password": password, "domain": "Global"}).text.strip().replace('"', '')
    fileobj = open(fn, 'rb')
    r = requests.post('http://localhost:9000/API/Package/ImportPackage', headers={"Authorization": "Basic " + token},
                      files={"file": fileobj})
    fileobj.close()
