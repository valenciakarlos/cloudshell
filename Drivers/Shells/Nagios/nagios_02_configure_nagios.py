# service "Nagios"

import json
import os
import time
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

# sio_storage = attrs['Unified Datastore']
vcenter_ip = attrs['vCenter IP']
vcenter_pass = attrs['vCenter Administrator Password']
# exclude_esxs = attrs['Exclude ESXs From SDC Role']

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(
    paramiko.AutoAddPolicy())
ssh.connect(nagios_ip, username=nagios_username,password=nagios_password)
ssh.exec_command("echo \"\$USER3\$="+esxi_password+"\" >> /usr/local/nagios/etc/resource.cfg")
# ssh.exec_command("echo \"\$USER4\$="+sio_storage+"\" >> /usr/local/nagios/etc/resource.cfg")
ssh.exec_command("echo \"\$USER4\$="+'NotInUse'+"\" >> /usr/local/nagios/etc/resource.cfg")
ssh.exec_command("echo \"\$USER5\$="+vcenter_ip+"\" >> /usr/local/nagios/etc/resource.cfg")
# ssh.exec_command("echo \"\$USER6\$="+exclude_esxs+"\" >> /usr/local/nagios/etc/resource.cfg")
ssh.exec_command("echo \"\$USER6\$="+'NotInUse'+"\" >> /usr/local/nagios/etc/resource.cfg")
ssh.exec_command("echo \"\$USER7\$="+vcenter_pass+"\" >> /usr/local/nagios/etc/resource.cfg")

#add Qauli prefix to "commands" file
ssh.exec_command("echo '#Quali Commands:' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo '######' >> /usr/local/nagios/etc/objects/commands.cfg")
#add Memory command to "commands" file
ssh.exec_command("echo '#Check Memory#' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo 'define command{' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo '    command_name check_esxi_memory' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo '    command_line $USER1$/QualiChecks.py -v $USER5$ -u administrator@vsphere.local -p $USER7$ -e $USER6$ -d $USER4$ -x $HOSTADDRESS$ -t memory -w $ARG1$ -c $ARG2$' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo '}' >> /usr/local/nagios/etc/objects/commands.cfg")

#add CPU command to "commands" file
ssh.exec_command("echo '#Check CPU#' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo 'define command{' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo '    command_name check_esxi_cpu' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo '    command_line $USER1$/QualiChecks.py -v $USER5$ -u administrator@vsphere.local -p $USER7$ -e $USER6$ -d $USER4$ -x $HOSTADDRESS$ -t cpu -w $ARG1$ -c $ARG2$' >> /usr/local/nagios/etc/objects/commands.cfg")
ssh.exec_command("echo '}' >> /usr/local/nagios/etc/objects/commands.cfg")

#add Storage command to "commands" file
# ssh.exec_command("echo '#Check Storage#' >> /usr/local/nagios/etc/objects/commands.cfg")
# ssh.exec_command("echo 'define command{' >> /usr/local/nagios/etc/objects/commands.cfg")
# ssh.exec_command("echo '    command_name check_esxi_storage' >> /usr/local/nagios/etc/objects/commands.cfg")
# ssh.exec_command("echo '    command_line $USER1$/QualiChecks.py -v $USER5$ -u administrator@vsphere.local -p $USER7$ -e $USER6$ -d $USER4$ -x $HOSTADDRESS$ -t storage -w $ARG1$ -c $ARG2$' >> /usr/local/nagios/etc/objects/commands.cfg")
# ssh.exec_command("echo '}' >> /usr/local/nagios/etc/objects/commands.cfg")

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
check_command           check_esxi_memory!70!90\n\
max_check_attempts      5\n\
check_interval          0.5\n\
retry_interval          0.5\n\
}\n\
define service{\n\
    use                     generic-service\n\
hostgroup_name          quali-esxi\n\
service_description     CPU\n\
check_command           check_esxi_cpu!70!90\n\
max_check_attempts      5\n\
check_interval          0.5\n\
retry_interval          0.5\n\
}\n\
#define service{\n\
#    use                     generic-service\n\
#hostgroup_name          quali-esxi\n\
#service_description     ScaleIO Storage\n\
#check_command           check_esxi_storage!70!90\n\
#max_check_attempts      5\n\
#check_interval          0.5\n\
#retry_interval          0.5\n\
#}\n\
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


### QualiCheck Script ###
# Exampleargs: -v <vcenter_ip> -u administrator@vsphere.local -p <password> -e <esx_to_exclude_datastore_test(CSV)> -d <datastore_to_test_name> -x <esx_to_test> -t <test_memort_cpu_storage> -w 20 -c 50
script = r'''#!/usr/local/bin/python2.7
#\"\"

import argparse
import atexit
import getpass

try:
    from pyvim import connect
except:
    from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim
import ssl
import requests


def get_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--vcenter',
                        required=True,
                        action='store',
                        help='Remote vCenter to connect to')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='User name to use when connecting to host')

    parser.add_argument('-p', '--password',
                        required=True,
                        action='store',
                        help='Password to use when connecting to host')

    parser.add_argument('-e', '--exclude',
                        required=False,
                        action='store',
                        help='ESX exclude list')

    parser.add_argument('-d', '--datastore',
                        required=False,
                        action='store',
                        help='ScaleIO Datastore name')

    parser.add_argument('-x', '--host',
                        required=True,
                        action='store',
                        help='Name of ESXi host as seen in vCenter Server')

    parser.add_argument('-t', '--test',
                        required=True,
                        action='store',
                        help='Check to run; cpu, memory or storage')

    parser.add_argument('-w', '--warning',
                        required=True,
                        action='store',
                        help='% to send a warning')

    parser.add_argument('-c', '--critical',
                        required=True,
                        action='store',
                        help='% to send critical')

    args = parser.parse_args()
    return args


def CPU(host, warn, crit):
    percent = (float(host.summary.quickStats.overallCpuUsage) / float(host.summary.hardware.cpuMhz * host.summary.hardware.numCpuCores)) * 100
    if int(percent) < int(warn):
        exitcode = 0
    elif int(percent) < int(crit):
        exitcode = 1
    else:
        exitcode = 2
    print (str(round(percent,3)) + ' | CPU Usage=' + str(round(percent,3)) + ';' + warn + ';' + crit + ';0;100')
    exit(int(exitcode))

def Memory(host, warn, crit):
    percent = (float(host.summary.quickStats.overallMemoryUsage) / 1024) / (float(host.summary.hardware.memorySize) / 1024 / 1024 / 1024) * 100
    if int(percent) < int(warn):
        exitcode = 0
    elif int(percent) < int(crit):
        exitcode = 1
    else:
        exitcode = 2
    print (str(round(percent,3)) + ' | Memory Usage=' + str(round(percent,3)) + ';' + warn + ';' + crit + ';0;100')
    exit(int(exitcode))

def Storage(host, exclude, storage, warn, crit):
    datastore = ''
    if host.name not in exclude.split(','):
        for data in host.datastore:
            if data.name == storage:
                datastore = data
                break
        else:
            raise Exception('No Datastore with name ' + storage + ' was found')
    else:
        raise Exception('ESX is excluded from SIO Datastore')

    percent = ((float(datastore.summary.capacity) - float(datastore.summary.freeSpace)) / 1024 / 1024 / 1024) / (float(datastore.summary.capacity) / 1024 / 1024 / 1024) * 100
    if int(percent) < int(warn):
        exitcode = 0
    elif int(percent) < int(crit):
        exitcode = 1
    else:
        exitcode = 2
    print (str(round(percent,3)) + ' | Storage Usage=' + str(round(percent,3)) + ';' + warn + ';' + crit + ';0;100')
    exit(int(exitcode))


def main():

    args = get_args()
    try:
        default_context = ssl._create_default_https_context
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.verify_mode = ssl.CERT_NONE
    requests.packages.urllib3.disable_warnings()
    try:
        service_instance = connect.SmartConnect(host=args.vcenter,
                                                user=args.user,
                                                pwd=args.password,
                                                port=443,
                                                sslContext=context)
        if not service_instance:
            print('Could not connect to the specified host using specified '
                  'username and password')
            return -1

        atexit.register(connect.Disconnect, service_instance)

        content = service_instance.RetrieveContent()

        search_index = content.searchIndex
        # quick/dirty way to find an ESXi host
        host = search_index.FindByDnsName(dnsName=args.host, vmSearch=False)
        # host = search_index.FindByDnsName(dnsName=args.vihost, vmSearch=False)

        test = args.test
        warn = args.warning
        crit = args.critical
        if test == 'cpu':
            CPU(host, warn, crit)
        elif test == 'memory':
            Memory(host, warn, crit)
        elif test == 'storage':
            Storage(host, args.exclude, args.datastore, warn, crit)
        else:
            raise Exception('No valid test was selected Got: ' + test)


    except vmodl.MethodFault as e:
        print('Caught vmodl fault : ' + e.msg)
        return -1
    except Exception as e:
        print('Caught exception : ' + str(e))
        if 'No Datastore' in str(e):
            exit(2)
        return -1

    return 0

if __name__ == '__main__':
    main()

'''

ssh.exec_command("rm /usr/local/nagios/etc/pynag/hosts/*.cfg -f")
ssh.exec_command("echo \"" + script + "\"> /usr/local/nagios/libexec/QualiChecks.py")
stdin, stdout, ssh_stderr = ssh.exec_command("chmod +x /usr/local/nagios/libexec/QualiChecks.py")
out = stdout.read()
print out
