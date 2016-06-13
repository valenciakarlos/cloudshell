from quali_remote import *
import os
import json
import time
from xml.dom.minidom import parseString


with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

versa_dir_ip = attrs['Versa Director NB IP']
versa_username = attrs['Versa Username']
versa_password = attrs['Versa Password']
versa_controller_name = attrs['Versa Controller Name']
versa_controller_ip = attrs['Versa Controller NB IP']
cms_uuid = attrs['Versa CMS UUID']
versa_provider_org = attrs['Versa Provider Name']


#Create controller
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/cms/local/instances''', versa_username, versa_password, 'post', '''{"instance":{"name":"''' + versa_controller_name + '''","ip-address":"''' + versa_controller_ip + '''"}}''', is_body_json=True)
except Exception as e:
    print e
res_net = ''
res_org = ''
#Get info from Director
try:
    res_org = rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/cms/local/organizations/organization?select=name;uuid''', versa_username, versa_password, 'get', '', True, True)

except Exception as e:
    print e

#Get uuid
xml_res = parseString(res_org)
for node in xml_res.getElementsByTagName('uuid'):
    res_uuid = node.toxml().replace('<uuid>', '').replace('</uuid>', '')


#Get network info
try:
    res_net = rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/cms/local/organizations/organization/''' + res_uuid + '''/org-networks/org-network/''', versa_username, versa_password, 'get', '', False, True)
except Exception as e:
    print e
net_uuid = []
net_name = []
xml_res = parseString(res_net)
for uuid in (xml_res.getElementsByTagName('uuid')):
    net_uuid.append(uuid.toxml().replace('<uuid>', '').replace('</uuid>', ''))
#print net_uuid
for name in (xml_res.getElementsByTagName('name')):
    net_name.append(name.toxml().replace('<name>', '').replace('</name>', ''))
#print net_name


try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/cms/local/organizations/organization/''' + cms_uuid, versa_username, versa_password, 'put', '''{"organization":{"uuid":"''' + cms_uuid + '''","name":"SDWAN-CMS-ORG","org-networks":{"org-network":[{"uuid":"''' + net_uuid[0] + '''","name":"''' + net_name[0] + '''","ipaddress-allocation-mode":"manual"},{"uuid":"''' + net_uuid[1] + '''","name":"''' + net_name[1] + '''","ipaddress-allocation-mode":"manual"},{"uuid":"''' + net_uuid[2] + '''","name":"''' + net_name[2] + '''","ipaddress-allocation-mode":"manual"}]},"resource-pool":{"instances":["default","''' + versa_controller_name + '''"]}}}''', is_body_json=True)
except Exception as e:
    print e

#get Provider uuid
parent_uuid = rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/provider/organizations/organization?format=json&select=name;uuid;parent-org;subscription-plan&filters=jsonpath{$.organization[?(@.parent-org==%27none%27)]}''', versa_username, versa_password, 'get','', is_body_json=True)
_parent_uuid = json.loads(parent_uuid)
provider_uuid =  _parent_uuid['organization'][0]['uuid']
#print provider_uuid


#Create Controller
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/actions/_operations/add-devices''', versa_username, versa_password, 'post', '''<add-devices><devices><device><mgmt-ip>''' + versa_controller_ip + '''</mgmt-ip><name>''' + versa_controller_name + '''</name><org>''' + provider_uuid + '''</org><cmsorg>''' + cms_uuid + '''</cmsorg><type>controller</type><networking-info><network-info><network-name>''' + net_name[0] + '''</network-name><interface>vni-0/0</interface></network-info><network-info><network-name>''' + net_name[1] + '''</network-name><interface>vni-0/1</interface></network-info></networking-info><snglist><sng><name>Default_All_Services</name><isPartOfVCSN>true</isPartOfVCSN><services>sdwan</services></sng></snglist></device></devices></add-devices>''')
except Exception as e:
    print e