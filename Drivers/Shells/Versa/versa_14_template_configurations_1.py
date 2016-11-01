from quali_remote import *
import os
import json
import time

from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

versa_dir_ip = attrs['Versa Director NB IP']
versa_username = attrs['Versa Username']
versa_password = attrs['Versa Password']
versa_controller_name = attrs['Versa Controller Name']
versa_provider_org = attrs['Versa Provider Name']
versa_customer_org = attrs['Versa Customer Name']
versa_director_sb_ip = attrs['Versa Director SB IP']

#Create WAN Interface
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-Staging/config/interfaces''', versa_username, versa_password, 'post', '{"vni":{"name":"vni-0/0","description":"WAN interface","enable":true,"unit":[{"name":"0","family":{"inet":{"address":[{"addr":"{$v_vni-0-0_-_Unit_0_Static_address}"}]}},"enable":true}],"promiscuous":false}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#Create Tunnle Interface
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-Staging/config/interfaces''', versa_username, versa_password, 'post', '{"tvi":{"enable":true,"mtu":"1400","mode":"ipsec","type":"ipsec","unit":[{"name":"0","family":{},"enable":true}],"name":"tvi-0/3"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#Create WAN NW
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-Staging/config/networks''', versa_username, versa_password, 'post', '{"network":{"name":"WAN-NW","interfaces":["vni-0/0.0"]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Create Global-VR
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-Staging/config/routing-instances''', versa_username, versa_password, 'post', '{"routing-instance":{"name":"Global-VR","instance-type":"virtual-router","networks":["WAN-NW"],"routing-options":{"static":{"route":{"rti-static-route-list":[{"ip-prefix":"0.0.0.0/0","next-hop":"{$v_Global-VR_Next_Hop_address-0}","preference":"1","interface":"vni-0/0.0"}]}}}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Create Provider MGMR RI
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-Staging/config/routing-instances''', versa_username, versa_password, 'post', '{"routing-instance":[{"name":"Prov-Mgmt-RI","instance-type":"virtual-router","interfaces":["tvi-0/3.0"]}]}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#Get Provider uuid
try:
    provider_uuid = rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/provider/organizations/organization?format=json&select=name;uuid;parent-org;subscription-plan&filters=jsonpath{$.organization[?(@.parent-org==%27none%27)]}''', versa_username, versa_password, 'get', '', is_body_json=True, return_xml=True)
except Exception as e:
    print e

provider_uuid = json.loads(provider_uuid)
provider_uuid = provider_uuid['organization'][0]['uuid']

#Update traffic identification
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-Staging/config/orgs/org/''' + versa_provider_org, versa_username, versa_password, 'put', '<org><name>' + versa_provider_org + '</name><uuid>' + provider_uuid + '</uuid><traffic-identification><using>tvi-0&#x2F;3.0</using><using-networks>WAN-NW</using-networks></traffic-identification><available-routing-instances>Prov-Mgmt-RI</available-routing-instances><available-routing-instances>Global-VR</available-routing-instances><sd-wan xmlns="http://www.versa-networks.com/sdwan"></sd-wan><available-service-node-groups xmlns="http://www.versa-networks.com/sng">default-sng</available-service-node-groups></org>', is_body_json=False, return_xml=True)
except Exception as e:
    print e


#Update system parameters
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-Staging/config/system/services//''', versa_username, versa_password, 'put', '{"services":{"sftp":"disabled","ssh":"enabled"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Create VNF Manager
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-Staging/config/system/vnf-manager''', versa_username, versa_password, 'put', '{"vnf-manager":{"ip-addresses":["' + versa_director_sb_ip + '/32"],"vnf-mgmt-interfaces":["tvi-0/3.0"]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

quali_exit(__file__)