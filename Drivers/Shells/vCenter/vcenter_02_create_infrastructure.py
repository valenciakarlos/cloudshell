# service "vCenter"

from vCenterCommon import *
import json
import time
import os
from quali_remote import powershell

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

# VC Params
vcenter_ip = attrs['vCenter IP']
vcenter_username = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']

# ESXi Info
esx_username = attrs['vCenter ESXi Username']
esx_password = attrs['vCenter ESXi Password']
# VC Infra Params

datacenter_name = attrs['vCenter Datacenter Name']

cluster1 = attrs['vCenter Cluster1 Name']
cluster2 = attrs['vCenter Cluster2 Name']
cluster3 = attrs['vCenter Cluster3 Name']
cluster4 = attrs['vCenter Cluster4 Name']
cluster5 = attrs['vCenter Cluster5 Name']

cluster1_esxi = attrs['vCenter Cluster1 ESXis']
cluster2_esxi = attrs['vCenter Cluster2 ESXis']
cluster3_esxi = attrs['vCenter Cluster3 ESXis']
cluster4_esxi = attrs['vCenter Cluster4 ESXis']
cluster5_esxi = attrs['vCenter Cluster5 ESXis']

cluster1_drs = attrs['vCenter Cluster1 DRS']
cluster2_drs = attrs['vCenter Cluster2 DRS']
cluster3_drs = attrs['vCenter Cluster3 DRS']
cluster4_drs = attrs['vCenter Cluster4 DRS']
cluster5_drs = attrs['vCenter Cluster5 DRS']

cluster1_ha = attrs['vCenter Cluster1 HA']
cluster2_ha = attrs['vCenter Cluster2 HA']
cluster3_ha = attrs['vCenter Cluster3 HA']
cluster4_ha = attrs['vCenter Cluster4 HA']
cluster5_ha = attrs['vCenter Cluster5 HA']

clusters = [
    [cluster1,cluster1_esxi,cluster1_ha,cluster1_drs],
    [cluster2,cluster2_esxi,cluster2_ha,cluster2_drs],
    [cluster3,cluster3_esxi,cluster3_ha,cluster3_drs],
    [cluster4,cluster4_esxi,cluster4_ha,cluster4_drs],
    [cluster5,cluster5_esxi,cluster5_ha,cluster5_drs]
    ]


def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

#Init Params
vcenterparams = {
    'IP': vcenter_ip,
    'user': vcenter_username,
    'password': vcenter_password}


#Set VC session
session = Vcenter(vcenterparams)

#Create DC
session.create_datacenter(datacenter_name)
# STEPS # Catch already exists exception

#Create Clusters
for cluster in clusters:
    if cluster[0] != '':
        session.create_cluster(cluster[0], datacenter_name, str2bool(cluster[3]), 'manual', str2bool(cluster[2]))
        # STEPS # Catch already exists exception

#Add ESXi to Cluster
for cluster in clusters:
    if cluster[0] != '':
        esxi = cluster[1].split(',')
        for e in esxi:
            #Get Thumbprint
            tp = session.getsslThumbprint(e)
            session.add_host(cluster[0], e, tp, esx_username, esx_password)
            # STEPS # Catch already added exception


# exit maintenance mode for all the vcenter hosts
powershell('''
Add-PSSnapin VMware.VimAutomation.Core
Connect-VIServer ''' + vcenter_ip + ''' -User ''' + vcenter_username + ''' -Password ''' + vcenter_password + '''

Get-VMHost | Set-VMHost -State Connected

<#$VMHost = Get-VMHost
$storMgr = Get-View $VMHost.ExtensionData.ConfigManager.DatastoreSystem

$i = 2
$storMgr.QueryAvailableDisksForVmfs($null) | %{
  New-Datastore -name datastore$i -vmfs -path $_.CanonicalName
  $i = $i+1
}#>

''')
