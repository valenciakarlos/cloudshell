# service "Nagios"

import json
import os
import time
import subprocess
import paramiko
with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']
nagios_password = attrs['Nagios Root Password']
nagios_username = 'root'
nagios_ip = attrs['Nagios IP']
esxi_password = attrs['ESX Root Password']

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(
    paramiko.AutoAddPolicy())
ssh.connect(nagios_ip, username=nagios_username,password=nagios_password)
ssh.exec_command("echo \"\$USER3\$="+esxi_password+"\" >> /usr/local/nagios/etc/resource.cfg")
#add Qauli prefix to "commands" file
ssh.exec_command("echo '#Quali Commands:' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo '######' >> /usr/local/nagios/etc/objects/commands.cfg")
#add Memory command to "commands" file
ssh.exec_command("echo '#Check Memory#' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo 'define command{' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo '    command_name check_esxi_memory' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo '    command_line $USER1$/QualiMem $HOSTADDRESS$ $USER3$ $ARG1$ $ARG2$' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo '}' >> /usr/local/nagios/etc/objects/commands.cfg")
#Add 'quali-esxi' hostgroup template with services (including Memory)
ssh.exec_command("echo '''define hostgroup {\n\
hostgroup_name                 quali-esxi\n\
alias                          Quali Managed ESXi\n\
}\n\
\n\
define service{\n\
    use                     generic-service\n\
hostgroup_name          quali-esxi\n\
service_description     Memory\n\
check_command           check_esxi_memory!50!80\n\
max_check_attempts      5\n\
check_interval          0.5\n\
retry_interval          0.5\n\
}\n\
define service{\n\
    use                     generic-service\n\
hostgroup_name          quali-esxi\n\
service_description     HTTP\n\
check_command           check_http!-w 2 -c 5\n\
max_check_attempts      5\n\
check_interval          0.5\n\
retry_interval          0.5\n\
}\n\
define service{\n\
    use                     generic-service\n\
hostgroup_name          quali-esxi\n\
service_description     SSH\n\
check_command           check_ssh\n\
max_check_attempts      5\n\
check_interval          0.5\n\
retry_interval          0.5\n\
}\n\
\n\
define service{\n\
    use                     generic-service\n\
hostgroup_name          quali-esxi\n\
service_description     vSphere_902\n\
check_command           check_tcp!902\n\
max_check_attempts      5\n\
check_interval          0.5\n\
retry_interval          0.5\n\
}''' >> /usr/local/nagios/etc/pynag/hostgroups/QualiESXiGroup.cfg")

