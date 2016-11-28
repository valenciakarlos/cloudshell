import json
import os

from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from cloudshell.api.cloudshell_api import InputNameValue
import requests
import shutil

csapi = helpers.get_api_session()
resid = helpers.get_reservation_context_details().id

logdir = r'c:\ProgramData\QualiSystems\Logs\%s' % resid

zipname = r'%s\%s' % (os.environ['TEMP'], 'logs.zip')

shutil.make_archive(zipname.replace('.zip', ''), 'zip', logdir)

zipdata = None
with open(zipname, 'rb') as f:
    zipdata = f.read()

# print zipname
os.remove(zipname)

con_details = helpers.get_connectivity_context_details()
env_details = helpers.get_reservation_context_details()
token1 = json.loads(os.environ['QUALICONNECTIVITYCONTEXT'])['adminAuthToken']
# print token1
# pw = con_details.admin_pass
# print pw
# pw = csapi.DecryptPassword(con_details.admin_pass).Value
# print pw
# pw = 'admin'

token2 = requests.put('http://%s:%d/API/Auth/Login' % (con_details.server_address, 9000),
                      headers={'Content-Type': 'application/x-www-form-urlencoded'},
                      # data='username=%s&password=%s&domain=%s' % (con_details.admin_user, pw, env_details.domain)
                        data='token=%s&domain=%s' % (token1, env_details.domain)
                      ).content

if token2.startswith('"') and token2.endswith('"'):
    token2 = token2[1:-1]

j = requests.post('http://%s:%s/Api/Package/AttachFileToReservation' % (con_details.server_address, 9000),
                  headers={
                      'Authorization': 'Basic ' + token2,
                  },
                  files={
                      'QualiPackage': ('QualiPackage', zipdata),
                      'reservationId': ('reservationId', env_details.id),
                      'saveFileAs': ('saveFileAs', 'logs.zip'),
                      'overwriteIfExists': ('overwriteIfExists', 'True'),
                  })
print j.status_code
print j.text
print 'logs.zip has been attached to the reservation.\n\nReload the page and click the paperclip icon to download the file.'
