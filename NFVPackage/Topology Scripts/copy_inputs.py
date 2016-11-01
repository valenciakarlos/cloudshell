from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from cloudshell.api.cloudshell_api import InputNameValue, CloudShellAPISession, AttributeNameValue, \
    ResourceAttributesUpdateRequest

csapi = helpers.get_api_session()
resid = helpers.get_reservation_context_details().id

rd = csapi.GetReservationDetails(resid).ReservationDescription

siteman_details = [r for r in rd.Resources if r.ResourceModelName == 'SiteManagerShell'][0]
# brocade_details = [r for r in rd.Resources if r.ResourceModelName == 'Brocade NOS Switch'][0]
# onrack_details = [r for r in rd.Resources if r.ResourceModelName == 'OnrackShell'][0]

esxis_details = [csapi.GetResourceDetails(r.Name) for r in rd.Resources if r.ResourceModelName == 'ComputeShell']

vcenter_attrs = {}
for s in rd.Services:
    if s.ServiceName == 'vCenter':
        vcenter_attrs = dict([(a.Name, a.Value) for a in s.Attributes])

scaleio_attrs = {}
for s in rd.Services:
    if s.ServiceName == 'ScaleIO':
        scaleio_attrs = dict([(a.Name, a.Value) for a in s.Attributes])

versa_attrs = {}
for s in rd.Services:
    if s.ServiceName == 'Versa':
        versa_attrs = dict([(a.Name, a.Value) for a in s.Attributes])

site_manager_attrs = dict([(a.Name, a.Value) for a in csapi.GetResourceDetails(siteman_details.Name).ResourceAttributes])
site_manager_attrs['ResourceAddress'] = siteman_details.FullAddress

# brocade_attrs = dict([(a.Name, a.Value) for a in csapi.GetResourceDetails(brocade_details.Name).ResourceAttributes])
# brocade_attrs['ResourceAddress'] = brocade_details.FullAddress

# onrack_attrs = dict([(a.Name, a.Value) for a in csapi.GetResourceDetails(onrack_details.Name).ResourceAttributes])
# onrack_attrs['ResourceAddress'] = onrack_details.FullAddress


site_manager_attrs['Interface Names For Migration'] = 'aaua'
site_manager_attrs['Default VLAN'] = '4'
site_manager_attrs['Management VLAN'] = '5'
# site_manager_attrs['Management Gateway'] = site_manager_attrs['Management Start IP']
# site_manager_attrs['Data Gateway'] = site_manager_attrs['Data Start IP']
# site_manager_attrs['Data2 Gateway'] = site_manager_attrs['Data2 Start IP']

emc_mgmt_portgroup = 'mgmtportgrp'
emc_data_portgroup = 'dataportgrp'
emc_data2_portgroup = 'data2portgrp'

edge_ip_pool_start = '10.10.109.180'
edge_ip_pool_end = '10.10.109.200'
edge_ip_pool_gateway = '10.10.109.1'

vcd_license_key = 'T000L-JZ5EK-N827J-0X106-AX5PH'

data_ip_start = site_manager_attrs['Data Start IP']
data2_ip_start = site_manager_attrs['Data2 Start IP']
mgmt_ip_start = site_manager_attrs['Management Start IP']
pxe_ip_start = site_manager_attrs['PXE Network Start IP']

# brocade_ip = brocade_attrs['ResourceAddress']
# brocade_password = brocade_attrs['Password']
data_gateway = site_manager_attrs['Data Gateway']
data_netmask = site_manager_attrs['Data Netmask']
data2_gateway = site_manager_attrs['Data2 Gateway']
data2_netmask = site_manager_attrs['Data2 Netmask']
data_search_domain = site_manager_attrs['Data Search Domains']
management_dns1 = site_manager_attrs['Management DNS1']
management_dns2 = site_manager_attrs['Management DNS2']
management_gateway = site_manager_attrs['Management Gateway']
management_netmask = site_manager_attrs['Management Netmask']
management_ntp_ip = site_manager_attrs['Management NTP']
management_search_domain = site_manager_attrs['Management Search Domains']
pxe_gateway = site_manager_attrs['PXE Network Gateway']
pxe_netmask = site_manager_attrs['PXE Network Netmask']

# onrack_ip = onrack_attrs['ResourceAddress']


cluster2_name = vcenter_attrs['vCenter Cluster2 Name']
cluster3_name = vcenter_attrs['vCenter Cluster3 Name']
datacenter = vcenter_attrs['vCenter Datacenter Name']
esx_root_password = vcenter_attrs['vCenter Datacenter Name']
sio_unified_datastore = scaleio_attrs['Unified Datastore']
vcenter_datastore = vcenter_attrs['vCenter Datastore']
vcenter_password = vcenter_attrs['vCenter Administrator Password']
vds1_name = vcenter_attrs['VDS1 Name']
versa_analytics_sb_ip = versa_attrs.get('Versa Analytics SB IP', '')
versa_controller_lan_ip = versa_attrs.get('Versa Controller LAN IP', '')

def ipadd(base, offset):
    a = [int(x) for x in base.split('.')]
    for i in range(len(a)):
        a[len(a) - 1 - i] += offset
        if a[len(a) - 1 - i] <= 255:
            return '.'.join([str(x) for x in a])
        a[len(a) - 1 - i] -= 256
        offset = 1
    raise Exception('ip address overflow %s + %d' % (base, offset))

def mgmt_pool(offset):
    return ipadd(mgmt_ip_start, offset)

def data_pool(offset):
    return ipadd(data_ip_start, offset)

def data2_pool(offset):
    return ipadd(data2_ip_start, offset)

pxeoffset = 0
def pxe_dynamic():
    global pxeoffset
    rv = ipadd(pxe_ip_start, pxeoffset)
    # print 'pxe dynamic %d' % pxeoffset
    pxeoffset += 1
    return rv

mgmtoffset = 42
def mgmt_dynamic():
    global mgmtoffset
    rv = ipadd(mgmt_ip_start, mgmtoffset)
    # print 'mgmt dynamic %d' % mgmtoffset
    mgmtoffset += 1
    return rv

dataoffset = 42
def data_dynamic():
    global dataoffset
    rv = ipadd(data_ip_start, dataoffset)
    dataoffset += 1
    return rv

data2offset = 42
def data2_dynamic():
    global data2offset
    rv = ipadd(data2_ip_start, data2offset)
    data2offset += 1
    return rv

vcenter_ip = mgmt_pool(1)
scaleio_gateway_management_ip = mgmt_pool(10)
scaleio_gateway_data_ip = data_pool(10)
scaleio_gateway_data2_ip = data2_pool(10)

scaleio_primary_mdm_mgmt_ip = mgmt_pool(7)
scaleio_primary_mdm_data_ip = data_pool(7)
scaleio_primary_mdm_data2_ip = data2_pool(7)
scaleio_secondary_mdm_mgmt_ip = mgmt_pool(8)
scaleio_secondary_mdm_data_ip = data_pool(8)
scaleio_secondary_mdm_data2_ip = data2_pool(8)
scaleio_tiebreaker_mgmt_ip = mgmt_pool(9)
scaleio_tiebreaker_data_ip = data_pool(9)
scaleio_tiebreaker_data2_ip = data2_pool(9)
# scaleio_sds1_data_ip = data_pool(36)
# scaleio_sds1_mgmt_ip = mgmt_pool(36)
# scaleio_sds2_data_ip = data_pool(37)
# scaleio_sds2_mgmt_ip = mgmt_pool(37)
# scaleio_sds3_data_ip = data_pool(38)
# scaleio_sds3_mgmt_ip = mgmt_pool(38)
# scaleio_sds4_data_ip = data_pool(39)
# scaleio_sds4_mgmt_ip = mgmt_pool(39)


vrops_ip = mgmt_pool(6)
logi_ip = mgmt_pool(5)
nagios_ip = mgmt_pool(2)
vcd_vm_ip = data_pool(1)
vcd_management_ip = mgmt_pool(4)
nsx_manager_ip = mgmt_pool(3)
compute_ip_pool_start = data_pool(15)
compute_ip_pool_end = data_pool(25)
mgmt_ip_pool_start = mgmt_pool(15)
mgmt_ip_pool_end = mgmt_pool(35)
versa_director_nb_ip = mgmt_pool(40)
versa_analytics_nb_ip = mgmt_pool(11)
versa_controller_nb_ip = mgmt_pool(12)
versa_branch1_nb_ip = mgmt_pool(13)
versa_branch2_nb_ip = mgmt_pool(14)
vra_ip = mgmt_pool(41)


sio_master_host_ip = ''
versa_host_ips = []

sio_mdm_host_ips = []
sio_nonmdm_host_ips = []
# deploy master
# vcenter on master
# master in Master cluster
# 3 other hosts in SIO cluster
# other hosts in third cluster "NFV" "VNF" "Compute"
# SDS on all in "Compute"

all_host_ips = []
all_host_ips172 = []
sdc_host_ips = []
sds_host_ips = []

ed2 = []
for p in ['48B', '495', '48C', '487', '489']:
    for ed in esxis_details:
        if p in ed.Name:
            ed2.append(ed)

for ed in esxis_details:
    if ed not in ed2:
        ed2.append(ed)

esxis_details = ed2

host_name2ip = {}
host_name2ip172 = {}

pxeoffset = mgmtoffset


for i in range(len(esxis_details)):
    # addr = esxis_details[i].Address
    # addr172 = [a.Value for a in esxis_details[i].ResourceAttributes if a.Name == 'ESX PXE Network IP'][0]

    addr = mgmt_dynamic()
    addr172 = pxe_dynamic()

    host_name2ip[esxis_details[i].Name] = addr
    host_name2ip172[esxis_details[i].Name] = addr172

    all_host_ips.append(addr)
    all_host_ips172.append(addr172)

    if i == 0:
        sio_master_host_ip = addr

    if i in [2, 3]:
        versa_host_ips.append(addr)

    if 1 <= i <= 3:
        sio_mdm_host_ips.append(addr)
    if i > 3:
        sio_nonmdm_host_ips.append(addr)

    sds_host_ips.append(addr)
    sdc_host_ips.append(addr)


# print host_name2ip
# print mgmtoffset
# print host_name2ip172
# print pxeoffset

svm_mgmt_ips = [mgmt_dynamic() for _ in sds_host_ips]
svm_data_ips = [data_dynamic() for _ in sds_host_ips]
svm_data2_ips = [data2_dynamic() for _ in sds_host_ips]

sdc_data_vmk_ips = [data_dynamic() for _ in sdc_host_ips]
sdc_data2_vmk_ips = [data2_dynamic() for _ in sdc_host_ips]

aa = [
    # ('Resource', 'ComputeShell', 'OnRack Address', onrack_ip),
    ('Resource', 'ComputeShell', 'ResourceAddress', host_name2ip),
    ('Resource', 'ComputeShell', 'ESX PXE Network IP', host_name2ip172),
    ('Resource', 'ComputeShell', 'ESX Gateway', management_gateway),
    ('Resource', 'ComputeShell', 'ESX Netmask', management_netmask),
    ('Resource', 'ComputeShell', 'ESX Domain', management_search_domain),
    ('Resource', 'ComputeShell', 'ESX DNS1', management_dns1),
    ('Resource', 'ComputeShell', 'ESX DNS2', management_dns2),
    ('Resource', 'ComputeShell', 'ESX PXE Network Gateway', pxe_gateway),
    ('Resource', 'ComputeShell', 'ESX PXE Network Netmask', pxe_netmask),

    ('Service', 'vCenter', 'vCenter ESXi IP', sio_master_host_ip),
    ('Service', 'vCenter', 'vCenter IP', vcenter_ip),
    ('Service', 'vCenter', 'vCenter Gateway', management_gateway),
    ('Service', 'vCenter', 'vCenter DNS1', management_dns1),
    ('Service', 'vCenter', 'vCenter DNS2', management_dns2),
    ('Service', 'vCenter', 'vCenter NTP Server', management_ntp_ip),

    ('Service', 'vCenter', 'vCenter Cluster1 ESXis', sio_master_host_ip),
    ('Service', 'vCenter', 'vCenter Cluster2 ESXis', ','.join(sio_nonmdm_host_ips)),
    ('Service', 'vCenter', 'vCenter Cluster3 ESXis', ','.join(sio_mdm_host_ips)),

    ('Service', 'vCenter', 'VDS1 Hosts', ','.join(all_host_ips)),
    ('Service', 'vCenter', 'VDS1 Hosts PXE IPs', ','.join(all_host_ips172)),
    ('Service', 'vCenter', 'VDS1 Kernel Subnet', ''),
    ('Service', 'vCenter', 'VDS1 Kernel IPs', ''),

    ('Service', 'vCenter', 'VDS2 Hosts', ','.join(sdc_host_ips)),
    ('Service', 'vCenter', 'VDS2 Kernel Subnet', data_netmask),
    ('Service', 'vCenter', 'VDS2 Kernel IPs', ','.join(sdc_data_vmk_ips)),

    ('Service', 'vCenter', 'VDS3 Hosts', ','.join(versa_host_ips)),
    ('Service', 'vCenter', 'VDS3 Kernel Subnet', ''),
    ('Service', 'vCenter', 'VDS3 Kernel IPs', ''),

    ('Service', 'vCenter', 'VDS4 Hosts', ','.join(versa_host_ips)),
    ('Service', 'vCenter', 'VDS4 Kernel Subnet', ''),
    ('Service', 'vCenter', 'VDS4 Kernel IPs', ''),

    ('Service', 'vCenter', 'VDS5 Hosts', ','.join(sdc_host_ips)),
    ('Service', 'vCenter', 'VDS5 Kernel Subnet', data2_netmask),
    ('Service', 'vCenter', 'VDS5 Kernel IPs', ','.join(sdc_data2_vmk_ips)),

    ('Service', 'ScaleIO', 'vCenter IP', vcenter_ip),
    ('Service', 'ScaleIO', 'Call Home DNS Server 1', management_dns1),
    ('Service', 'ScaleIO', 'Call Home DNS Server 2', management_dns2),
    ('Service', 'ScaleIO', 'Host for ScaleIO Gateway', sio_master_host_ip),
    ('Service', 'ScaleIO', 'Management Network Label', emc_mgmt_portgroup),
    ('Service', 'ScaleIO', 'Data Network Label', emc_data_portgroup),
    ('Service', 'ScaleIO', 'Data2 Network Label', emc_data2_portgroup),
    ('Service', 'ScaleIO', 'Gateway Management IP', scaleio_gateway_management_ip),
    ('Service', 'ScaleIO', 'Gateway Data IP', scaleio_gateway_data_ip),
    ('Service', 'ScaleIO', 'Gateway Data2 IP', scaleio_gateway_data2_ip),
    ('Service', 'ScaleIO', 'Primary MDM Management IP', scaleio_primary_mdm_mgmt_ip),
    ('Service', 'ScaleIO', 'Primary MDM Data IP', scaleio_primary_mdm_data_ip),
    ('Service', 'ScaleIO', 'Primary MDM Data2 IP', scaleio_primary_mdm_data2_ip),
    ('Service', 'ScaleIO', 'Secondary MDM Management IP', scaleio_secondary_mdm_mgmt_ip),
    ('Service', 'ScaleIO', 'Secondary MDM Data IP', scaleio_secondary_mdm_data_ip),
    ('Service', 'ScaleIO', 'Secondary MDM Data2 IP', scaleio_secondary_mdm_data2_ip),
    ('Service', 'ScaleIO', 'Tie Breaker Management IP', scaleio_tiebreaker_mgmt_ip),
    ('Service', 'ScaleIO', 'Tie Breaker Data IP', scaleio_tiebreaker_data_ip),
    ('Service', 'ScaleIO', 'Tie Breaker Data2 IP', scaleio_tiebreaker_data2_ip),
    # ('Service', 'ScaleIO', 'SDS1 Data IP', scaleio_sds1_data_ip),
    # ('Service', 'ScaleIO', 'SDS1 MGMT IP', scaleio_sds1_mgmt_ip),
    # ('Service', 'ScaleIO', 'SDS2 Data IP', scaleio_sds2_data_ip),
    # ('Service', 'ScaleIO', 'SDS2 MGMT IP', scaleio_sds2_mgmt_ip),
    # ('Service', 'ScaleIO', 'SDS3 Data IP', scaleio_sds3_data_ip),
    # ('Service', 'ScaleIO', 'SDS3 MGMT IP', scaleio_sds3_mgmt_ip),
    # ('Service', 'ScaleIO', 'SDS4 Data IP', scaleio_sds4_data_ip),
    # ('Service', 'ScaleIO', 'SDS4 MGMT IP', scaleio_sds4_mgmt_ip),
    ('Service', 'ScaleIO', 'SDS Management IPs CSV', ','.join(svm_mgmt_ips)),
    ('Service', 'ScaleIO', 'SDS Data IPs CSV', ','.join(svm_data_ips)),
    ('Service', 'ScaleIO', 'SDS Data2 IPs CSV', ','.join(svm_data2_ips)),

    ('Service', 'ScaleIO', 'MGMT Subnet', management_netmask),
    ('Service', 'ScaleIO', 'Data Subnet', data_netmask),
    ('Service', 'ScaleIO', 'Data2 Subnet', data2_netmask),
    ('Service', 'ScaleIO', 'MGMT Gateway', management_gateway),

    ('Service', 'vRealize Operations Manager', 'vCenter FQDN', vcenter_ip),
    ('Service', 'vRealize Operations Manager', 'vROPS IP', vrops_ip),
    ('Service', 'vRealize Operations Manager', 'vROPS Netmask', management_netmask),
    ('Service', 'vRealize Operations Manager', 'vROPS Gateway', management_gateway),
    ('Service', 'vRealize Operations Manager', 'vROPS DNS Server IP', management_dns1),
    ('Service', 'vRealize Operations Manager', 'vROPS NTP Server IP', management_ntp_ip),
    ('Service', 'vRealize Operations Manager', 'vROPS Product Key', ''),
    ('Service', 'vRealize Operations Manager', 'Cloud vCenter FQDN', vcenter_ip),

    ('Service', 'vRealize Log Insight', 'Log Insight IP', logi_ip),
    ('Service', 'vRealize Log Insight', 'Log Insight Gateway', management_gateway),
    ('Service', 'vRealize Log Insight', 'Log Insight Netmask', management_netmask),
    ('Service', 'vRealize Log Insight', 'Log Insight DNS Server IP', management_dns1),
    ('Service', 'vRealize Log Insight', 'Log Insight License Key', ''),
    ('Service', 'vRealize Log Insight', 'Log Insight NTP Servers CSV', management_ntp_ip),
    ('Service', 'vRealize Log Insight', 'vROPS FQDN', vrops_ip),

    ('Service', 'Nagios Registration', 'Nagios Machine IP Address', nagios_ip),
    ('Service', 'Nagios Monitoring', 'Nagios DNS1', management_dns1),
    ('Service', 'Nagios Monitoring', 'Nagios DNS2', management_dns2),
    ('Service', 'Nagios Monitoring', 'Nagios Gateway', management_gateway),
    ('Service', 'Nagios Monitoring', 'Nagios IP', nagios_ip),
    ('Service', 'Nagios Monitoring', 'Nagios Netmask', management_netmask),
    ('Service', 'Nagios Monitoring', 'Nagios Search Domains', management_search_domain),
    ('Service', 'Nagios Monitoring', 'vCenter IP', vcenter_ip),
    ('Resource', 'NagiosServer', 'Nagios IP', nagios_ip),

    ('Service', 'vCloud Director', 'vCenter IP', vcenter_ip),
    ('Service', 'vCloud Director', 'vCD Management DNS1', management_dns1),
    ('Service', 'vCloud Director', 'vCD Management DNS2', management_dns2),
    ('Service', 'vCloud Director', 'vCD Management Gateway', management_gateway),
    ('Service', 'vCloud Director', 'vCD Management IP', vcd_management_ip),
    ('Service', 'vCloud Director', 'vCD Management Netmask', management_netmask),
    ('Service', 'vCloud Director', 'vCD Management Search Domains', management_search_domain),
    ('Service', 'vCloud Director', 'vCD VM IP', vcd_vm_ip),
    ('Service', 'vCloud Director', 'vCD VM Netmask', data_netmask),
    ('Service', 'vCloud Director', 'vCD VM Gateway', data_gateway),
    ('Service', 'vCloud Director', 'vCD License Key', vcd_license_key),
    ('Service', 'vCloud Director', 'vShield Manager Address', nsx_manager_ip),

    ('Service', 'NSX Manager', 'NSX IP', nsx_manager_ip),
    ('Service', 'NSX Manager', 'vCenter IP', vcenter_ip),
    ('Service', 'NSX Manager', 'Compute IP Pool DNS Suffix', data_search_domain),
    ('Service', 'NSX Manager', 'Compute IP Pool Start IP', compute_ip_pool_start),
    ('Service', 'NSX Manager', 'Compute IP Pool End IP', compute_ip_pool_end),
    ('Service', 'NSX Manager', 'Compute IP Pool Gateway', data_gateway),
    ('Service', 'NSX Manager', 'Edge IP Pool Start IP', edge_ip_pool_start),
    ('Service', 'NSX Manager', 'Edge IP Pool End IP', edge_ip_pool_end),
    ('Service', 'NSX Manager', 'Edge IP Pool Gateway', edge_ip_pool_gateway),
    ('Service', 'NSX Manager', 'MGMT IP Pool DNS Server1', management_dns1),
    ('Service', 'NSX Manager', 'MGMT IP Pool DNS Server2', management_dns2),
    ('Service', 'NSX Manager', 'MGMT IP Pool DNS Suffix', management_search_domain),
    ('Service', 'NSX Manager', 'MGMT IP Pool Start IP', mgmt_ip_pool_start),
    ('Service', 'NSX Manager', 'MGMT IP Pool End IP', mgmt_ip_pool_end),
    ('Service', 'NSX Manager', 'MGMT IP Pool Gateway', management_gateway),
    ('Service', 'NSX Manager', 'NSX DNS Server IP', management_dns1),
    ('Service', 'NSX Manager', 'NSX Gateway IP', management_gateway),
    ('Service', 'NSX Manager', 'NSX Netmask', management_netmask),
    ('Service', 'NSX Manager', 'NSX NTP Servers', management_ntp_ip),
    ('Service', 'NSX Manager', 'NSX Search Domain', management_search_domain),
    ('Service', 'NSX Manager', 'Cluster', cluster2_name),
    ('Service', 'NSX Manager', 'Controller Cluster', cluster2_name),
    ('Service', 'NSX Manager', 'Compute Cluster', cluster2_name),
    ('Service', 'NSX Manager', 'MGMT Cluster', cluster2_name),

    ('Service', 'Versa Director', 'Versa Director NB DNS', management_dns1),
    ('Service', 'Versa Director', 'Versa Director NB Gateway', management_gateway),
    ('Service', 'Versa Director', 'Versa Director NB IP', versa_director_nb_ip),
    ('Service', 'Versa Director', 'Versa Director NB Mask', management_netmask),
    ('Service', 'Versa Director', 'Versa Analytics NB DNS', management_dns1),
    ('Service', 'Versa Director', 'Versa Analytics NB Gateway', management_gateway),
    ('Service', 'Versa Director', 'Versa Analytics NB IP', versa_analytics_nb_ip),
    ('Service', 'Versa Director', 'Versa Analytics NB Mask', management_netmask),
    ('Service', 'Versa Director', 'Versa Controller NB DNS', management_dns1),
    ('Service', 'Versa Director', 'Versa Controller NB Gateway', management_gateway),
    ('Service', 'Versa Director', 'Versa Controller NB IP', versa_controller_nb_ip),
    ('Service', 'Versa Director', 'Versa Controller NB Mask', management_netmask),
    ('Service', 'Versa Director', 'Versa Branch1 NB DNS', management_dns1),
    ('Service', 'Versa Director', 'Versa Branch1 NB Gateway', management_gateway),
    ('Service', 'Versa Director', 'Versa Branch1 NB IP', versa_branch1_nb_ip),
    ('Service', 'Versa Director', 'Versa Branch1 NB Mask', management_netmask),
    ('Service', 'Versa Director', 'Versa Branch2 NB DNS', management_dns1),
    ('Service', 'Versa Director', 'Versa Branch2 NB Gateway', management_gateway),
    ('Service', 'Versa Director', 'Versa Branch2 NB IP', versa_branch2_nb_ip),
    ('Service', 'Versa Director', 'Versa Branch2 NB Mask', management_netmask),

    # ('Service', 'OnRack', 'ESX Root Password', esx_root_password),
    ('Service', 'vCenter', 'vCenter SSO Password', vcenter_password),
    ('Service', 'ScaleIO', 'vCenter IP', vcenter_ip),
    ('Service', 'ScaleIO', 'vCenter Password', vcenter_password),
    ('Service', 'ScaleIO', 'Datacenter', datacenter),
    ('Service', 'ScaleIO', 'ScaleIO Admin Password', vcenter_password),
    ('Service', 'ScaleIO', 'Unified Datastore', sio_unified_datastore),
    ('Service', 'ScaleIO', 'ESX Root Password', esx_root_password),
    ('Service', 'ScaleIO', 'Gateway Admin Password', vcenter_password),
    ('Service', 'ScaleIO', 'LIA Password', vcenter_password),
    ('Service', 'ScaleIO', 'SVM Root Password', esx_root_password),
    ('Service', 'ScaleIO', 'Management Network Label', emc_mgmt_portgroup),
    ('Service', 'ScaleIO', 'Data Network Label', emc_data_portgroup),
    ('Service', 'ScaleIO', 'Data2 Network Label', emc_data2_portgroup),
    ('Service', 'ScaleIO', 'ScaleIO Cluster', cluster3_name),

    ('Service', 'vRealize Operations Manager', 'vCenter FQDN', vcenter_ip),
    ('Service', 'vRealize Operations Manager', 'vCenter Administrator Password', vcenter_password),
    ('Service', 'vRealize Operations Manager', 'vROPS Datacenter', datacenter),
    ('Service', 'vRealize Operations Manager', 'vROPS Datastore', sio_unified_datastore),
    ('Service', 'vRealize Operations Manager', 'vROPS Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'vRealize Operations Manager', 'vROPS admin Password', vcenter_password),
    ('Service', 'vRealize Operations Manager', 'Cloud vCenter Administrator Password', vcenter_password),
    ('Service', 'vRealize Operations Manager', 'app_vrops_vra Password', vcenter_password),
    ('Service', 'vRealize Operations Manager', 'Cloud vCenter FQDN', vcenter_ip),
    ('Service', 'vRealize Operations Manager', 'app_vrops_vcenter Password', vcenter_password),
    ('Service', 'vRealize Operations Manager', 'VNX Password', vcenter_password),
    ('Service', 'vRealize Operations Manager', 'vROPS Cluster', cluster3_name),

    ('Service', 'vRealize Log Insight', 'vCenter FQDN', vcenter_ip),
    ('Service', 'vRealize Log Insight', 'vCenter Administrator Password', vcenter_password),
    ('Service', 'vRealize Log Insight', 'Log Insight Datacenter', datacenter),
    ('Service', 'vRealize Log Insight', 'Log Insight Datastore', sio_unified_datastore),
    ('Service', 'vRealize Log Insight', 'Log Insight Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'vRealize Log Insight', 'Log Insight Admin Password', vcenter_password),
    ('Service', 'vRealize Log Insight', 'Cloud vCenter FQDN', vcenter_ip),
    ('Service', 'vRealize Log Insight', 'app_logi_vcenter Password', vcenter_password),
    ('Service', 'vRealize Log Insight', 'vROPS FQDN', vrops_ip),
    ('Service', 'vRealize Log Insight', 'vROPS admin Password', vcenter_password),
    ('Service', 'vRealize Log Insight', 'Log Insight Cluster', cluster3_name),

    ('Service', 'Nagios Registration', 'Nagios Machine IP Address', nagios_ip),
    ('Service', 'Nagios Monitoring', 'ESX Root Password', esx_root_password),
    ('Service', 'Nagios Monitoring', 'Nagios Datacenter', datacenter),
    ('Service', 'Nagios Monitoring', 'Nagios Datastore', vcenter_datastore),
    ('Service', 'Nagios Monitoring', 'Nagios IP', nagios_ip),
    ('Service', 'Nagios Monitoring', 'Nagios Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'Nagios Monitoring', 'vCenter Administrator Password', vcenter_password),
    ('Service', 'Nagios Monitoring', 'vCenter IP', vcenter_ip),
    ('Service', 'vCloud Director', 'vCenter IP', vcenter_ip),
    ('Service', 'vCloud Director', 'vCenter Administrator Password', vcenter_password),
    ('Service', 'vCloud Director', 'Datacenter', datacenter),
    ('Service', 'vCloud Director', 'Datastore', sio_unified_datastore),
    ('Service', 'vCloud Director', 'vCD Root Password', esx_root_password),
    ('Service', 'vCloud Director', 'vCD Management Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'vCloud Director', 'vCD VM Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'vCloud Director', 'vCD Administrator Password', esx_root_password),
    ('Service', 'vCloud Director', 'vShield Manager Address', nsx_manager_ip),
    ('Service', 'vCloud Director', 'vShield Manager Password', vcenter_password),
    ('Service', 'NSX Manager', 'vCenter IP', vcenter_ip),
    ('Service', 'NSX Manager', 'vCenter Administrator Password', vcenter_password),
    ('Service', 'NSX Manager', 'Controller Datastore', sio_unified_datastore),
    ('Service', 'NSX Manager', 'Controller Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'NSX Manager', 'Datastore', sio_unified_datastore),
    ('Service', 'NSX Manager', 'NSX Password', vcenter_password),
    ('Service', 'NSX Manager', 'NSX Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'NSX Manager', 'NSX SSO Password', vcenter_password),
    ('Service', 'Versa Director', 'vCenter Administrator Password', vcenter_password),
    ('Service', 'Versa Director', 'vCenter IP', vcenter_ip),
    ('Service', 'Versa Director', 'Versa Datacenter', datacenter),
    ('Service', 'Versa Director', 'Versa Datastore', sio_unified_datastore),
    ('Service', 'Versa Director', 'Versa Cluster', cluster2_name),
    ('Service', 'Versa Director', 'Versa SB VDS', vds1_name),
    ('Service', 'Versa Director', 'Versa Traffic VDS', vds1_name),
    ('Service', 'Versa Director', 'Versa SDWAN VDS', vds1_name),
    ('Service', 'Versa Director', 'Versa Director NB Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'Versa Director', 'Versa Analytics NB Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'Versa Director', 'Versa Controller NB Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'Versa Director', 'Versa Branch1 Cluster', cluster2_name),
    ('Service', 'Versa Director', 'Versa Branch1 NB Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'Versa Director', 'Versa Branch2 Cluster', cluster2_name),
    ('Service', 'Versa Director', 'Versa Branch2 NB Portgroup Name', emc_mgmt_portgroup),
    ('Service', 'Versa Director', 'Versa LEF DST IP', versa_analytics_sb_ip),
    ('Service', 'Versa Director', 'Versa LEF SRC IP', versa_controller_lan_ip),

    ('Service', 'vRealize Appliance', 'Datacenter', datacenter),
    ('Service', 'vRealize Appliance', 'Cluster', cluster2_name),
    ('Service', 'vRealize Appliance', 'vRA Datastore', sio_unified_datastore),
    ('Service', 'vRealize Appliance', 'vRA Disk Format', 'thin'),
    # ('Service', 'vRealize Appliance', 'vRA Hostname', vra_hostname),
    # ('Service', 'vRealize Appliance', 'vRA Root Password', vra_root_password),
    ('Service', 'vRealize Appliance', 'vRA Gateway IP', management_gateway),
    ('Service', 'vRealize Appliance', 'vRA Netmask', management_netmask),
    ('Service', 'vRealize Appliance', 'vRA Domain', management_search_domain),
    ('Service', 'vRealize Appliance', 'vRA DNS Search Path', management_search_domain),
    ('Service', 'vRealize Appliance', 'vRA DNS Server IP', ','.join([management_dns1, management_dns2])),
    ('Service', 'vRealize Appliance', 'vRA IP', vra_ip),
    ('Service', 'vRealize Appliance', 'vRA Portgroup Name', emc_mgmt_portgroup),
    # ('Service', 'vRealize Appliance', 'vRA VM Name', vra_vm_name),
]

dd = csapi.GetReservationDetails(resid).ReservationDescription

res2av = {}
alias2av = {}
for kind, model, attr, value in aa:
    if kind == 'Resource':
        for res in dd.Resources:
            if model == res.ResourceModelName:
                if res.Name not in res2av:
                    res2av[res.Name] = []
                if isinstance(value, dict):
                    v = value[res.Name]
                else:
                    v = value
                res2av[res.Name].append((attr, v))
    else:
        for svc in dd.Services:
            if model == svc.ServiceName:
                if svc.Alias not in alias2av:
                    alias2av[svc.Alias] = []
                alias2av[svc.Alias].append((attr, value))

# print str(res2av)
# print str(alias2av)

# csapi.SetAttributesValues([
#     ResourceAttributesUpdateRequest(res, [
#         AttributeNameValue(attr, value)
#         for attr, value in res2av[res]
#         if attr != 'ResourceAddress'
#     ])
#     for res in res2av
# ])
# for res in res2av:
#     for attr, value in res2av[res]:
#         if attr == 'ResourceAddress':
#             csapi.UpdateResourceAddress(res, value)

for res in res2av:
    for attr, value in res2av[res]:
        if attr == 'ResourceAddress':
            csapi.UpdateResourceAddress(res, value)
        else:
            csapi.SetAttributeValue(res, attr, value)

for alias in alias2av:
    csapi.SetServiceAttributesValues(resid, alias, [
        AttributeNameValue(attr, value)
        for attr, value in alias2av[alias]
        ])
