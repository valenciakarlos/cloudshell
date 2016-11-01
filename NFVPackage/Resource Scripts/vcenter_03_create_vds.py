# service "vCenter"

from vCenterCommon import *
import json
import os
import time
import sys

from quali_remote import quali_enter, quali_exit, qs_trace, qs_info
quali_enter(__file__)

# with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
#     f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(
#         os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']
vcenter_ip = attrs['vCenter IP']
vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']
esx_user = attrs['vCenter ESXi Username']
esx_password = attrs['vCenter ESXi Password']
datacenter = attrs['vCenter Datacenter Name']
vds1_name = attrs['VDS1 Name']
vds1_hosts = attrs['VDS1 Hosts']
vds1_hosts172 = attrs['VDS1 Hosts PXE IPs']
vds1_vnics = attrs['VDS1 Hosts VNICS']
vds1_version = attrs['VDS1 Version']
vds1_portgroup = attrs['VDS1 Port Group Name']
vds1_num_ports = attrs['VDS1 Num Uplink Ports']
if not vds1_num_ports:
    vds1_num_ports = '32'
vds1_vlanmode = attrs['VDS1 Port Group VLAN Type']
vds1_vlan_ids = attrs['VDS1 Port Group VLAN IDs']
vds1_ips = attrs['VDS1 Kernel IPs']
vds1_subnet = attrs['VDS1 Kernel Subnet']

vds2_name = attrs['VDS2 Name']
vds2_hosts = attrs['VDS2 Hosts']
vds2_vnics = attrs['VDS2 Hosts VNICS']
vds2_version = attrs['VDS2 Version']
vds2_portgroup = attrs['VDS2 Port Group Name']
vds2_num_ports = attrs['VDS2 Num Uplink Ports']
if not vds2_num_ports:
    vds2_num_ports = '32'
vds2_vlanmode = attrs['VDS2 Port Group VLAN Type']
vds2_vlan_ids = attrs['VDS2 Port Group VLAN IDs']
vds2_ips = attrs['VDS2 Kernel IPs']
vds2_subnet = attrs['VDS2 Kernel Subnet']

vds3_name = attrs['VDS3 Name']
vds3_hosts = attrs['VDS3 Hosts']
vds3_vnics = attrs['VDS3 Hosts VNICS']
vds3_version = attrs['VDS3 Version']
vds3_portgroup = attrs['VDS3 Port Group Name']
vds3_num_ports = attrs['VDS3 Num Uplink Ports']
if not vds3_num_ports:
    vds3_num_ports = '32'
vds3_vlanmode = attrs['VDS3 Port Group VLAN Type']
vds3_vlan_ids = attrs['VDS3 Port Group VLAN IDs']
vds3_ips = attrs['VDS3 Kernel IPs']
vds3_subnet = attrs['VDS3 Kernel Subnet']

vds4_name = attrs['VDS4 Name']
vds4_hosts = attrs['VDS4 Hosts']
vds4_vnics = attrs['VDS4 Hosts VNICS']
vds4_version = attrs['VDS4 Version']
vds4_portgroup = attrs['VDS4 Port Group Name']
vds4_num_ports = attrs['VDS4 Num Uplink Ports']
if not vds4_num_ports:
    vds4_num_ports = '32'
vds4_vlanmode = attrs['VDS4 Port Group VLAN Type']
vds4_vlan_ids = attrs['VDS4 Port Group VLAN IDs']
vds4_ips = attrs['VDS4 Kernel IPs']
vds4_subnet = attrs['VDS4 Kernel Subnet']

vds5_name = attrs['VDS5 Name']
vds5_hosts = attrs['VDS5 Hosts']
vds5_vnics = attrs['VDS5 Hosts VNICS']
vds5_version = attrs['VDS5 Version']
vds5_portgroup = attrs['VDS5 Port Group Name']
vds5_num_ports = attrs['VDS5 Num Uplink Ports']
if not vds5_num_ports:
    vds5_num_ports = '32'
vds5_vlanmode = attrs['VDS5 Port Group VLAN Type']
vds5_vlan_ids = attrs['VDS5 Port Group VLAN IDs']
vds5_ips = attrs['VDS5 Kernel IPs']
vds5_subnet = attrs['VDS5 Kernel Subnet']


# example values
# vcenter_ip = '10.10.111.32'
# vcenter_user = 'administrator@vsphere.local'
# vcenter_password = 'Welcome1!'
# datacenter = 'vmworlddemo'
# mill = int(round(time.time() * 1000))
# vds1_name = 'vds_%d' % mill
# vds1_hosts = '10.10.111.26,10.10.111.23,10.10.111.22'
# vds1_vnics = 'vmnic3,vmnic1;vmnic1;vmnic1,vmnic3'
# vds1_version = '6.0.0'
# vds1_portgroup = 'vds_%d_pg1' % mill
# vds1_num_ports = '4'
# vds1_vlanmode = 'trunk'
# vds1_vlan_ids = '1,2,5,100-110,60,150,400'


# Build donor physical nic list for powershell
# nics = []
# donor_vnics = ''
# if len(vds2_vnics.split(';')) == 1 and len(vds1_hosts.split(',')) > 1:
#     nics = vds2_vnics.split(';') * len(vds1_hosts.split(','))
#     for nic in nics:
#         donor_vnics += nic + ';'
#     donor_vnics = donor_vnics[:-1]
# else:
#     donor_vnics = vds2_vnics

# Create VDS 1 (MGMT) using PowerCLI and migrate physical NICs to it. (vmnic1)
# script = '''
# Add-PSSnapin VMware.VimAutomation.Core
# import-module VMware.VimAutomation.vds
# $vcip = \'''' + vcenter_ip + '''\'
# $vcuser = \'''' + vcenter_user + '''\'
# $vcpass = \'''' + vcenter_password + '''\'
# $vmhost_array = \'''' + vds1_hosts + '''\'
# $vds_name = \'''' + vds1_name + '''\'
# $dcname = \'''' + datacenter + '''\'
# $portgroupname = \'''' + vds1_portgroup + '''\'
# $pnics = \'''' + donor_vnics + '''\'
# $pnicesx = @()
# foreach ($pnc in $pnics.split(';')){
#     $pnicesx += $pnc.split(',')[0]
# }
# Connect-VIServer $vcip -user $vcuser -password $vcpass
#
#
# Write-Host "`nCreating new VDS" $vds_name
# $vds = New-VDSwitch -Name $vds_name -Location (Get-Datacenter -Name $dcname)
#
#
# Write-Host "Creating new Management DVPortgroDVPortgroup"
# New-VDPortgroup -Name $portgroupname -Vds $vds | Out-Null
# $num = 0
# foreach ($vmhost in $vmhost_array.split(",")) {
#     if ($vmhost -ne ''){
#         # Add ESXi host to VDS
#         Write-Host "Adding" $vmhost "to" $vds_name
#         $vds | Add-VDSwitchVMHost -VMHost $vmhost | Out-Null
#         # add donor pnic to vSwitch1
#         $myVMHostNetworkAdapter = Get-VMhost $vmhost | Get-VMHostNetworkAdapter -Physical -Name $pnicesx[$num]
#         $vss = Get-VirtualSwitch -VMHost $vmhost -name vSwitch1
#         Add-VirtualSwitchPhysicalNetworkAdapter -VMHostPhysicalNic $myVMHostNetworkAdapter -virtualswitch $vss -Confirm:$false
#         sleep 5
#         # Set NicTeamingPolicy
#         $policy = Get-NicTeamingPolicy -VirtualSwitch $vss
#         $nic0 = Get-VMHost $vmhost | Get-VMHostNetworkAdapter -Physical -Name vmnic1
#         $nicn = Get-VMHost $vmhost | Get-VMHostNetworkAdapter -Physical -Name $pnicesx[$num]
#         Set-NicTeamingPolicy -MakeNicActive $nicn -VirtualSwitchPolicy $policy
#         Set-NicTeamingPolicy -MakeNicStandby $nic0 -VirtualSwitchPolicy $policy
#         sleep 5
#         # Migrate pNIC to VDS (vmnic1)
#         Write-Host "Adding vmnic1 to" $vds_name
#         $vmhostNetworkAdapter = Get-VMHost $vmhost | Get-VMHostNetworkAdapter -Physical -Name vmnic1
#         $vds | Add-VDSwitchPhysicalNetworkAdapter -VMHostNetworkAdapter $vmhostNetworkAdapter -Confirm:$false
#         sleep 5
#         # Migrate VMkernel interfaces to VDS
#         $mgmt_portgroup = $portgroupname
#         Write-Host "Migrating" $mgmt_portgroup "to" $vds_name
#         $dvportgroup = Get-VDPortgroup -name $mgmt_portgroup -VDSwitch $vds
#         $vmk = Get-VMHostNetworkAdapter -Name vmk0 -VMHost $vmhost
#         Set-VMHostNetworkAdapter -PortGroup $dvportgroup -VirtualNic $vmk -confirm:$false | Out-Null
#         sleep 5
#         # Migrate VMs using old network name
#         foreach ($vm in Get-VM -Location $vmhost){
#             foreach($ada in Get-networkadapter -vm $vm){
#                 if ($ada.NetworkName -eq "VM Network"){
#                     try {
#                         Set-NetworkAdapter -NetworkAdapter $ada -NetworkName $dvportgroup -Confirm:$false
#                     }
#                     catch {
#                     sleep 300
#                         Connect-VIServer $vcip -user $vcuser -password $vcpass
#                     }
#                 }
#             }
#         }
#
#
#         # Remove old vSwitch
#         Write-Host "Removing vSwitch " $vswitch
#         Remove-VirtualSwitch -VirtualSwitch $vss -Confirm:$false
#         $num += 1
#     }
# }
# '''

script = '''
Add-PSSnapin VMware.VimAutomation.Core
import-module VMware.VimAutomation.vds
$vcip = \'''' + vcenter_ip + '''\'
$vcuser = \'''' + vcenter_user + '''\'
$vcpass = \'''' + vcenter_password + '''\'
$esxuser = \'''' + esx_user + '''\'
$esxpass = \'''' + esx_password + '''\'
$vmhost_array = \'''' + vds1_hosts + '''\'
$vmhost_array172 = \'''' + vds1_hosts172 + '''\'
$vds_name = \'''' + vds1_name + '''\'
$dcname = \'''' + datacenter + '''\'
$portgroupname = \'''' + vds1_portgroup + '''\'
# foreach ($pnc in $pnics.split(';')){
#     $pnicesx += $pnc.split(',')[0]
# }

Connect-VIServer $vcip -user $vcuser -password $vcpass  -force:$true -savecredentials:$false

Write-Host "`nCreating new VDS" $vds_name
New-VDSwitch -Name $vds_name -Location (Get-Datacenter -Name $dcname)

$vds = get-vdswitch $vds_name
Write-Host "Creating temporary ephemeral dvportgroup qstempdpg"

# dvportgroup must be ephemeral to be controlled by PowerCLI connected directly to the ESXi
New-VDPortgroup -Name $portgroupname -Vds $vds -PortBinding Ephemeral | Out-Null

foreach ($vmhost in $vmhost_array.split(",")) {
    if ($vmhost -ne ''){
        Write-Host "Adding" $vmhost "to" $vds_name
        $vds | Add-VDSwitchVMHost -VMHost $vmhost | Out-Null
    }
}
Disconnect-VIServer -confirm:$false

foreach ($vmhost172 in $vmhost_array172.split(",")) {
    Write-Host "Migrating ESXi $vmhost172 to distributed switch"
    write-host "Connect-VIServer $vmhost172 -user $esxuser -password $esxpass  -force:`$true -savecredentials:`$false"
    Connect-VIServer $vmhost172 -user $esxuser -password $esxpass  -force:$true -savecredentials:$false

    Write-Host "Moving vmk1 from vSwitch1 to $vds_name portgroup $portgroupname"
    $a=Get-VDPortgroup $portgroupname
    $a
    $b=get-vmhost | Get-VMHostNetworkAdapter -VMKernel -name vmk1
    $b
    Set-VMHostNetworkAdapter -PortGroup $a -VirtualNic $b -Confirm:$false

    Write-Host "Adding vmnic1 to $vds_name"
    $c=get-vmhost | Get-VMHostNetworkAdapter -Physical -Name vmnic1
    Get-VDSwitch |  Add-VDSwitchPhysicalNetworkAdapter -VMHostNetworkAdapter $c -confirm:$false

    foreach ($vm in Get-VM){
        foreach($ada in Get-networkadapter -vm $vm){
            if ($ada.NetworkName -eq "VM Network"){
                Write-Host "Migrating $vm from VM Network to $portgroupname"
                try {
                    Set-NetworkAdapter -NetworkAdapter $ada -NetworkName $portgroupname -Confirm:$false
                } catch {
                    Write-Host "Exception: $_.Exception.Message"
                    Write-Host "Failsafe - got disconnected when migrating $vm to $portgroupname, waiting 2 minutes"
                    sleep 120
                    Connect-VIServer $vmhost172 -user $esxuser -password $esxpass  -force:$true -savecredentials:$false
                }
            }
        }
    }
    # Write-Host "Removing vSwitch1"
    # Remove-VirtualSwitch -VirtualSwitch vSwitch1 -Confirm:$false

    Disconnect-VIServer -confirm:$false
}

# Connect-VIServer $vcip -user $vcuser -password $vcpass -force:$true -savecredentials:$false

# Write-Host "Creating new Management DVPortgroup"
# New-VDPortgroup -Name $portgroupname -Vds $vds | Out-Null
#
# foreach ($vm in Get-VM){
#     foreach($ada in Get-networkadapter -vm $vm){
#         if ($ada.NetworkName -eq "qstempdpg"){
#             try{
#                 Write-Host "Migrating $vm from qstempdpg to $portgroupname"
#                 Set-NetworkAdapter -NetworkAdapter $ada -NetworkName $portgroupname -Confirm:$false
#             } catch {
#                 sleep 10
#                 Connect-VIServer $vcip -user $vcuser -password $vcpass
#             }
#         }
#     }
# }

'''

# try:
print powershell(script)
# except Exception, e:
#     print e

# try:
vcenterparams = {
    'IP': vcenter_ip,
    'user': vcenter_user,
    'password': vcenter_password}

# Set VC session
session = Vcenter(vcenterparams)

#if vds1_name:
#    # Create DV Switch
#    dv_switch = session.create_dvSwitch(datacenter, vds1_name, vds1_version, int(vds1_num_ports), vds1_hosts.split(','), vds1_vnics.split(';'))
#    # Add port group to this switch
#    session.add_dvPort_group(dv_switch, vds1_portgroup, int(vds1_num_ports), vds1_vlanmode, vds1_vlan_ids)

if vds2_name:
    # Create DV Switch
    dv_switch = session.create_dvSwitch(datacenter, vds2_name, vds2_version, int(vds2_num_ports), vds2_hosts.split(','), vds2_vnics.split(';'))
    # STEPS # Catch already exists exception, log that it was skipped
    # Add port group to this switch
    session.add_dvPort_group(dv_switch, vds2_portgroup, int(vds2_num_ports), vds2_vlanmode, vds2_vlan_ids)
    # STEPS # Catch already exists exception
    if vds2_ips:
        addVMKernel(vds2_hosts, vds2_ips, vds2_subnet, vds2_name, vds2_portgroup, vcenter_ip, vcenter_user, vcenter_password)
        # STEPS # Catch already exists exception, see if it can add only new hosts
if vds3_name:
    # Create DV Switch
    dv_switch = session.create_dvSwitch(datacenter, vds3_name, vds3_version, int(vds3_num_ports), vds3_hosts.split(','), vds3_vnics.split(';'))
    # STEPS # Catch already exists exception
    # Add port group to this switch
    session.add_dvPort_group(dv_switch, vds3_portgroup, int(vds3_num_ports), vds3_vlanmode, vds3_vlan_ids)
    # STEPS # Catch already exists exception
    if vds3_ips:
        addVMKernel(vds3_hosts, vds3_ips, vds3_subnet, vds3_name, vds3_portgroup, vcenter_ip, vcenter_user, vcenter_password)
        # STEPS # Catch already exists exception, see if it can add only new hosts
if vds4_name:
    # Create DV Switch
    dv_switch = session.create_dvSwitch(datacenter, vds4_name, vds4_version, int(vds4_num_ports), vds4_hosts.split(','), vds4_vnics.split(';'))
    # STEPS # Catch already exists exception
    # Add port group to this switch
    session.add_dvPort_group(dv_switch, vds4_portgroup, int(vds4_num_ports), vds4_vlanmode, vds4_vlan_ids)
    # STEPS # Catch already exists exception
    if vds4_ips:
        addVMKernel(vds4_hosts, vds4_ips, vds4_subnet, vds4_name, vds4_portgroup, vcenter_ip, vcenter_user, vcenter_password)
        # STEPS # Catch already exists exception, see if it can add only new hosts
if vds5_name:
    # Create DV Switch
    dv_switch = session.create_dvSwitch(datacenter, vds5_name, vds5_version, int(vds5_num_ports),
                                        vds5_hosts.split(','), vds5_vnics.split(';'))
    # STEPS # Catch already exists exception
    # Add port group to this switch
    session.add_dvPort_group(dv_switch, vds5_portgroup, int(vds5_num_ports), vds5_vlanmode, vds5_vlan_ids)
    # STEPS # Catch already exists exception
    if vds5_ips:
        addVMKernel(vds5_hosts, vds5_ips, vds5_subnet, vds5_name, vds5_portgroup, vcenter_ip, vcenter_user,
                    vcenter_password)
        # STEPS # Catch already exists exception, see if it can add only new hosts
# except Exception, e:
#     print "Caught exception: %s" % str(e)
#     sys.exit(1)
#
quali_exit(__file__)
