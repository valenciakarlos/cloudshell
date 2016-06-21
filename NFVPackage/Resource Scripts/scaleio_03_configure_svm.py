# service "ScaleIO"

from SIOCommon import *
import datetime
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
import os
import json

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

starttime = datetime.datetime.now()

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

# vCenter Info
vcenter_ip = attrs['vCenter IP']
vcenter_user = attrs['vCenter Username']
vcenter_password = attrs['vCenter Password']
datacenter = attrs['Datacenter']
esx_excludes = attrs['Exclude ESXs From SDC Role']

# SIO Deployment Info
vm_name = attrs['ScaleIO SVM Name PreFix']
sio_svm_cluster = attrs['ScaleIO Cluster']
sio_version = attrs['ScaleIO Version']
sio_admin_password = attrs['ScaleIO Admin Password']
gateway_password = attrs['Gateway Admin Password']
lia_password = attrs['LIA Password']
svm_password = attrs['SVM Root Password']
sio_storage_name = attrs['Unified Datastore']
prot_domain_name = attrs['Protection Domain Name']
storage_pool_name = attrs['Storage Pool Name']
fault_number = attrs['Number of Faultsets']
fault_name_prefix = attrs['Faultset Name PreFix']
rmcache = attrs['RAM Read Cache size per SDS']
system_name = attrs['ScaleIO System Name']
volume_type = attrs['Volume Type']
volume_size = attrs['Volume Size']
zp = attrs['Enable Zero Padding']
if (zp.lower() == 'false') or (zp is False):
    zp = ''
backscanner = attrs['Enable Background Scanner']
if (backscanner.lower() == 'false') or (backscanner is False):
    backscanner = ''
# Callhome info
callhome_smtp_server = attrs['Call Home SMTP Server']
callhome_smtp_port = attrs['Call Home SMTP Port']
callhome_smtp_tls = attrs['Call Home SMTP Use TLS']
callhome_smtp_username = attrs['Call Home SMTP Username']
callhome_smtp_password = attrs['Call Home SMTP Password']
callhome_sio_username = attrs['Call Home ScaleIO Username']
callhome_sio_password = attrs['Call Home ScaleIO Password']
callhome_email_from = attrs['Call Home Email From']
callhome_email_to = attrs['Call Home Email To']
callhome_customer_name = attrs['Call Home Customer Name']
callhome_severity_level = attrs['Call Home Severity Level']
callhome_syslog_server = attrs['Call Home Syslog Server']
callhome_syslog_port = attrs['Call Home Syslog Port']
callhome_syslog_facility = attrs['Call Home Syslog Facility']
callhome_dns1 = attrs['Call Home DNS Server 1']
callhome_dns2 = attrs['Call Home DNS Server 2']

# IP Info
mgmt_netmask = attrs['MGMT Subnet']
data1_netmask = attrs['Data Subnet']
data2_netmask = attrs['Second Data Subnet']
mgmt_gw = attrs['MGMT Gateway']

svm1_mgmt_ip = attrs['Primary MDM Management IP']
svm2_mgmt_ip = attrs['Secondary MDM Management IP']
svm3_mgmt_ip = attrs['Tie Breaker Management IP']
svm4_mgmt_ip = attrs['Gateway Management IP']

svm1_data1_ip = attrs['Primary MDM Data IP']
svm2_data1_ip = attrs['Secondary MDM Data IP']
svm3_data1_ip = attrs['Tie Breaker Data IP']
svm4_data1_ip = attrs['Gateway Data IP']

svm1_data2_ip = '' #'192.168.73.250'
svm2_data2_ip = '' #'192.168.73.251'
svm3_data2_ip = '' #'192.168.73.252'
svm4_data2_ip = '' #'192.168.73.253'

sds1_mgmt_ip = attrs['SDS1 MGMT IP']
sds2_mgmt_ip = attrs['SDS2 MGMT IP']
sds3_mgmt_ip = attrs['SDS3 MGMT IP']
sds4_mgmt_ip = attrs['SDS4 MGMT IP']

sds1_data1_ip = attrs['SDS1 Data IP']
sds2_data1_ip = attrs['SDS2 Data IP']
sds3_data1_ip = attrs['SDS3 Data IP']
sds4_data1_ip = attrs['SDS4 Data IP']

sds1_data2_ip = '' #'192.168.73.250'
sds2_data2_ip = '' #'192.168.73.251'
sds3_data2_ip = '' #'192.168.73.252'
sds4_data2_ip = '' #'192.168.73.253'

_siodic = {
    'Primary': [svm1_mgmt_ip, svm1_data1_ip, svm1_data2_ip],
    'Secondary': [svm2_mgmt_ip, svm2_data1_ip, svm2_data2_ip],
    'TieBreaker': [svm3_mgmt_ip, svm3_data1_ip, svm3_data2_ip],
    'Gateway': [svm4_mgmt_ip, svm4_data1_ip, svm4_data2_ip],
    'SDS-1': [sds1_mgmt_ip, sds1_data1_ip, sds1_data2_ip],
    'SDS-2': [sds2_mgmt_ip, sds2_data1_ip, sds2_data2_ip],
    'SDS-3': [sds3_mgmt_ip, sds3_data1_ip, sds3_data2_ip],
    'SDS-4': [sds4_mgmt_ip, sds4_data1_ip, sds4_data2_ip],
}



svms = getSIOSvms(vcenter_ip, vcenter_user, vcenter_password, datacenter, esx_excludes, vm_name)
svms.pop()
siodic = {}

for svm in svms:
    name = svm.replace(vm_name + '-', '')
    siodic[name] = [_siodic[name][0]]
siodic['Gateway'] = [svm4_mgmt_ip]
esxs = getSIOesxs(vcenter_ip, vcenter_user, vcenter_password, datacenter, esx_excludes, sio_svm_cluster)
esxs.pop()
esx_for_Storage = esxs[0].split(",")[0]




# Get ESX Data IPs
sdcdatalist = []
sdcdataips = getESXDataIPs(vcenter_ip, vcenter_user, vcenter_password, datacenter, esx_excludes)
for sdc in sdcdataips.split(","):
    sdcdatalist.append(sdc)

# Get Disks of each SVM
diskdic = {}
try:
    for name in siodic:
        _vm_name = vm_name + '-' + name
        # Skip Gateway SVM
        if not "Gateway" in _vm_name:
            disks = getSvmDisks(_vm_name, vcenter_ip, vcenter_user, vcenter_password)
            # Check if the VM have more then 1 disk
            if disks != '1':
                disk = int(disks)-1
                diskdic[_vm_name] = [disk]

except Exception, e:
    print e
    with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' Got Error: ' + e + '\r\n')
    exit(1)


# Install SVM role

try:
    for name in siodic:
        _vm_name = vm_name + '-' + name
        # Install PGP Key
        installKey(siodic[name][0])
        if "Gateway" in name:
            installGateway(siodic[name][0], gateway_password)
            configureGateway(siodic[name][0], svm1_mgmt_ip, svm2_mgmt_ip, zp)
        else:
            # Install SDS & LIA
            installSDS(siodic[name][0])
            installLIA(siodic[name][0], lia_password)
            # Install MDM role and install & Configure CallHome
            if siodic[name][0] == svm1_mgmt_ip or siodic[name][0] == svm2_mgmt_ip:
                installSIOVM(siodic[name][0], "mdm")
                if callhome_smtp_server != '':
                    installCallHome(siodic[name][0])
                    configureCallhome(siodic[name][0], smtphost=callhome_smtp_server, port=callhome_smtp_port, tls=callhome_smtp_tls.lower(), smtpuser=callhome_smtp_username, smtppass=callhome_smtp_password, user=callhome_sio_username, password=callhome_sio_password, fromemail=callhome_email_from, toemail=callhome_email_to, customername=callhome_customer_name, severity=callhome_severity_level.lower())
            elif "TieBreaker" in name:
                installSIOVM(siodic[name][0], "tb")
        # Change root Password
        changeRootPassword(siodic[name][0], svm_password)

except Exception, e:
    print e
    with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' Got Error: ' + e + '\r\n')
    exit(1)

# Configure SIO MDM Cluster
svmlist = []
try:
    configureSDS(svm1_mgmt_ip, svm2_mgmt_ip, svm3_mgmt_ip, adminpassword=sio_admin_password, password=svm_password)
    configureMainStorage(svm1_mgmt_ip, svm2_mgmt_ip, adminpassword=sio_admin_password, zp=zp, backscan=backscanner, sysname=system_name, password=svm_password, sp=storage_pool_name, pd=prot_domain_name)
    faults = createFaultsets(svm1_mgmt_ip, adminpassword=sio_admin_password, password=svm_password, pd=prot_domain_name, faultnameprefix=fault_name_prefix, number=fault_number)
    for name in siodic:
        _vm_name = vm_name + '-' + name
        if name != "Gateway":
            svmlist.append(siodic[name][0])
            svmlist.append(diskdic[_vm_name][0])
    addSdcNode(svm1_mgmt_ip, sdcdatalist, adminpassword=sio_admin_password, password=svm_password)
    time.sleep(30)
    addSdsStorage(svm1_mgmt_ip, svm2_mgmt_ip, svmlist, adminpassword=sio_admin_password, rmcache=rmcache, faultlist=faults, password=svm_password, pd=prot_domain_name, sp=storage_pool_name)
    time.sleep(30)
    addVolume(svm1_mgmt_ip, svm2_mgmt_ip, sdcdatalist, adminpassword=sio_admin_password, volumetype=volume_type, volumesize=volume_size, password=svm_password, pd=prot_domain_name, sp=storage_pool_name)
    time.sleep(30)
    addSioStorageToESX(esx_for_Storage, sio_storage_name, vcenter_ip, vcenter_user, vcenter_password)


except Exception, e:
    print e
    with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' Got Error: ' + e + '\r\n')
    exit(1)

# Install vCenter Plugin
try:
    installvCenterplugin(svm4_mgmt_ip, sio_version.replace('-', '.'), vcenter_ip, vcenter_user, vcenter_password)
    driver = webdriver.Firefox()
    driver.set_window_size(1440, 990)
    driver.implicitly_wait(20)
    driver.set_page_load_timeout(5)
    wait = WebDriverWait(driver, 10)
    # navigate to first page
    driver.get("https://" + vcenter_ip + "/")
    # login
    # set username
    # wait.until(EC.presence_of_element_located((By.NAME, 'vsphereConfig.credentials[0].hostname')))
    driver.find_element_by_xpath("//*[text()='Log in to vSphere Web Client']").click()
    time.sleep(5)
    driver.switch_to.frame('websso')
    time.sleep(1)
    driver.find_element_by_xpath("//*[@id='username']").send_keys(vcenter_user)
    # set password
    driver.find_element_by_xpath('//*[@id="password"]').send_keys(vcenter_password)
    # click login
    driver.find_element_by_xpath('//*[@id="submit"]').click()
    time.sleep(60)
    driver.quit()

except Exception, e:
    print e
    with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' Got Error: ' + e + '\r\n')
    exit(1)

endtime = datetime.datetime.now()
print "Total Configuration time: " + str(endtime - starttime)