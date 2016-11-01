
import json
import os
import time
import paramiko
import re
import qualipy.api.cloudshell_api

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


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


Reservation_Context = os.environ['RESERVATIONCONTEXT']
Reservation_Context_Json = json.loads(Reservation_Context)

Quali_Connectivity_Context = os.environ['QUALICONNECTIVITYCONTEXT']
Quali_Connectivity_Context_Json = json.loads(Quali_Connectivity_Context)

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
resource_address = resource['address']
attrs = resource['attributes']
resource_Username = attrs['User']

serverAddress = Quali_Connectivity_Context_Json['serverAddress']
adminUser = Quali_Connectivity_Context_Json['adminUser']
adminPass = Quali_Connectivity_Context_Json['adminPass']
domain = Reservation_Context_Json['domain']

session = qualipy.api.cloudshell_api.CloudShellAPISession(serverAddress,adminUser,adminPass,domain)

resource_Password = attrs['Password'] #encrypted
resource_Password = session.DecryptPassword(resource_Password).Value

#inputs
interface_names = os.environ['InterfaceNames']
vlan_id = os.environ['VLAN_ID']


#connect
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #allow auto-accepting new hosts
ssh.connect(resource_address, username=resource_Username, password=resource_Password)
chan = ssh.invoke_shell()
#goto config terminal
do_command_and_wait(chan, r' ', '#')
do_command_and_wait(chan, r'config term', '#')
for interface in interface_names.split(','):
    if interface:
        #goto interface
        do_command_and_wait(chan, r'interface ' + interface, '#')
        #set access vlan
        do_command_and_wait(chan, r'switchport mode access', '#')
        #set vlan id
        do_command_and_wait(chan, r'switchport access vlan ' + vlan_id, '#')

