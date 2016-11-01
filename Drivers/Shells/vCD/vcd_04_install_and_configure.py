# service "vCloud Director"

import json
import os
import time
import paramiko
import socket
import re

from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)


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
    
    time.sleep(1)
    return buff


def ssh_upload(ssh1, local_file, dest_file):
    if local_file and dest_file:
        qs_trace('ssh upload : ' + local_file + ' -> ' + dest_file)
        sftp = ssh1.open_sftp()
        sftp.put(local_file, dest_file)
    


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']
vcdAddress = attrs['vCD Management IP']
vcdVMAddress = attrs['vCD VM IP']
rootPassword = attrs['vCD Root Password']
binPath = attrs['vCD Installation File Path']
syslogServer = attrs['vCD Syslog Server']
hostname = socket.gethostname()
csServerAddress = socket.gethostbyname(hostname)


#vcdAddress = "10.10.111.152"
#vcdVMAddress = "10.10.110.152"
#rootPassword = "dangerous2"
#binPath = r'C:\deploy\vmware-vcloud-director-8.0.0-3017494.bin'
#csServerAddress = "10.10.111.102"
#syslogServer = ''

#connect
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #allow auto-accepting new hosts

ssh.connect(vcdAddress, username='root', password=rootPassword)

#upload bin
ssh_upload(ssh, binPath, r'/tmp/vcd-install.bin')
#chmod
do_command(ssh, r'chmod u+x /tmp/vcd-install.bin')
#stop firewall
do_command(ssh, r'chkconfig iptables off')
do_command(ssh, r'service iptables stop')

#start install
chan = ssh.invoke_shell()
do_command_and_wait(chan, r'/tmp/vcd-install.bin', expect=r'Would you like to run the script now')
do_command_and_wait(chan, r'n', expect=r'\]#')
do_command_and_wait(chan, r'chown vcloud:vcloud /opt/keystore', expect=r'\]#')
#start configuration
out = do_command_and_wait(chan, r'/opt/vmware/vcloud-director/bin/configure', expect=r'Choice \[default=1\]')
#find the eth0 ip
m = re.search('(\d)\..' + vcdAddress,out)
pos = m.groups()[0]
out = do_command_and_wait(chan, pos, expect=r'Choice \[default=1\]')
#find the eth1 ip
m = re.search('(\d)\..' + vcdVMAddress,out)
pos = m.groups()[0]
do_command_and_wait(chan, pos, expect=r'Please enter the path to the Java keystore')
do_command_and_wait(chan, r'/opt/keystore/certificates.ks', expect=r'Please enter the password')
do_command_and_wait(chan, rootPassword, expect=r'Syslog host name or IP address')
if syslogServer:
    do_command_and_wait(chan, syslogServer, expect=r'What UDP port is the remote syslog server listening on')
    do_command_and_wait(chan, r'514', expect=r'Enter the database type')
else:
    do_command_and_wait(chan, r'', expect=r'Enter the database type')

do_command_and_wait(chan, r'2', expect=r'Enter the host \(or IP address\) for the database')
do_command_and_wait(chan, csServerAddress, expect=r'Enter the database port')
do_command_and_wait(chan, r'1433', expect=r'Enter the database name')
do_command_and_wait(chan, r'vcloud', expect=r'Enter the database instance')
do_command_and_wait(chan, r'qualisystems2008', expect=r'Enter the database username')
do_command_and_wait(chan, r'vcloud', expect=r'Enter the database password')
do_command_and_wait(chan, r'vcloudpass', r'Start it now|\]#')
do_command_and_wait(chan, r'y', r'\]#')

quali_exit(__file__)
