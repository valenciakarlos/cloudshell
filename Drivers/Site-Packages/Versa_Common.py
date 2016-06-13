
from vCenterCommon import *


def addAdapter(vmname, networks, vcenter_ip, vcenter_user, vcenter_password):
    #Skip First Adaptor (####ETH1) (already existing)
    tempnet = ''
    try:
        tempnet = networks['eth0'][1]
    except Exception, e:
        tempnet = tempnet[:-1]
        pass
    try:
        tempnet += ','
        tempnet += networks['eth2'][1]
    except Exception, e:
        tempnet = tempnet[:-1]
        pass
    try:
        tempnet += ','
        tempnet += networks['eth3'][1]
    except Exception, e:
        tempnet = tempnet[:-1]
        pass
    try:
        tempnet += ','
        tempnet += networks['eth4'][1]
    except Exception, e:
        tempnet = tempnet[:-1]
        pass

    script = '''Add-PSSnapin VMware.VimAutomation.Core\n
    Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue \n'''
    networks = tempnet.split(',')
    for network in networks:
        script += '''New-NetworkAdapter -NetworkName "''' + network + '''" -VM "''' + vmname + '''" -StartConnected -Type "e1000" \n'''
    powershell(script)

def firstEth(netconf):
    script = '''"echo 'auto lo `n iface lo inet loopback `n'''
    for eth in netconf:
        if eth == 'eth0':
            script += '''auto '''  + eth + ''' `n iface ''' + eth + ''' inet static `n hwaddress ether ''' + netconf[eth][5] + '''`n address ''' + netconf[eth][0] + ''' `n netmask ''' + netconf[eth][2] + ''' `n gateway ''' + netconf[eth][3] + ''' `n dns-nameservers ''' + netconf[eth][4] + '''`n'''
    return(script)


def addEth(netconf):
    script = ''
    for eth in netconf:
        if eth != 'eth0':
            script += '''auto '''  + eth + ''' `n iface ''' + eth + ''' inet static `n hwaddress ether ''' + netconf[eth][5] + '''`n address ''' + netconf[eth][0] + ''' `n netmask ''' + netconf[eth][2] + ''' `n gateway ''' + netconf[eth][3] + ''' `n dns-nameservers ''' + netconf[eth][4] + '''`n'''
    return(script)



def setAdapterMAC(vmname, vmnetwrokinfo, vcenter_ip, vcenter_user, vcenter_password):
    macs =  getAdapterMac(vmname, vcenter_ip, vcenter_user, vcenter_password)
    n = 0
    for x in reversed(macs):
        eth = "eth" + str(n)
        n += 1
        temp =  vmnetwrokinfo[eth]
        temp = temp + (x,)
        vmnetwrokinfo[eth] = temp
    return vmnetwrokinfo


def addRoute(vm_gw, cont_ip='', cont_netmask='', cont_network=''):
    script = '''up route add default gw ''' + vm_gw + '''`n'''
    if cont_ip != '':
        script += '''up route add -net ''' + cont_network + ''' netmask ''' + cont_netmask + ''' gw ''' + cont_ip + ''' dev eth1'''

    return (script)


def invokeScript(script, vmname, vmuser, vmpass, retry, delay, vcenter_ip, vcenter_user, vcenter_password):
    start = '''Add-PSSnapin VMware.VimAutomation.Core\n
    Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue\n'''
    script += ''
    script = start + 'Invoke-VMScript -ScriptText ' + script + ''' -VM "''' + vmname + '''" -GuestUser ''' + vmuser + ''' -GuestPassword ''' + vmpass
    while retry > 0:
        try:
            ans = powershell(script)
            if not 'error' in ans.lower():
                retry = 0
                finish = True
                return ans
            else:
                retry += -1
                time.sleep(delay)
                finish = ans
        except Exception, e:
            retry += -1
            time.sleep(delay)
            finish = e.message
    if finish is not True:
        raise Exception(finish)





#Controller\Branches
def addNFVAdapter(vmname, networks, vcenter_ip, vcenter_user, vcenter_password):
    #Skip First Adaptor (already existing)
    tempnet = ''
    try:
        tempnet = networks['eth1'][1]
    except Exception, e:
        tempnet = tempnet[:-1]
        pass
    try:
        tempnet += ','
        tempnet += networks['eth2'][1]
    except Exception, e:
        tempnet = tempnet[:-1]
        pass
    try:
        tempnet += ','
        tempnet += networks['eth3'][1]
    except Exception, e:
        tempnet = tempnet[:-1]
        pass
    try:
        tempnet += ','
        tempnet += networks['eth4'][1]
    except Exception, e:
        tempnet = tempnet[:-1]
        pass

    script = '''Add-PSSnapin VMware.VimAutomation.Core\n
    Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue \n'''
    networks = tempnet.split(',')
    for network in networks:
        script += '''New-NetworkAdapter -NetworkName "''' + network + '''" -VM "''' + vmname + '''" -StartConnected -Type "e1000" \n'''
    powershell(script)

def firstNFVEth(vmname, vmuser, vmpass, netconf, retry, delay, vcenter_ip, vcenter_user, vcenter_password):
    script = '''Add-PSSnapin VMware.VimAutomation.Core\n
    Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue\n
    Invoke-VMScript -ScriptText "echo \'''' + vmpass +  '''\' | sudo chmod 777 /etc/network/interfaces" -VM "''' + vmname + '''" -GuestUser ''' + vmuser + ''' -GuestPassword ''' + vmpass + '''\n
    Invoke-VMScript -ScriptText "echo \'''' + vmpass +  '''\' | sudo -S chmod 777 /etc/network/interfaces" -VM "''' + vmname + '''" -GuestUser ''' + vmuser + ''' -GuestPassword ''' + vmpass + '''\n
    Invoke-VMScript -ScriptText "echo 'auto lo `n iface lo inet loopback' > /etc/network/interfaces" -VM "''' + vmname + '''" -GuestUser ''' + vmuser + ''' -GuestPassword ''' + vmpass + '''\n'''
    for eth in netconf:
        if eth == 'eth0':
            script += '''Invoke-VMScript -ScriptText "echo 'auto '''  + eth + ''' `n iface ''' + eth + ''' inet static `n hwaddress ether ''' + netconf[eth][5] + ''' `n address ''' + netconf[eth][0] + ''' `n netmask ''' + netconf[eth][2] + ''' `n gateway ''' + netconf[eth][3] + ''' `n dns-nameservers ''' + netconf[eth][4] +  ''' `n #EOF' >> /etc/network/interfaces" -VM "''' + vmname + '''" -GuestUser ''' + vmuser + ''' -GuestPassword ''' + vmpass + '''\n'''
    while retry > 0:
        try:
            ans = powershell(script)
            if not 'error' in ans.lower():
                retry = 0
                finish = True
            else:
                retry += -1
                time.sleep(delay)
                finish = ans
        except Exception, e:
            retry += -1
            time.sleep(delay)
            finish = e.message
    if finish is not True:
        raise Exception(finish)

def addNFVEth(vmname, vmuser, vmpass, netconf):
    script = '''Add-PSSnapin VMware.VimAutomation.Core\n
    Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue\n'''
    for eth in netconf:
        if eth != 'eth0':
            script += '''Invoke-VMScript -ScriptText "echo 'auto '''  + eth + ''' `n iface ''' + eth + ''' inet static `n hwaddress ether ''' + netconf[eth][5] + ''' `n address ''' + netconf[eth][0] + ''' `n netmask ''' + netconf[eth][2] + ''' `n gateway ''' + netconf[eth][3] + ''' `n dns-nameservers ''' + netconf[eth][4] + '''' >> /etc/network/interfaces" -VM "''' + vmname + '''" -GuestUser ''' + vmuser + ''' -GuestPassword ''' + vmpass + '''\n'''
    powershell(script)



