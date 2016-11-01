# service "vCloud Director"

import json
import os
import time
import paramiko

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


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']
vcdAddress = attrs['vCD Management IP']
vcdVMAddress = attrs['vCD VM IP']
rootPassword = attrs['vCD Root Password']
httpDname = attrs['vCD HTTP Service Cert dname']
httpExt = attrs['vCD HTTP Service Cert ext dns']
proxyDname = attrs['vCD Proxy Service Cert dname']
proxyExt = attrs['vCD HTTP Service Cert ext dns']

#value examples
#vcdAddress = "10.10.111.152"
#vcdVMAddress = "10.10.110.152"
#rootPassword = "dangerous2"
#httpDname = "CN=scln152.lss.emc.com, OU=Engineering, O=EMC Corp, L=Santa Clara S=California C=US"
#httpExt = "san=dns:scln152.lss.emc.com,dns:scln152"
#proxyDname = "CN=vcd3.lss.emc.com, OU=Engineering, O=EMC Corp, L=Santa Clara S=California C=US"
#proxyExt = "san=dns:vcd3.lss.emc.com,dns:vcd3"

if ",ip:" not in httpExt:
    httpExt += ",ip:" + vcdAddress

if ",ip:" not in proxyExt:
    proxyExt += ",ip:" + vcdVMAddress

#connect
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #allow auto-accepting new hosts

ssh.connect(vcdAddress, username='root', password=rootPassword)

#create folder
do_command(ssh, r'mkdir /opt/keystore')

#create certificate files
httpcert = 'keytool -keystore /opt/keystore/certificates.ks -alias http -storepass ' + rootPassword + ' -keypass ' + rootPassword + ' -storetype JCEKS -genkeypair -keyalg RSA -keysize 2048 -validity 365 -dname "' + httpDname + '" -ext "' + httpExt + '"'

do_command(ssh, httpcert)

proxycert = 'keytool -keystore /opt/keystore/certificates.ks -alias consoleproxy -storepass ' + rootPassword + ' -keypass ' + rootPassword + ' -storetype JCEKS -genkeypair -keyalg RSA -keysize 2048 -validity 365 -dname "' + proxyDname + '" -ext "' + proxyExt + '"'

do_command(ssh, proxycert)

print 'self-signed certificates created'

quali_exit(__file__)