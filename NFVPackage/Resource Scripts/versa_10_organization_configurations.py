from quali_remote import *
import os
import json
import time
from xml.dom.minidom import parseString
from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

versa_dir_ip = attrs['Versa Director NB IP']
versa_username = attrs['Versa Username']
versa_password = attrs['Versa Password']
versa_controller_name = attrs['Versa Controller Name']
versa_controller_ip = attrs['Versa Controller NB IP']
versa_provider_org = attrs['Versa Provider Name']
vnf_mgr_ip = attrs['Versa Director SB IP'] + '/32'
versa_customer_org = attrs['Versa Customer Name']

#Create Sites Provider
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/'''+ versa_controller_name + '''/config/orgs/org/''' + versa_provider_org + '''/sd-wan/site/''', versa_username, versa_password, 'put', '{"site":{"site-name":"Controller","site-type":"controller","site-id":"1","chassis-id":"Controller","global-tenant-id":"1","management-routing-instance":"Prov-Mgmt-VR","wan-interfaces":{"vni":[{"name":"vni-0/1.0","encryption":"optional","circuit-name":"Internet-Link-1","shaping-rate":{}}]},"branch-vnf-manager":{"ip-addresses":["' + vnf_mgr_ip +'"]}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#Create Site Customer
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/'''+ versa_controller_name + '''/config/orgs/org/''' +  versa_customer_org + '''/sd-wan/site/''', versa_username, versa_password, 'put', '{"site":{"site-name":"Controller","site-type":"controller","site-id":"1","chassis-id":"Controller","global-tenant-id":"2","management-routing-instance":"Cust-Mgmt-VR","wan-interfaces":{"vni":[{"name":"vni-0/1.0","encryption":"optional","circuit-name":"Internet-Link-1","shaping-rate":{}}]},"branch-vnf-manager":{"ip-addresses":["' + vnf_mgr_ip + '"]}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Get Provider uuid
try:
    provider_uuid = rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/provider/organizations/organization?format=json&select=name;uuid;parent-org;subscription-plan&filters=jsonpath{$.organization[?(@.parent-org==%27none%27)]}''', versa_username, versa_password, 'get', '', is_body_json=True, return_xml=True)
except Exception as e:
    print e

provider_uuid = json.loads(provider_uuid)
provider_uuid = provider_uuid['organization'][0]['uuid']



#Traffic - Provider
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/'''+ versa_controller_name + '''/config/orgs/org/''' + versa_provider_org, versa_username, versa_password, 'put', '<org><name>' + versa_provider_org + '</name><uuid>' + provider_uuid + '</uuid><appliance-owner></appliance-owner><options><session-limit>1000000</session-limit></options><traffic-identification><using>tvi-0&#x2F;1.0</using><using>tvi-0&#x2F;2.0</using><using>tvi-0&#x2F;3.0</using><using-networks>Prov-Mgmt-NW</using-networks><using-networks>WAN-NW</using-networks></traffic-identification><available-routing-instances>Cust-Mgmt-VR</available-routing-instances><available-routing-instances>Global-VR</available-routing-instances><available-routing-instances>Prov-Mgmt-VR</available-routing-instances><sd-wan xmlns="http://www.versa-networks.com/sdwan"><site><site-type>controller</site-type><global-tenant-id>1</global-tenant-id><site-name>Controller</site-name><chassis-id>Controller</chassis-id><site-id>1</site-id><management-routing-instance>Prov-Mgmt-VR</management-routing-instance><wan-interfaces><vni><name>vni-0&#x2F;1.0</name><circuit-name>Internet-Link-1</circuit-name><shaping-rate/><encryption>optional</encryption></vni></wan-interfaces><branch-vnf-manager><ip-addresses>' + vnf_mgr_ip + '</ip-addresses></branch-vnf-manager><statistics/></site></sd-wan><available-service-node-groups xmlns="http://www.versa-networks.com/sng">default-sng</available-service-node-groups></org>', is_body_json=False, return_xml=True)
except Exception as e:
    print e


#Get Customer uuid
try:
    customer_uuid = rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/provider/organizations/organization?format=json&select=name;uuid;parent-org;subscription-plan&filters=jsonpath{$.organization[?(@.parent-org==%27''' +versa_provider_org + '''%27)]}''', versa_username, versa_password, 'get', '', is_body_json=True, return_xml=True)
except Exception as e:
    print e

customer_uuid = json.loads(customer_uuid)
customer_uuid = customer_uuid['organization'][0]['uuid']


#Traffic - Customer
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/'''+ versa_controller_name + '''/config/orgs/org/''' + versa_customer_org, versa_username, versa_password, 'put', '<org><name>' + versa_customer_org + '</name><uuid>' + customer_uuid + '</uuid><services>sdwan</services><options><session-limit>1000000</session-limit></options><traffic-identification><using>tvi-0&#x2F;5.0</using><using>tvi-0&#x2F;6.0</using></traffic-identification><available-routing-instances>Prov-Mgmt-VR</available-routing-instances><available-routing-instances>Cust-Mgmt-VR</available-routing-instances><available-routing-instances>Global-VR</available-routing-instances><sd-wan xmlns="http://www.versa-networks.com/sdwan"><site><site-type>controller</site-type><global-tenant-id>2</global-tenant-id><site-name>Controller</site-name><chassis-id>Controller</chassis-id><site-id>1</site-id><management-routing-instance>Cust-Mgmt-VR</management-routing-instance><wan-interfaces><vni><name>vni-0&#x2F;1.0</name><circuit-name>Internet-Link-1</circuit-name><shaping-rate/><encryption>optional</encryption></vni></wan-interfaces><branch-vnf-manager><ip-addresses>' + vnf_mgr_ip + '</ip-addresses></branch-vnf-manager><statistics/></site></sd-wan><available-service-node-groups xmlns="http://www.versa-networks.com/sng">default-sng</available-service-node-groups></org>', is_body_json=False, return_xml=True)
except Exception as e:
    print e

quali_exit(__file__)