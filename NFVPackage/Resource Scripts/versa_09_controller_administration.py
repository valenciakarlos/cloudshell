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
versa_controller_ip = attrs['Versa Controller NB IP']
controller_lan_ip_subnet = attrs['Versa Controller LAN Subnet']
versa_provider_org = attrs['Versa Provider Name']
controller_wan_ip = attrs['Versa Controller WAN IP']
controlller_lan_ip = attrs['Versa Controller LAN IP']
provider_mgmt_ike = attrs['Versa Provider MGMT IKE']
provider_mgmt_ike_subnet = attrs['Versa Provider MGMT IKE Subnet']
tnt_mgmt_ike = attrs['Versa TNT MGMT IKE']
tnt_mgmt_ike_subnet = attrs['Versa TNT MGMT IKE Subnet']
provider_mgmt_ipsec = attrs['Versa Provider MGMT IPSec']
provider_mgmt_ipsec_subnet = attrs['Versa Provider MGMT IPSec Subnet']
tnt_mgmt_ipsec = attrs['Versa TNT MGMT IPSec']
tnt_mgmt_ipsec_subnet = attrs['Versa TNT MGMT IPSec Subnet']
staging_ipsec = attrs['Versa Staging IPSec']
bgp_client_nw = attrs['Versa BGP Client NW']
versa_customer_org = attrs['Versa Customer Name']

#Get Controller uuid
try:
    controller_uuid = rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/provider/appliances/appliance?format=json&select=name;uuid&filters=jsonpath{$.appliance[?(@.name==%27'''+ versa_controller_name + '''%27)]}''', versa_username, versa_password, 'get', '', is_body_json=True, return_xml=True)
except Exception as e:
    print e

controller_uuid = json.loads(controller_uuid)
controller_uuid = controller_uuid['appliance'][0]['uuid']





#Get Customer uuid
try:
    customer_uuid = rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/provider/organizations/organization?format=json&select=name;uuid;parent-org;subscription-plan&filters=jsonpath{$.organization[?(@.parent-org==%27''' +versa_provider_org + '''%27)]}''', versa_username, versa_password, 'get', '', is_body_json=True, return_xml=True)
except Exception as e:
    print e

customer_uuid = json.loads(customer_uuid)
customer_uuid = customer_uuid['organization'][0]['uuid']



#Associate controller to customer 
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/actions/_operations/associate-organization-to-appliance''', versa_username, versa_password, 'post', '{"associate-organization-to-appliance":{"orguuid":"''' + customer_uuid + '''","networking-info":{"network-info":[]},"available-service-node-groups":["default-sng"],"services":["sdwan"],"applianceuuid":"''' + controller_uuid + '"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e



#time.sleep(500)
#edit WAN interface
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/interfaces/vni/''', versa_username, versa_password, 'patch', '''{
"vni":
{
    "name":"vni-0/1",
    "description":"Internet Facing - to SDWAN Branches",
    "enable":true,
    "unit":[
        {"name":"0",
         "family":
             {"inet":
                 {"address":[
                     {"addr":
                          "''' + controller_wan_ip + '''"
                      }]
                 }
             },
         "enable":true
         }],
    "promiscuous":false
}}
''', is_body_json=True, return_xml=True)
except Exception as e:
    print e



#edit LAN interface
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/interfaces/vni/''', versa_username, versa_password, 'patch', '''
{
    "vni": [
        {
            "name": "vni-0/0",
            "description": "Prov Mgmt Facing - to VD & VA",
            "enable":true,
            "unit":[
                {"name":"0",
                 "family":
                     {"inet":
                         {"address":[
                             {"addr":
                                  "''' + controlller_lan_ip + controller_lan_ip_subnet + '''"
                              }]
                         }
                     },
                 "enable":true
                 }],
            "promiscuous":false
        }
    ]
}
''', is_body_json=True, return_xml=True)
except Exception as e:
    print e





#Create WAN_NW
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/networks''', versa_username, versa_password, 'post', '{"network":{"name":"WAN-NW","interfaces":["vni-0/1.0"]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Create LAN_NW
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/networks''', versa_username, versa_password, 'post', '{"network":{"name":"Prov-Mgmt-NW","interfaces":["vni-0/0.0"]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Create IKEI tvi ProdMgmt
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/interfaces''', versa_username, versa_password, 'post', '{"tvi":{"enable":true,"mtu":"1400","mode":"ipsec","type":"p2mp-vxlan","unit":[{"name":"0","description":"Prov Mgmt IKE Interface","family":{"inet":{"address":[{"addr":"' + provider_mgmt_ike + provider_mgmt_ike_subnet + '"}]}},"enable":true}],"name":"tvi-0/1"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Create IKEI tvi TntMgmt
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/interfaces''', versa_username, versa_password, 'post', '{"tvi":{"enable":true,"mtu":"1400","mode":"ipsec","type":"p2mp-vxlan","unit":[{"name":"0","description":"Tenant Mgmt IKE Interface","family":{"inet":{"address":[{"addr":"' + tnt_mgmt_ike + tnt_mgmt_ike_subnet + '"}]}},"enable":true}],"name":"tvi-0/5"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#Create IPSec tvi - ProvMgmt
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/interfaces''', versa_username, versa_password, 'post', '{"tvi":{"enable":true,"mtu":"1400","mode":"ipsec","type":"p2mp-esp","unit":[{"name":"0","description":"Prov Mgmt IPSec Interface","family":{"inet":{"address":[{"addr":"' + provider_mgmt_ipsec + provider_mgmt_ipsec_subnet + '"}]}},"enable":true}],"name":"tvi-0/2"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#Create IPSec tvi - TntMgmt
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/interfaces''', versa_username, versa_password, 'post', '{"tvi":{"enable":true,"mtu":"1400","mode":"ipsec","type":"p2mp-esp","unit":[{"name":"0","description":"Tenant Mgmt IPSec Interface","family":{"inet":{"address":[{"addr":"' + tnt_mgmt_ipsec + tnt_mgmt_ipsec_subnet + '"}]}},"enable":true}],"name":"tvi-0/6"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Create IPSec tvi - staging
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/interfaces''', versa_username, versa_password, 'post', '{"tvi":{"enable":true,"mtu":"1400","mode":"ipsec","type":"ipsec","unit":[{"name":"0","description":"Staging IPSec Interface","family":{"inet":{"address":[{"addr":"' + staging_ipsec + '"}]}},"enable":true}],"name":"tvi-0/3"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Create Global-VR RI
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/routing-instances''', versa_username, versa_password, 'post', '{"routing-instance":[{"name":"Global-VR","instance-type":"virtual-router","networks":["WAN-NW"]}]}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Create provider-Mgmt RI
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/routing-instances''', versa_username, versa_password, 'post', '{"routing-instance":{"name":"Prov-Mgmt-VR","instance-type":"virtual-router","networks":["Prov-Mgmt-NW"],"description":"Provider Mgmt Routing Instance","interfaces":["tvi-0/1.0","tvi-0/2.0","tvi-0/3.0"],"usage-type":"sdwan-management","routing-options":{"static":{"route":{"rti-static-route-list":[{"ip-prefix":"0.0.0.0/0","next-hop":"' + controlller_lan_ip + '","preference":"1","interface":"vni-0/0.0"}]}}}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e
                                                                                                                                                                                            
#Create Customer Mgmt RI
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/routing-instances''', versa_username, versa_password, 'post', '{"routing-instance":[{"name":"Cust-Mgmt-VR","instance-type":"virtual-router","mpls-vpn-core":[null],"interfaces":["tvi-0/5.0","tvi-0/6.0"],"routing-options":{"static":{"route":{"rti-static-route-list":[{"ip-prefix":"0.0.0.0/0","next-hop":"' + tnt_mgmt_ipsec + '","preference":"1","interface":"tvi-0/6.0","tag":"0"}]}},"rti-mpls-vpn-local-router-address":"' + tnt_mgmt_ipsec + '"},"protocols":{"bgp":{"rti-bgp":[{"instance-id":"1","router-id":"' + tnt_mgmt_ipsec + '","cluster-id":"0.0.0.0","local-as":{"as-number":"1000"},"ibgp-preference":"200","ebgp-preference":"20","hold-time":"90","graceful-restart":{"enable":[null],"maximum-restart-time":"120","purge-time":"120","recovery-time":"120","stalepath-time":"120"},"route-flap":{"free-max-time":"180","reuse-max-time":"60","reuse-size":"256","reuse-array-size":"1024"},"group":[{"name":"Branches","type":"internal","peer-as":"1000","local-address":"' + tnt_mgmt_ipsec + '","family":{"inet":{"versa-private":{"loops":null,"prefix-limit":null}},"inet-vpn":{"unicast":{"loops":null,"prefix-limit":null}}},"route-reflector-client":[null],"allow":[{"address-mask":"' + bgp_client_nw + '"}]}]}]}}}]}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

quali_exit(__file__)