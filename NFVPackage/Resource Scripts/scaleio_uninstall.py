# service "ScaleIO"

import os
import time
import json
import sys
from vCenterCommon import deleteVMs, vmPower
from SIOCommon import getSIOesxs
from quali_remote import powershell, quali_enter, quali_exit

quali_enter(__file__)

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

vcenter_ip = attrs['vCenter IP']
vcenter_user = attrs['vCenter Username']
vcenter_password = attrs['vCenter Password']


#delete scale io datastore
sio_storage_name = attrs['Unified Datastore']
datacenter = attrs['Datacenter']
esx_excludes = attrs['Exclude ESXs From SDC Role']
sio_svm_cluster = attrs['ScaleIO Cluster']
esxs = getSIOesxs(vcenter_ip, vcenter_user, vcenter_password, datacenter, esx_excludes, sio_svm_cluster)
esxs.pop()
esx_for_Storage = esxs[0].split(",")[0]
script = '''Add-PSSnapin VMware.VimAutomation.Core

Function Get-DatastoreMountInfo {
	[CmdletBinding()]
	Param (
		[Parameter(ValueFromPipeline=$true)]
		$Datastore
	)
	Process {
		$AllInfo = @()
		if (-not $Datastore) {
			$Datastore = Get-Datastore
		}
		Foreach ($ds in $Datastore) {  
			if ($ds.ExtensionData.info.Vmfs) {
				$hostviewDSDiskName = $ds.ExtensionData.Info.vmfs.extent[0].diskname
				if ($ds.ExtensionData.Host) {
					$attachedHosts = $ds.ExtensionData.Host
					Foreach ($VMHost in $attachedHosts) {
						$hostview = Get-View $VMHost.Key
						$hostviewDSState = $VMHost.MountInfo.Mounted
						$StorageSys = Get-View $HostView.ConfigManager.StorageSystem
						$devices = $StorageSys.StorageDeviceInfo.ScsiLun
						Foreach ($device in $devices) {
							$Info = "" | Select Datastore, VMHost, Lun, Mounted, State
							if ($device.canonicalName -eq $hostviewDSDiskName) {
								$hostviewDSAttachState = ""
								if ($device.operationalState[0] -eq "ok") {
									$hostviewDSAttachState = "Attached"							
								} elseif ($device.operationalState[0] -eq "off") {
									$hostviewDSAttachState = "Detached"							
								} else {
									$hostviewDSAttachState = $device.operationalstate[0]
								}
								$Info.Datastore = $ds.Name
								$Info.Lun = $hostviewDSDiskName
								$Info.VMHost = $hostview.Name
								$Info.Mounted = $HostViewDSState
								$Info.State = $hostviewDSAttachState
								$AllInfo += $Info
							}
						}
						
					}
				}
			}
		}
		$AllInfo
	}
}

Function Unmount-Datastore {
	[CmdletBinding()]
	Param (
		[Parameter(ValueFromPipeline=$true)]
		$Datastore
	)
	Process {
		if (-not $Datastore) {
			Write-Host "No Datastore defined as input"
			Exit
		}
		Foreach ($ds in $Datastore) {
			$hostviewDSDiskName = $ds.ExtensionData.Info.vmfs.extent[0].Diskname
			if ($ds.ExtensionData.Host) {
				$attachedHosts = $ds.ExtensionData.Host
				Foreach ($VMHost in $attachedHosts) {
					$hostview = Get-View $VMHost.Key
					$StorageSys = Get-View $HostView.ConfigManager.StorageSystem
					Write-Host "Unmounting VMFS Datastore $($DS.Name) from host $($hostview.Name)..."
					$StorageSys.UnmountVmfsVolume($DS.ExtensionData.Info.vmfs.uuid);
				}
			}
		}
	}
}

        Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue
        Get-Datastore ''' + sio_storage_name + ''' | Unmount-Datastore
        Remove-Datastore -Datastore ''' + sio_storage_name + ''' -VMHost ''' + esx_for_Storage + ''' -Confirm:$false
        '''
out = powershell(script)
if 'not' in out:
    print out
    sys.exit(1)


#delete vms
vm_name_prefix = attrs['ScaleIO SVM Name PreFix'] + '*'
vmPower(vm_name_prefix, 'stop', vcenter_ip, vcenter_user, vcenter_password)
deleteVMs(vm_name_prefix, vcenter_ip, vcenter_user, vcenter_password)

quali_exit(__file__)