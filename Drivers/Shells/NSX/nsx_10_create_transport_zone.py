# service "NSX Manager"

#
# # demo
# import time
# time.sleep(3)
# print 'Executed ' + __file__.split('\\')[-1].replace('.py', '')
# exit()
# # /demo


import json
import os
import time

from quali_remote import *
from NSX_Common import *
with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

nsx_ip = attrs['NSX IP']
nsx_user = attrs['NSX Username']
nsx_password = attrs['NSX Password']

vcenter_ip = attrs['vCenter IP']
vcenter_user = attrs['vCenter Administrator Username']
vcenter_password = attrs['vCenter Administrator Password']


tz_name = attrs['Transport Zone Name']
tz_description = attrs['Transport Zone Description']

datacenter_name = attrs['Datacenter']
edge_cluster = attrs['Controller Cluster']
compute_cluster = attrs['Compute Cluster']

datacenter_moref, cluster_csv_morefs = powershell('''
Add-PSSnapin VMware.VimAutomation.Core
Connect-VIServer ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + '''

$a1 = (get-datacenter | where { $_.Name -eq "''' + datacenter_name + '''" } | get-view).MoRef.Value

$a2 = ''

$cl = (get-cluster | where { $_.Name -eq "''' + compute_cluster + '''" })
if(($cl | Measure).Count -eq 0) {
    $cl = (get-resourcepool | where { $_.Name -eq "''' + compute_cluster + '''" })
}
$a2 += ($cl | get-view).MoRef.Value
$a2 += ','
$cl = (get-cluster | where { $_.Name -eq "''' + edge_cluster + '''" })
if(($cl | Measure).Count -eq 0) {
    $cl = (get-resourcepool | where { $_.Name -eq "''' + edge_cluster + '''" })
}
$a2 += ($cl | get-view).MoRef.Value

write-host '<%<%', $a1, $a2
''').split('<%<%')[1].strip().split(' ')


rest_api_query('''https://''' + nsx_ip + '''/api/2.0/vdn/scopes''', nsx_user, nsx_password, 'post', '''
<vdnScope>
    <name>''' + tz_name + '''</name>
    <description>''' + tz_description + '''</description>
    <clusters>
''' + (

    '\n'.join(['''
    <cluster>
        <cluster>
            <objectId>''' + cluster_moref + '''</objectId>
        </cluster>
   </cluster>''' for cluster_moref in set(cluster_csv_morefs.split(','))])

) + '''
    </clusters>
    <controlPlaneMode>UNICAST_MODE</controlPlaneMode>
</vdnScope>
''')
