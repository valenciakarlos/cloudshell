
import os
import re
from vCenterCommon import *
from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']
vcenter_ip = attrs['vCenter IP']

versa_dir_ip = attrs['Versa Director NB IP']
versa_username = 'Administrator' #attrs['Versa Username']
versa_password = 'versa123' #attrs['Versa Password']
analytics_ip = attrs['Versa Analytics NB IP']
mgmt_gw = attrs['Versa Director NB Gateway']
analytics_sb_ip = attrs['Versa Analytics SB IP']
br1_ip = attrs['Versa Branch1 NB IP']
br2_ip = attrs['Versa Branch2 NB IP']
#Controller config
#eth 0
controller_portgroup = attrs['Versa Controller NB Portgroup Name']
controller_vmname = attrs['Versa Controller VM Name']
controller_ova_path = attrs['Versa Controller Path']
controller_ip = attrs['Versa Controller NB IP']
controller_dns = attrs['Versa Controller NB DNS']
controller_mask = attrs['Versa Controller NB Mask']
controller_gateway = attrs['Versa Controller NB Gateway']
controller_eth = 'eth0'
#Branch1 config
#eth 0
branch1_portgroup = attrs['Versa Branch1 NB Portgroup Name']
branch1_vmname = attrs['Versa Branch1 VM Name']
branch1_ip = attrs['Versa Branch1 NB IP']
branch1_dns = attrs['Versa Branch1 NB DNS']
branch1_mask = attrs['Versa Branch1 NB Mask']
branch1_gateway = attrs['Versa Branch1 NB Gateway']
branch1_eth = 'eth0'
#Branch2 config
#eth 0
branch2_vmname = attrs['Versa Branch2 VM Name']
branch2_portgroup = attrs['Versa Branch2 NB Portgroup Name']
branch2_ip = attrs['Versa Branch2 NB IP']
branch2_dns = attrs['Versa Branch2 NB DNS']
branch2_mask = attrs['Versa Branch2 NB Mask']
branch2_gateway = attrs['Versa Branch2 NB Gateway']
branch2_eth = 'eth0'
analytics_log_port = attrs['Versa Analytics Logs Port']




def firstEth(ip, netmask, gateway, dns, eth='eth0'):
    script = '''auto lo `n iface lo inet loopback `n'''
    script += '''auto '''  + eth + ''' `n iface ''' + eth + ''' inet static `n  address ''' + ip + ''' `n netmask ''' + netmask + ''' `n gateway ''' + gateway + ''' `n dns-nameservers ''' + dns
    return script


#helpers
def do_command(ssh1, command):
    if command:
        qs_trace('ssh : ' + command)
        stdin, stdout, stderr = ssh1.exec_command(command)
        stdin.close()
        a = []
        for line in stdout.read().splitlines():
            a.append(line + '\n')
        for line in stderr.read().splitlines():
            a.append(line + '\n')
        rv = '\n'.join(a)
        qs_trace('ssh result: ' + rv)
        return rv


def do_command_and_wait(chan, command, expect):
    qs_trace('ssh : ' + command + ' : wait for : ' + expect)
    # Ssh and wait for the password prompt.
    chan.send(command + '\n')

    buff = ''
    #while buff.find(expect) < 0:
    while not re.search(expect, buff, 0):
        resp = chan.recv(9999)
        buff += resp
        #print resp
    qs_trace('replay : ' + buff + ' : wait for : ' + expect)
    time.sleep(1)
    return buff

try:
    #connect
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #allow auto-accepting new hosts

    ssh.connect(versa_dir_ip, username=versa_username, password=versa_password)


    #start Config Wizard
    chan = ssh.invoke_shell()
    do_command_and_wait(chan, r'n', expect=r' ')
    time.sleep(1)
    do_command_and_wait(chan, r'n', expect=r' ')
    time.sleep(1)
    do_command_and_wait(chan, r'n', expect=r' ')
    time.sleep(1)

    #Add Controll SSH key
    #do_command_and_wait(chan, r'sudo -i', expect=r'')
    #do_command_and_wait(chan, versa_password, expect=r'')
    #do_command_and_wait(chan, r'sudo ssh-keyscan  ' + controller_ip + ' >> /home/versa/.ssh/known_hosts', expect=r'#')
    #Disable 2way auth
    do_command_and_wait(chan, r'cli', expect=r' ')
    do_command_and_wait(chan, r'conf', expect=r' ')
    do_command_and_wait(chan, r'set system enable-2factor-auth false', expect=r' ')
    do_command_and_wait(chan, r'commit', expect=r' ')
except Exception, e:
    print "Failed to configure Director, Error:\"" + e.message + '"'


try:
    #Configure Controller Static IP
    contssh = paramiko.SSHClient()
    contssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #allow auto-accepting new hosts

    contssh.connect(controller_ip, username='admin', password='versa123')

    contchan = contssh.invoke_shell()
    do_command_and_wait(contchan, r'cli', expect=r' ')
    do_command_and_wait(contchan, r'conf', expect=r' ')
    do_command_and_wait(contchan, r'set interfaces eth-0/0 unit 0 family inet address ' + controller_ip + ' prefix-length 24 gateway ' + mgmt_gw, expect=r' ')
    do_command_and_wait(contchan, r'commit', expect=r' ')
    do_command_and_wait(contchan, r'q', expect=r' ')
    do_command_and_wait(contchan, r'q', expect=r' ')
    cmd = firstEth(controller_ip, controller_mask, controller_gateway, controller_dns).split('`n')
    do_command_and_wait(contchan, r'echo " " > /etc/network/interfaces', expect=r' ')
    for c in cmd:
        c = 'echo "' + c + '" >> /etc/network/interfaces'
        do_command_and_wait(contchan, c, expect=r' ')
        time.sleep(10)
except Exception, e:
    print "Failed to configure Controller, Error:\"" + e.message + '"'
#Reboot controller
try:
    vmPower(controller_vmname, 'restart', vcenter_ip, vcenter_user, vcenter_password)
except Exception, e:
    print "Failed to reboot Controller, Error:\"" + e.message + '"'
try:
    #Configure Branch1 Static IP
    br1ssh = paramiko.SSHClient()
    br1ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #allow auto-accepting new hosts

    br1ssh.connect(br1_ip, username='admin', password='versa123')

    br1chan = br1ssh.invoke_shell()
    do_command_and_wait(br1chan, r'cli', expect=r' ')
    do_command_and_wait(br1chan, r'conf', expect=r' ')
    do_command_and_wait(br1chan, r'set interfaces eth-0/0 unit 0 family inet address ' + br1_ip + ' prefix-length 24 gateway ' + mgmt_gw, expect=r' ')
    do_command_and_wait(br1chan, r'commit', expect=r' ')
    do_command_and_wait(br1chan, r'q', expect=r' ')
    do_command_and_wait(br1chan, r'q', expect=r' ')
    cmd = firstEth(branch1_ip, branch1_mask, branch1_gateway, branch1_dns).split('`n')
    do_command_and_wait(br1chan, r'echo " " > /etc/network/interfaces', expect=r' ')
    for c in cmd:
        c = '''echo "''' + c + '" >> /etc/network/interfaces'
        do_command_and_wait(br1chan, c, expect=r' ')
except Exception, e:
    print "Failed to configure Branch1, Error:\"" + e.message + '"'
try:
    #Configure Branch2 Static IP
    br2ssh = paramiko.SSHClient()
    br2ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #allow auto-accepting new hosts

    br2ssh.connect(br2_ip, username='admin', password='versa123')

    br2chan = br2ssh.invoke_shell()
    do_command_and_wait(br2chan, r'cli', expect=r' ')
    do_command_and_wait(br2chan, r'conf', expect=r' ')
    do_command_and_wait(br2chan, r'set interfaces eth-0/0 unit 0 family inet address ' + br2_ip + ' prefix-length 24 gateway ' + mgmt_gw, expect=r' ')
    do_command_and_wait(br2chan, r'commit', expect=r' ')
    do_command_and_wait(br2chan, r'q', expect=r' ')
    do_command_and_wait(br2chan, r'q', expect=r' ')
    cmd = firstEth(branch2_ip, branch2_mask, branch2_gateway, branch2_dns).split('`n')
    do_command_and_wait(br2chan, r'echo " " > /etc/network/interfaces', expect=r' ')
    for c in cmd:
        c = '''echo "''' + c + '" >> /etc/network/interfaces'
        do_command_and_wait(br2chan, c, expect=r' ')
except Exception, e:
    print "Failed to configure Branch2, Error:\"" + e.message + '"'

#Configure Analytics

#connect
analssh = paramiko.SSHClient()
analssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #allow auto-accepting new hosts

analssh.connect(analytics_ip, username='versa', password='versa123')

#start Analytics Config Wizard
analchan = analssh.invoke_shell()
do_command_and_wait(analchan, r'cli', expect=r' ')
do_command_and_wait(analchan, r'conf', expect=r' ')
do_command_and_wait(analchan, r'set log-collector-exporter local collectors collector1 address ' + analytics_sb_ip + ' port ' + analytics_log_port + ' transport tcp storage directory /var/tmp/log format syslog', expect=r' ')
do_command_and_wait(analchan, r'commit', expect=r' ')
do_command_and_wait(analchan, r'q', expect=r' ')
do_command_and_wait(analchan, r'q', expect=r' ')
do_command_and_wait(analchan, r'sudo /opt/versa/scripts/van-scripts/vansetup.py', expect=r' ')
time.sleep(1)
do_command_and_wait(analchan, r'versa123', expect=r' ')
time.sleep(100)
do_command_and_wait(analchan, r'y', expect=r' ')
time.sleep(200)
do_command_and_wait(analchan, r'y', expect=r' ')
time.sleep(100)

quali_exit(__file__)