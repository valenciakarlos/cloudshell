from quali_remote import *
import os
import json
import time
import re

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

versa_dir_ip = attrs['Versa Director NB IP']
versa_username = attrs['Versa Username']
versa_password = attrs['Versa Password']
versa_controller_name = attrs['Versa Controller Name']
versa_provider_org = attrs['Versa Provider Name']
versa_customer_org = attrs['Versa Customer Name']
bracnh1_name = attrs['Versa Branch1 VM Name']
bracnh2_name = attrs['Versa Branch2 VM Name']
controller_sdwan_ip = attrs['Versa Controller SDWAN IP']
versa_branch_client_gateway = attrs['Versa Branch Client Gateway']
versa_branch_server_gateway = attrs['Versa Branch Server Gateway']
versa_branch_client_subnet = attrs['Versa Branch Client Subnet']
versa_branch_server_subnet = attrs['Versa Branch Server Subnet']
versa_branch1_sdwan_ip = attrs['Versa Branch1 SDWAN IP']
versa_branch2_sdwan_ip = attrs['Versa Branch2 SDWAN IP']
versa_branch1_sdwan_subnet = attrs['Versa Branch1 SDWAN Subnet']
versa_branch2_sdwan_subnet = attrs['Versa Branch2 SDWAN Subnet']
versa_sb_network = attrs['Versa SB Network']
versa_sb_subnet = attrs['Versa SB Subnet']
versa_analytics_sb_ip = attrs['Versa Analytics SB IP']
versa_director_sb_ip = attrs['Versa Director SB IP']
versa_prov_mgmt_ipsec = attrs['Versa Provider MGMT IPSec']
versa_tnt_mgmt_ipsec = attrs['Versa TNT MGMT IPSec']
versa_prov_mgmt_ike = attrs['Versa Provider MGMT IKE']
versa_tnt_mgmt_ike = attrs['Versa TNT MGMT IKE']
versa_branch1_tvi2_ip = attrs['Versa Branch1 TVI2 IP']
versa_branch2_tvi2_ip = attrs['Versa Branch2 TVI2 IP']
versa_branch1_tvi2_subnet = attrs['Versa Branch1 TVI2 IP Subnet']
versa_branch2_tvi2_subnet = attrs['Versa Branch2 TVI2 IP Subnet']
versa_branch1_tvi4_ip = attrs['Versa Branch1 TVI4 IP']
versa_branch1_tvi4_subnet = attrs['Versa Branch1 TVI4 IP Subnet']
versa_branch2_tvi4_ip = attrs['Versa Branch2 TVI4 IP']
versa_branch2_tvi4_subnet = attrs['Versa Branch2 TVI4 IP Subnet']
versa_branch1_tvi5_ip = attrs['Versa Branch1 TVI5 IP']
versa_branch1_tvi5_subnet = attrs['Versa Branch1 TVI5 IP Subnet']
versa_branch2_tvi5_ip = attrs['Versa Branch2 TVI5 IP']
versa_branch2_tvi5_subnet = attrs['Versa Branch2 TVI5 IP Subnet']
versa_branch1_tvi1_ip = attrs['Versa Branch1 TVI1 IP']
versa_branch1_tvi1_subnet = attrs['Versa Branch1 TVI1 IP Subnet']
versa_branch2_tvi1_ip = attrs['Versa Branch2 TVI1 IP']
versa_branch2_tvi1_subnet = attrs['Versa Branch2 TVI1 IP Subnet']
br1_ipsec_id = attrs['Versa Branch1 PreStaging IPSec ID']
br2_ipsec_id = attrs['Versa Branch2 PreStaging IPSec ID']
provider_ipsec_id = attrs['Versa Provider PreStaging IPSec ID']
prestaging_key = attrs['Versa Branch PreStaging IPSec Key']
br1_staging_ipsec_id = attrs['Versa Branch1 Staging IPSec ID']
br2_staging_ipsec_id = attrs['Versa Branch2 Staging IPSec ID']
provider_staging_ipsec_id = attrs['Versa Provider Staging IPSec ID']
staging_key = attrs['Versa Branch Staging IPSec Key']
br1_poststaging_ipsec_id = attrs['Versa Branch1 PostStaging IPSec ID']
br2_poststaging_ipsec_id = attrs['Versa Branch2 PostStaging IPSec ID']
provider_poststaging_ipsec_id = attrs['Versa Provider PostStaging IPSec ID']
poststaging_key = attrs['Versa Branch PostStaging IPSec Key']
analytics_log_port = attrs['Versa Analytics Logs Port']
br1_chas = attrs['Versa Branch1 Serial']
br2_chas = attrs['Versa Branch2 Serial']
br1_number = re.sub(r"\D", "", br1_chas)
br2_number = re.sub(r"\D", "", br2_chas)
br1_location = attrs['Versa Branch1 Location']
br2_location = attrs['Versa Branch2 Location']
br1_long = attrs['Versa Branch1 Longitude']
br1_lat = attrs['Versa Branch1 Latitude']
br2_long = attrs['Versa Branch2 Longitude']
br2_lat = attrs['Versa Branch2 Latitude']

#staging - Update Site Info
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-Staging/config/orgs/org/''' + versa_provider_org + '''/sd-wan/site/''', versa_username, versa_password, 'put', '{"site":{"site-name":"{$v_Provider_Site_Name}","site-type":"branch-poststaging","chassis-id":"{$v_Provider_Chassis_ID}","global-tenant-id":"1","management-routing-instance":"Prov-Mgmt-RI","wan-interfaces":{"vni":[{"name":"vni-0/0.0","encryption":"optional","circuit-name":"Internet","circuit-type":"Broadband","circuit-media":"DSL","shaping-rate":{}}]}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#staging - Update Controller Info
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-Staging/config/orgs/org/'''  + versa_provider_org + '''/sd-wan/controllers''', versa_username, versa_password, 'post', '{"controller":{"name":"Controller","site-name":"Controller","site-id":"1","transport-addresses":{"transport-address":[{"name":"Controller-WAN-IP","ip-address":"{$v_Provider_Controller-Controller-WAN-IP_Transport_IP}","routing-instance":"Global-VR"}]},"management-addresses":{"management-address":[]}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#staging - IPSec Prof
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-Staging/config/orgs/org-services/''' + versa_provider_org + '''/ipsec''', versa_username, versa_password, 'post', '{"vpn-profile":{"name":"Staging-IPSec","vpn-type":"branch-staging-sdwan","tunnel-initiate":"automatic","routing-instance":"Global-VR","tunnel-routing-instance":"Prov-Mgmt-RI","tunnel-interface":"tvi-0/3.0","remote-auth-type":"psk","local-auth-info":{"auth-type":"psk","id-type":"email","key":"' + prestaging_key + '","id-string":"{$v_Provider_Staging-IPSec_Local_auth_email_identifier}"},"peer-auth-info":{"auth-type":"psk","id-type":"email","key":"' + prestaging_key + '","id-string":"' + provider_ipsec_id + '"},"ipsec":{"life":{"duration":28800}},"ike":{"group":"mod1","lifetime":"28800","dpd-timeout":"30"},"local":{"inet":"{$v_Provider_Staging-IPSec_Local_IP}"},"peer":{"inet":"' + controller_sdwan_ip + '"}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#staging - VariableValue Branch2
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/device-template-variable/''' + bracnh2_name + ''',Branches-Staging''', versa_username, versa_password, 'put', '{"device-template-variable":{"device":"' + bracnh2_name + '","serial-number":"' + br2_chas + '","template":"Branches-Staging","variable-binding":{"attrs":[{"name":"{$v_Provider_Staging-IPSec_Local_IP}","value":"' + versa_branch2_sdwan_ip + '"},{"name":"{$v_Global-VR_Next_Hop_address-0}","value":"' + controller_sdwan_ip + '"},{"name":"{$v_Provider_Staging-IPSec_Local_auth_email_identifier}","value":"' + br2_ipsec_id + '"},{"name":"{$v_VNF_IP_Address-Prefix}","value":"' + versa_director_sb_ip + '"},{"name":"{$v_vni-0-0_-_Unit_0_Static_address}","value":"' + versa_branch2_sdwan_ip + versa_branch2_sdwan_subnet + '"},{"name":"{$v_Prov-Mgmt_Next_Hop_address-0}","value":"' + versa_director_sb_ip + '"},{"name":"{$v_Provider_Chassis_ID}","value":"' + br2_chas + '"},{"name":"{$v_Provider_Controller-Controller-WAN-IP_Transport_IP}","value":"' + controller_sdwan_ip + '"},{"name":"{$v_Provider_Site_Name}","value":"' + bracnh2_name + '"}]}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#staging - VariableValue Branch1
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/device-template-variable/''' + bracnh1_name + ''',Branches-Staging''', versa_username, versa_password, 'put', '{"device-template-variable":{"device":"' + bracnh1_name + '","serial-number":"' + br1_chas + '","template":"Branches-Staging","variable-binding":{"attrs":[{"name":"{$v_Provider_Staging-IPSec_Local_IP}","value":"' + versa_branch1_sdwan_ip + '"},{"name":"{$v_Global-VR_Next_Hop_address-0}","value":"' + controller_sdwan_ip + '"},{"name":"{$v_Provider_Staging-IPSec_Local_auth_email_identifier}","value":"' + br1_ipsec_id + '"},{"name":"{$v_VNF_IP_Address-Prefix}","value":"' + versa_director_sb_ip + '"},{"name":"{$v_vni-0-0_-_Unit_0_Static_address}","value":"' + versa_branch1_sdwan_ip + versa_branch1_sdwan_subnet + '"},{"name":"{$v_Prov-Mgmt_Next_Hop_address-0}","value":"' + versa_director_sb_ip + '"},{"name":"{$v_Provider_Chassis_ID}","value":"' + br1_chas + '"},{"name":"{$v_Provider_Controller-Controller-WAN-IP_Transport_IP}","value":"' + controller_sdwan_ip + '"},{"name":"{$v_Provider_Site_Name}","value":"' + bracnh1_name + '"}]}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Create WAN Interface
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/interfaces''', versa_username, versa_password, 'post', '{"vni":{"name":"vni-0/0","description":"WAN Interface","enable":true,"unit":[{"name":"0","family":{"inet":{"address":[{"addr":"{$v_vni-0-0_-_Unit_0_Static_address}"}]}},"enable":true}],"promiscuous":false}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#PostStagging - Create LAN Interface
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/interfaces''', versa_username, versa_password, 'post', '{"vni":{"name":"vni-0/1","description":"LAN Interface","enable":true,"unit":[{"name":"0","family":{"inet":{"address":[{"addr":"{$v_vni-0-1_-_Unit_0_Static_address}"}]}},"enable":true}],"promiscuous":false}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

###TODO  Already done??
#PostStagging - Create Tunnle Interfaces
#try:
#    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/interfaces''', versa_username, versa_password, 'post', '{"vni":{"name":"vni-0/1","description":"LAN Interface","enable":true,"unit":[{"name":"0","family":{"inet":{"address":[{"addr":"{$v_vni-0-1_-_Unit_0_Static_address}"}]}},"enable":true}],"promiscuous":false}}', is_body_json=True, return_xml=True)
#except Exception as e:
#    print e


#PostStagging - Create TVI VXVLAN Prov
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/interfaces''', versa_username, versa_password, 'post', '{"tvi":{"enable":true,"description":"VXLAN Interface for Prov-Mgmt","mtu":"1400","mode":"ipsec","type":"p2mp-vxlan","unit":[{"name":"0","family":{"inet":{"address":[{"addr":"{$v_tvi-0-1_-_Unit_0_Static_address}"}]}},"enable":true}],"name":"tvi-0/1"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e



#PostStagging - Create TVI VXVLAN Cust
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/interfaces''', versa_username, versa_password, 'post', '{"tvi":{"enable":true,"description":"VXLAN Interface for Cust-Mgmt","mtu":"1400","mode":"ipsec","type":"p2mp-vxlan","unit":[{"name":"0","family":{"inet":{"address":[{"addr":"{$v_tvi-0-4_-_Unit_0_Static_address}"}]}},"enable":true}],"name":"tvi-0/4"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Create TVI ESP Prov
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/interfaces''', versa_username, versa_password, 'post', '{"tvi":{"enable":true,"description":"ESP Interface for Prov-Mgmt","mtu":"1400","mode":"ipsec","type":"p2mp-esp","unit":[{"name":"0","family":{"inet":{"address":[{"addr":"{$v_tvi-0-2_-_Unit_0_Static_address}"}]}},"enable":true}],"name":"tvi-0/2"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Create TVI ESP Cust
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/interfaces''', versa_username, versa_password, 'post', '{"tvi":{"enable":true,"description":"ESP Interface for Cust-Mgmt","mtu":"1400","mode":"ipsec","type":"p2mp-esp","unit":[{"name":"0","family":{"inet":{"address":[{"addr":"{$v_tvi-0-5_-_Unit_0_Static_address}"}]}},"enable":true}],"name":"tvi-0/5"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Create PTVI Interfaces
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/interfaces''', versa_username, versa_password, 'post', '{"ptvi":[{"name":"ptvi1","parent-interface":"tvi-0/2.0","remote-address":"' + versa_prov_mgmt_ipsec + '"},{"name":"ptvi2","parent-interface":"tvi-0/5.0","remote-address":"' + versa_tnt_mgmt_ipsec + '"}]}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Create WAN NW
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/networks''', versa_username, versa_password, 'post', '{"network":{"name":"WAN-NW","interfaces":["vni-0/0.0"]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#PostStagging - Create LAN NW
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/networks''', versa_username, versa_password, 'post', '{"network":{"name":"LAN-NW","interfaces":["vni-0/1.0"]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - systemSetting VNFMgr
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/system/vnf-manager''', versa_username, versa_password, 'put', '{"vnf-manager":{"ip-addresses":["{$v_VNF_IP_Address-Prefix}"],"vnf-mgmt-interfaces":["tvi-0/2.0"]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

##TODO missing elemnts vnf-manager ## Chnaged: to "/identifaction"
#PostStagging - systemSetting Name
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/system/identification''', versa_username, versa_password, 'patch', '{"identification":{"name":"{$v_identification}","location":"{$v_location}","latitude":"{$v_latitude}","longitude":"{$v_longitude}"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#PostStagging - systemSetting SSH
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/system/services//''', versa_username, versa_password, 'put', '{"services":{"sftp":"disabled","ssh":"enabled"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

##TODO mismatch keypath ## Chnaged to "/session"
#PostStagging - systemSetting Session
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/system/session//''', versa_username, versa_password, 'put', '{"session":{"check-tcp-syn":false,"reevaluate-reverse-flow":false,"tcp-secure-reset":false,"tcp-send-reset":false,"tcp-adjust-mss":{"enable":true,"interface-types":"all","mss":"1300"}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - GlobalRI
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/routing-instances''', versa_username, versa_password, 'post', '{"routing-instance":[{"name":"Global-VR","instance-type":"virtual-router","networks":["WAN-NW"],"routing-options":{"static":{"route":{"rti-static-route-list":[{"ip-prefix":"0.0.0.0/0","next-hop":"{$v_Global-VR_Next_Hop_address-0}","preference":"1","interface":"vni-0/0.0"}]}}}}]}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

##TODO Malformed message ## Changed to accept": [null]"
#PostStagging - LAN VR
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/routing-instances''', versa_username, versa_password, 'post', '{"routing-instance":{"name":"LAN-VR","instance-type":"vrf","global-vrf-id":"10","description":"LAN Routing Instance","networks":["LAN-NW"],"route-distinguisher":"1L:2","vrf-both-target":"target:3L:4","mpls-vpn-core-instance":"Cust-Mgmt","policy-options":{"redistribution-policy":[{"name":"p1","term":[{"term-name":"t1","match":{"protocol":"direct"},"action":{"set-origin":"egp"}},{"term-name":"t2","match":{"protocol":"bgp"},"action":{"set-origin":"egp"}},{"term-name":"t3","match":{"protocol":"static"},"action":{"set-origin":"egp"}}]}],"redistribute-to-bgp":"p1"}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - ProvMgmt VR
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/routing-instances''', versa_username, versa_password, 'post', '{"routing-instance":[{"name":"Prov-Mgmt","instance-type":"virtual-router","usage-type":"sdwan-management","mpls-vpn-core":[null],"interfaces":["ptvi1","tvi-0/1.0","tvi-0/2.0"],"routing-options":{"static":{"route":{"rti-static-route-list":[{"ip-prefix":"{$v_Prov-Mgmt_Destination_address-0}","next-hop":"{$v_Prov-Mgmt_Next_Hop_address-0}","preference":"1","interface":"tvi-0/2.0","no-install":[null]},{"ip-prefix":"{$v_Prov-Mgmt_Destination_address-1}","next-hop":"{$v_Prov-Mgmt_Next_Hop_address-1}","preference":"1","interface":"ptvi1"}]}}}}]}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - CustMgmt VR
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/routing-instances''', versa_username, versa_password, 'post', '{"routing-instance":{"name":"Cust-Mgmt","instance-type":"virtual-router","interfaces":["ptvi2","tvi-0/4.0","tvi-0/5.0"],"mpls-vpn-core":[null],"routing-options":{"rti-mpls-vpn-local-router-address":"{$v_Cust-Mgmt_MPLS_Local_Router_address}","static":{"route":{"rti-static-route-list":[{"ip-prefix":"{$v_Cust-Mgmt_Destination_address-0}","next-hop":"{$v_Cust-Mgmt_Next_Hop_address-0}","preference":"1","interface":"tvi-0/5.0"}]}}},"protocols":{"bgp":{"rti-bgp":[{"instance-id":"1","router-id":"{$v_Cust-Mgmt_1_Router_ID-0}","cluster-id":"0.0.0.0","local-as":{"as-number":"1000"},"hold-time":"90","graceful-restart":{"enable":[null],"maximum-restart-time":"120","purge-time":"120","recovery-time":"120","stalepath-time":"120"},"route-flap":{"free-max-time":"180","reuse-max-time":"60","reuse-size":"256","reuse-array-size":"1024"},"group":[{"name":"versa","type":"internal","family":{"inet":{"versa-private":{"loops":null,"prefix-limit":null}},"inet-vpn":{"unicast":{"loops":null,"prefix-limit":null}}},"neighbor":[{"bgp-neighbor-ip":"{$v_Cust-Mgmt_1_versa_Neighbor_IP-0}","local-address":"{$v_Cust-Mgmt_1_versa_Neighbor_Local_IP-0}","peer-as":"1000"}]}]}]}}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Get Provider uuid
try:
    provider_uuid = rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/provider/organizations/organization?format=json&select=name;uuid;parent-org;subscription-plan&filters=jsonpath{$.organization[?(@.parent-org==%27none%27)]}''', versa_username, versa_password, 'get', '', is_body_json=True, return_xml=True)
except Exception as e:
    print e

provider_uuid = json.loads(provider_uuid)
provider_uuid = provider_uuid['organization'][0]['uuid']

##TODO Mismatch keypath ##Corrected Provider name
#PostStagging - ProvOrg Setting
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org/''' + versa_provider_org, versa_username, versa_password, 'put', '''<org><name>''' + versa_provider_org + '''</name><uuid>''' + provider_uuid + '''</uuid><traffic-identification><using>tvi-0&#x2F;1.0</using><using>tvi-0&#x2F;2.0</using><using>ptvi1</using><using-networks>WAN-NW</using-networks></traffic-identification><available-routing-instances>Prov-Mgmt</available-routing-instances><available-routing-instances>Global-VR</available-routing-instances><sd-wan xmlns="http://www.versa-networks.com/sdwan"></sd-wan><available-service-node-groups xmlns="http://www.versa-networks.com/sng">default-sng</available-service-node-groups></org>''', is_body_json=False, return_xml=True)
except Exception as e:
    print e

#Get Customer uuid
try:
    customer_uuid = rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/provider/organizations/organization?format=json&select=name;uuid;parent-org;subscription-plan&filters=jsonpath{$.organization[?(@.parent-org==%27''' +versa_provider_org + '''%27)]}''', versa_username, versa_password, 'get', '', is_body_json=True, return_xml=True)
except Exception as e:
    print e

customer_uuid = json.loads(customer_uuid)
customer_uuid = customer_uuid['organization'][0]['uuid']

#PostStagging - CustOrg Setting
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org/''' + versa_customer_org, versa_username, versa_password, 'put', '''<org><name>''' + versa_customer_org + '''</name><uuid>''' + customer_uuid + '''</uuid><traffic-identification><using>tvi-0&#x2F;4.0</using><using>tvi-0&#x2F;5.0</using><using>ptvi2</using><using-networks>LAN-NW</using-networks></traffic-identification><available-routing-instances>Global-VR</available-routing-instances><available-routing-instances>LAN-VR</available-routing-instances><available-routing-instances>Prov-Mgmt</available-routing-instances><available-routing-instances>Cust-Mgmt</available-routing-instances><sd-wan xmlns="http://www.versa-networks.com/sdwan"></sd-wan><available-service-node-groups xmlns="http://www.versa-networks.com/sng">default-sng</available-service-node-groups></org>''', is_body_json=False, return_xml=True)
except Exception as e:
    print e



#PostStagging - ProvOrg Site
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org/''' + versa_provider_org + '''/sd-wan/site/''', versa_username, versa_password, 'put', '''{"site":{"site-name":"{$v_Provider_Site_Name}","site-type":"branch","site-id":"{$v_Provider_Site_Id}","chassis-id":"{$v_Provider_Chassis_ID}","global-tenant-id":"1","management-routing-instance":"Prov-Mgmt","wan-interfaces":{"vni":[{"name":"vni-0/0.0","encryption":"optional","circuit-name":"Internet1","circuit-type":"Broadband","circuit-media":"DSL","shaping-rate":{}}]}}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e



#PostStagging - CustOrg Site
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org/''' + versa_customer_org + '''/sd-wan/site/''', versa_username, versa_password, 'put', '''{"site":{"site-name":"{$v_Cust-Demo_Site_Name}","site-type":"branch","site-id":"{$v_Customer_Site_Id}","chassis-id":"{$v_Customer_Chassis_ID}","global-tenant-id":"2","management-routing-instance":"Cust-Mgmt","wan-interfaces":{"vni":[{"name":"vni-0/0.0","circuit-name":"Internet1","circuit-type":"Broadband","circuit-media":"DSL","shaping-rate":{},"encryption":"optional","sla-monitoring":{"fc":[{"name":"fc_be","interval":"300000","logging-interval":"300000"},{"name":"fc_ef","interval":"150000","logging-interval":"300000"},{"name":"fc_af","interval":"120000","logging-interval":"240000"},{"name":"fc_nc","interval":"60000","logging-interval":"120000"}]}}]}}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#PostStagging - provOrg Controller
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org/''' + versa_provider_org + '''/sd-wan/controllers''', versa_username, versa_password, 'post', '''{"controller":{"name":"Controller","site-name":"Controller","site-id":"1","transport-addresses":{"transport-address":[{"name":"Cntrl-Trans","ip-address":"{$v_Provider_Controller-addr1_Transport_IP}","routing-instance":"Global-VR"}]},"management-addresses":{"management-address":[{"name":"IKE","ip-address":"{$v_Provider_Controller-IKE_Management_IP}","routing-instance":"Prov-Mgmt"},{"name":"secure","ip-address":"{$v_Provider_Controller-secure_Management_IP}","routing-instance":"Prov-Mgmt"}]}}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - CustOrg Controller
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org/''' + versa_customer_org + '''/sd-wan/controllers''', versa_username, versa_password, 'post', '''{"controller":{"name":"Controller","site-name":"Controller","site-id":"1","transport-addresses":{"transport-address":[{"name":"CustTrans","ip-address":"{$v_Customer_Controller-CustTrans_Transport_IP}","routing-instance":"Global-VR"}]},"management-addresses":{"management-address":[{"name":"IKE","ip-address":"{$v_Customer_Controller-IKE_Management_IP}","routing-instance":"Cust-Mgmt"},{"name":"secure","ip-address":"{$v_Customer_Controller-secure_Management_IP}","routing-instance":"Cust-Mgmt"}]}}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#PostStagging - Prov LEF Tempate
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_provider_org + '''/lef/templates''', versa_username, versa_password, 'post', '''<template><name>Template-ipfix</name><type>ipfix</type></template>''', is_body_json=False, return_xml=True)
except Exception as e:
    print e



#PostStagging - Prov LEF Collector
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' +  versa_provider_org + '''/lef/collectors''', versa_username, versa_password, 'post', '''{"collector":{"name":"Collector1","template":"Template-ipfix","transport":"tcp","destination-port":"''' + analytics_log_port + '''","destination-address":"{$v_Provider_Collector1_Destination_Address}","source-address":"{$v_Provider_Collector1_Source_Address}","transmit-rate":"10000","pending-queue-limit":"2048","template-resend-interval":"60","routing-instance":"Prov-Mgmt"}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e



#PostStagging - Prov LEF Prof1
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_provider_org + '''/lef/profiles''', versa_username, versa_password, 'post', '''{"profile":{"name":"LEF-Prof1","collector":"Collector1"}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Prov LEF Prof2
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_provider_org + '''/lef/default-profile''', versa_username, versa_password, 'put', '''{"default-profile":"LEF-Prof1"}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Cust LEF Tempalte
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_customer_org + '''/lef/templates''', versa_username, versa_password, 'post', '''<template><name>Template-ipfix</name><type>ipfix</type></template>''', is_body_json=False, return_xml=True)
except Exception as e:
    print e


##TODO  unknown elemnts, invalid path  ##Corrected Typo
#PostStagging - Cust LEF Collector
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_customer_org + '''/lef/collectors''', versa_username, versa_password, 'post', '''{"collector":{"name":"Collector1","template":"Template-ipfix","transport":"tcp","destination-port":"''' + analytics_log_port + '''","destination-address":"{$v_Customer_Collector1_Destination_Address}","source-address":"{$v_Customer_Collector1_Source_Address}","transmit-rate":"10000","pending-queue-limit":"2048","template-resend-interval":"60","routing-instance":"Prov-Mgmt"}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Cust LEF Prof 1
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_customer_org + '''/lef/profiles''', versa_username, versa_password, 'post', '''{"profile":{"name":"LEF-Prof1","collector":"Collector1"}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#PostStagging - Cust LEF Prof 2
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_customer_org + '''/lef/default-profile''', versa_username, versa_password, 'put', '''{"default-profile":"LEF-Prof1"}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e



#PostStagging - Prov LogCTRL
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' +  versa_provider_org + '''/traffic-monitoring/logging-control''', versa_username, versa_password, 'post', '''{"logging-control-profile":{"name":"traffic-monitoring","profile":"LEF-Prof1","options":{"stats":{"all":[null]},"sessions":{"all":"both"}}}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Cust LogCTRL
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_customer_org + '''/traffic-monitoring/logging-control''', versa_username, versa_password, 'post', '''{"logging-control-profile":{"name":"traffic-monitoring","profile":"LEF-Prof1","options":{"stats":{"all":[null]},"sessions":{"all":"both"}}}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Cust TrustNW
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_customer_org + '''/objects/zones/zone/trust''', versa_username, versa_password, 'put', '''{"zone":{"name":"trust","lef-profile":"LEF-Prof1","networks":["LAN-NW"]}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Cust RemoteTrust
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_customer_org + '''/objects/zones''', versa_username, versa_password, 'post', '''{"zone":{"name":"remote-trust","lef-profile":"LEF-Prof1","routing-instance":["Cust-Mgmt"]}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Cust ACP Creation
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_customer_org + '''/security/access-policies''', versa_username, versa_password, 'post', '''{"access-policy-group":{"name":"ACP"}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Cust ACP DefaultRule
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_customer_org + '''/security/access-policies/access-policy-group/ACP/rules''', versa_username, versa_password, 'post', '''{"access-policy":{"name":"Default-Allow","match":{"source":{"zone":{},"address":{}},"destination":{"zone":{},"address":{}},"application":{},"ttl":{}},"set":{"lef":{"profile":"LEF-Prof1","event":"both","options":{"send-pcap-data":{"enable":false}}},"action":"allow"}}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Prov IPSec
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_provider_org + '''/ipsec''', versa_username, versa_password, 'post', '''{"vpn-profile":{"name":"Prov-IPSec","vpn-type":"branch-sdwan","tunnel-initiate":"automatic","routing-instance":"Prov-Mgmt","tunnel-routing-instance":"Prov-Mgmt","tunnel-interface":"ptvi1","remote-auth-type":"psk","local-auth-info":{"auth-type":"psk","id-type":"email","key":"''' + poststaging_key + '''","id-string":"{$v_Provider_Prov-IPSec_Local_auth_email_identifier}"},"peer-auth-info":{"auth-type":"psk","id-type":"email","key":"''' + poststaging_key + '''","id-string":"{$v_Provider_Prov-IPSec_Peer_auth_email_identifier}"},"ipsec":{"life":{"duration":28800}},"ike":{"group":"mod1","lifetime":"28800","dpd-timeout":"30"},"local":{"inet":"{$v_Provider_Prov-IPSec_Local_IP}"},"peer":{"inet":"''' + versa_prov_mgmt_ike + '''"}}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Cust IPSec
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/template/Branches-PostStaging/config/orgs/org-services/''' + versa_customer_org + '''/ipsec''', versa_username, versa_password, 'post', '''{"vpn-profile":{"name":"PostStaging-IPSec","vpn-type":"branch-sdwan","tunnel-initiate":"automatic","routing-instance":"Cust-Mgmt","tunnel-routing-instance":"Cust-Mgmt","tunnel-interface":"ptvi2","remote-auth-type":"psk","local-auth-info":{"auth-type":"psk","id-type":"email","key":"''' + poststaging_key + '''","id-string":"{$v_Customer_PostStaging-IPSec_Local_auth_email_identifier}"},"peer-auth-info":{"auth-type":"psk","id-type":"email","key":"''' + poststaging_key + '''","id-string":"{$v_Customer_PostStaging-IPSec_Peer_auth_email_identifier}"},"ipsec":{"life":{"duration":28800}},"ike":{"group":"mod1","lifetime":"28800","dpd-timeout":"30"},"local":{"inet":"{$v_Customer_PostStaging-IPSec_Local_IP}"},"peer":{"inet":"''' + versa_tnt_mgmt_ike + '''"}}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e
                                                                                                                                                                                                                         
#PostStagging - Bind Data Bracnh2
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/device-template-variable/''' + bracnh2_name + ''',Branches-PostStaging''', versa_username, versa_password, 'put', '''{"device-template-variable":{"device":"''' + bracnh2_name + '''","serial-number":"''' + br2_chas + '''","template":"Branches-PostStaging","variable-binding":{"attrs":[{"name":"{$v_Customer_Site_Id}","value":"''' + br2_number + '''"},{"name":"{$v_Provider_Prov-IPSec_Local_auth_email_identifier}","value":"''' + br2_staging_ipsec_id + '''"},{"name":"{$v_Cust-Mgmt_Destination_address-0}","value":"0.0.0.0/0"},{"name":"{$v_Prov-Mgmt_Destination_address-0}","value":"0.0.0.0/0"},{"name":"{$v_Provider_Collector1_Destination_Address}","value":"''' + versa_analytics_sb_ip + '''"},{"name":"{$v_tvi-0-2_-_Unit_0_Static_address}","value":"''' + versa_branch2_tvi2_ip + versa_branch2_tvi2_subnet + '''"},{"name":"{$v_Customer_PostStaging-IPSec_Peer_auth_email_identifier}","value":"''' + provider_poststaging_ipsec_id + '''"},{"name":"{$v_Global-VR_Next_Hop_address-0}","value":"''' + controller_sdwan_ip + '''"},{"name":"{$v_tvi-0-4_-_Unit_0_Static_address}","value":"''' + versa_branch2_tvi4_ip + versa_branch2_tvi4_subnet + '''"},{"name":"{$v_Cust-Mgmt_Next_Hop_address-0}","value":"''' + versa_branch2_tvi5_ip + '''"},{"name":"{$v_tvi-0-5_-_Unit_0_Static_address}","value":"''' + versa_branch2_tvi5_ip + versa_branch2_tvi5_subnet + '''"},{"name":"{$v_Customer_PostStaging-IPSec_Local_IP}","value":"''' + versa_branch2_tvi4_ip + '''"},{"name":"{$v_Prov-Mgmt_Next_Hop_address-0}","value":"''' + versa_branch2_tvi2_ip + '''"},{"name":"{$v_Cust-Mgmt_MPLS_Local_Router_address}","value":"''' + versa_branch2_tvi5_ip + '''"},{"name":"{$v_Cust-Mgmt_1_versa_Neighbor_IP-0}","value":"''' + versa_tnt_mgmt_ipsec + '''"},{"name":"{$v_identification}","value":"''' + bracnh2_name + '''"},{"name":"{$v_Cust-Demo_Site_Name}","value":"Branch2"},{"name":"{$v_location}","value":"''' + br2_location + '''"},{"name":"{$v_Prov-Mgmt_Destination_address-1}","value":"''' + versa_sb_network + versa_sb_subnet + '''"},{"name":"{$v_Cust-Mgmt_1_versa_Neighbor_Local_IP-0}","value":"''' + versa_branch2_tvi5_ip + '''"},{"name":"{$v_tvi-0-1_-_Unit_0_Static_address}","value":"''' + versa_branch2_tvi1_ip + versa_branch2_tvi1_subnet + '''"},{"name":"{$v_Customer_Collector1_Source_Address}","value":"''' + versa_branch2_tvi2_ip + '''"},{"name":"{$v_vni-0-0_-_Unit_0_Static_address}","value":"''' + versa_branch2_sdwan_ip + versa_branch2_sdwan_subnet + '''"},{"name":"{$v_Provider_Collector1_Source_Address}","value":"''' + versa_branch2_tvi2_ip + '''"},{"name":"{$v_longitude}","value":"''' + br2_long + '''"},{"name":"{$v_Cust-Mgmt_1_Router_ID-0}","value":"''' + versa_branch2_tvi5_ip + '''"},{"name":"{$v_Customer_Controller-IKE_Management_IP}","value":"''' + versa_tnt_mgmt_ike + '''"},{"name":"{$v_Customer_Collector1_Destination_Address}","value":"''' + versa_analytics_sb_ip + '''"},{"name":"{$v_latitude}","value":"''' + br2_lat + '''"},{"name":"{$v_vni-0-1_-_Unit_0_Static_address}","value":"''' + versa_branch_server_gateway + versa_branch_server_subnet + '''"},{"name":"{$v_Prov-Mgmt_Next_Hop_address-1}","value":"''' + versa_prov_mgmt_ipsec + '''"},{"name":"{$v_VNF_IP_Address-Prefix}","value":"''' + versa_director_sb_ip + '''/32"},{"name":"{$v_Customer_PostStaging-IPSec_Local_auth_email_identifier}","value":"''' + br2_poststaging_ipsec_id + '''"},{"name":"{$v_Customer_Controller-secure_Management_IP}","value":"''' + versa_tnt_mgmt_ipsec + '''"},{"name":"{$v_Customer_Chassis_ID}","value":"''' + br2_chas + '''"},{"name":"{$v_Provider_Prov-IPSec_Peer_auth_email_identifier}","value":"''' + provider_staging_ipsec_id + '''"},{"name":"{$v_Provider_Prov-IPSec_Local_IP}","value":"''' + versa_branch2_tvi1_ip + '''"},{"name":"{$v_Customer_Controller-CustTrans_Transport_IP}","value":"''' + controller_sdwan_ip + '''"},{"name":"{$v_Provider_Controller-addr1_Transport_IP}","value":"''' + controller_sdwan_ip + '''"},{"name":"{$v_Provider_Site_Name}","value":"''' + bracnh2_name + '''"},{"name":"{$v_Provider_Controller-IKE_Management_IP}","value":"''' + versa_prov_mgmt_ike + '''"},{"name":"{$v_Provider_Chassis_ID}","value":"''' + br2_chas + '''"},{"name":"{$v_Provider_Controller-secure_Management_IP}","value":"''' + versa_prov_mgmt_ipsec + '''"},{"name":"{$v_Provider_Site_Id}","value":"''' + br2_number + '''"}]}}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#PostStagging - Bind Data Bracnh1
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/device-template-variable/''' + bracnh1_name + ''',Branches-PostStaging''', versa_username, versa_password, 'put', '''{"device-template-variable":{"device":"''' + bracnh1_name + '''","serial-number":"''' + br1_chas + '''","template":"Branches-PostStaging","variable-binding":{"attrs":[{"name":"{$v_Customer_Site_Id}","value":"''' + br1_number + '''"},{"name":"{$v_Provider_Prov-IPSec_Local_auth_email_identifier}","value":"''' + br1_staging_ipsec_id + '''"},{"name":"{$v_Cust-Mgmt_Destination_address-0}","value":"0.0.0.0/0"},{"name":"{$v_Prov-Mgmt_Destination_address-0}","value":"0.0.0.0/0"},{"name":"{$v_Provider_Collector1_Destination_Address}","value":"''' + versa_analytics_sb_ip + '''"},{"name":"{$v_tvi-0-2_-_Unit_0_Static_address}","value":"''' + versa_branch1_tvi2_ip + versa_branch1_tvi2_subnet + '''"},{"name":"{$v_Customer_PostStaging-IPSec_Peer_auth_email_identifier}","value":"''' + provider_poststaging_ipsec_id + '''"},{"name":"{$v_Global-VR_Next_Hop_address-0}","value":"''' + controller_sdwan_ip + '''"},{"name":"{$v_tvi-0-4_-_Unit_0_Static_address}","value":"''' + versa_branch1_tvi4_ip + versa_branch1_tvi4_subnet + '''"},{"name":"{$v_Cust-Mgmt_Next_Hop_address-0}","value":"''' + versa_branch1_tvi5_ip + '''"},{"name":"{$v_tvi-0-5_-_Unit_0_Static_address}","value":"''' + versa_branch1_tvi5_ip + versa_branch1_tvi5_subnet + '''"},{"name":"{$v_Customer_PostStaging-IPSec_Local_IP}","value":"''' + versa_branch1_tvi4_ip + '''"},{"name":"{$v_Prov-Mgmt_Next_Hop_address-0}","value":"''' + versa_branch1_tvi2_ip + '''"},{"name":"{$v_Cust-Mgmt_MPLS_Local_Router_address}","value":"''' + versa_branch1_tvi5_ip + '''"},{"name":"{$v_Cust-Mgmt_1_versa_Neighbor_IP-0}","value":"''' + versa_tnt_mgmt_ipsec + '''"},{"name":"{$v_identification}","value":"''' + bracnh1_name + '''"},{"name":"{$v_Cust-Demo_Site_Name}","value":"Branch1"},{"name":"{$v_location}","value":"''' + br1_location + '''"},{"name":"{$v_Prov-Mgmt_Destination_address-1}","value":"''' + versa_sb_network + versa_sb_subnet + '''"},{"name":"{$v_Cust-Mgmt_1_versa_Neighbor_Local_IP-0}","value":"''' + versa_branch1_tvi5_ip + '''"},{"name":"{$v_tvi-0-1_-_Unit_0_Static_address}","value":"''' + versa_branch1_tvi1_ip + versa_branch1_tvi1_subnet + '''"},{"name":"{$v_Customer_Collector1_Source_Address}","value":"''' + versa_branch1_tvi2_ip + '''"},{"name":"{$v_vni-0-0_-_Unit_0_Static_address}","value":"''' + versa_branch1_sdwan_ip + versa_branch1_sdwan_subnet + '''"},{"name":"{$v_Provider_Collector1_Source_Address}","value":"''' + versa_branch1_tvi2_ip + '''"},{"name":"{$v_longitude}","value":"''' + br1_long + '''"},{"name":"{$v_Cust-Mgmt_1_Router_ID-0}","value":"''' + versa_branch1_tvi5_ip + '''"},{"name":"{$v_Customer_Controller-IKE_Management_IP}","value":"''' + versa_tnt_mgmt_ike + '''"},{"name":"{$v_Customer_Collector1_Destination_Address}","value":"''' + versa_analytics_sb_ip + '''"},{"name":"{$v_latitude}","value":"''' + br1_lat + '''"},{"name":"{$v_vni-0-1_-_Unit_0_Static_address}","value":"''' + versa_branch_client_gateway + versa_branch_client_subnet + '''"},{"name":"{$v_Prov-Mgmt_Next_Hop_address-1}","value":"''' + versa_prov_mgmt_ipsec + '''"},{"name":"{$v_VNF_IP_Address-Prefix}","value":"''' + versa_director_sb_ip + '''/32"},{"name":"{$v_Customer_PostStaging-IPSec_Local_auth_email_identifier}","value":"''' + br1_poststaging_ipsec_id + '''"},{"name":"{$v_Customer_Controller-secure_Management_IP}","value":"''' + versa_tnt_mgmt_ipsec + '''"},{"name":"{$v_Customer_Chassis_ID}","value":"''' + br1_chas + '''"},{"name":"{$v_Provider_Prov-IPSec_Peer_auth_email_identifier}","value":"''' + provider_staging_ipsec_id + '''"},{"name":"{$v_Provider_Prov-IPSec_Local_IP}","value":"''' + versa_branch1_tvi1_ip + '''"},{"name":"{$v_Customer_Controller-CustTrans_Transport_IP}","value":"''' + controller_sdwan_ip + '''"},{"name":"{$v_Provider_Controller-addr1_Transport_IP}","value":"''' + controller_sdwan_ip + '''"},{"name":"{$v_Provider_Site_Name}","value":"''' + bracnh1_name + '''"},{"name":"{$v_Provider_Controller-IKE_Management_IP}","value":"''' + versa_prov_mgmt_ike + '''"},{"name":"{$v_Provider_Chassis_ID}","value":"''' + br1_chas + '''"},{"name":"{$v_Provider_Controller-secure_Management_IP}","value":"''' + versa_prov_mgmt_ipsec + '''"},{"name":"{$v_Provider_Site_Id}","value":"''' + br1_number + '''"}]}}}''', is_body_json=True, return_xml=True)
except Exception as e:
    print e
