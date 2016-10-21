

from Versa_Common import *
import sys

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

#General VM config
datastore = attrs['Versa Datastore']
thick_thin = attrs['Versa Disk Mode']
vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']
vcenter_ip = attrs['vCenter IP']
datacenter = attrs['Versa Datacenter']
cluster = attrs['Versa Cluster']

#Analytics config
analytics_portgroup = attrs['Versa Analytics NB Portgroup Name']
analytics_vm_name = attrs['Versa Analytics VM Name']
analytics_ova_path = attrs['Versa Analytics Path']
analytics_ip = attrs['Versa Analytics NB IP']
analytics_dns = attrs['Versa Analytics NB DNS']
analytics_mask = attrs['Versa Analytics NB Mask']
analytics_gateway = attrs['Versa Analytics NB Gateway']
analytics_eth = 'eth0'
#eth 1
analytics_1_portgroup = attrs['Versa Analytics SB Portgroup Name']
analytics_1_ip = attrs['Versa Analytics SB IP']
analytics_1_dns = attrs['Versa SB DNS']
analytics_1_mask = attrs['Versa SB Netmask']
analytics_1_gateway = attrs['Versa Controller LAN IP']
analytics_1_eth = 'eth1'
analytics = {
    analytics_eth:(analytics_ip,analytics_portgroup,analytics_mask,analytics_gateway,analytics_dns),
    analytics_1_eth:(analytics_1_ip,analytics_portgroup,analytics_1_mask,analytics_1_gateway,analytics_1_dns)
}
controller_ip = attrs['Versa Controller LAN IP']
controller_mask = attrs['Versa SB Netmask']
controller_network = attrs['Versa SB Network']

dv_switch = str(attrs['Versa SB VDS'])
vds1_num_ports = '128'
vds1_vlanmode = 'none'
vds1_vlan_ids = '0'


try:
    vcenterparams = {
        'IP': vcenter_ip,
        'user': vcenter_user,
        'password': vcenter_password}

    # Set VC session
    session = Vcenter(vcenterparams)
    # STEPS # Quit if analytics_vm_name already exists on vcenter_ip vcenter_user vcenter_password
    session.add_dvPort_group(dv_switch, analytics_1_portgroup, int(vds1_num_ports), vds1_vlanmode, vds1_vlan_ids)

except:
    pass


#Deploy Analytics
try:
    command = ' --skipManifestCheck --noSSLVerify  --allowExtraConfig --datastore=' + '"' + datastore + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --net:"VM Network"="' + analytics_1_portgroup + '" --name="' + analytics_vm_name + '" "' + analytics_ova_path + '" "vi://' + vcenter_user + ':"' + vcenter_password + '"@' + vcenter_ip + '/' + datacenter + '/host/' + cluster + '/Resources"'
    deployVM(command, analytics_vm_name, vcenter_ip, vcenter_user, vcenter_password, False)
    time.sleep(5)
    vmPower(analytics_vm_name, 'start', vcenter_ip, vcenter_user, vcenter_password)
except Exception, e:
    print '\r\n' + str(e)
    sys.exit(1)
        
route_script = '''\"echo up route add -net 172.16.0.0 netmask 255.255.0.0 gw 192.168.140.254 dev eth1 >> /etc/network/interfaces\"'''
time.sleep(30)
try:
    addAdapter(analytics_vm_name, analytics, vcenter_ip, vcenter_user, vcenter_password)
    analytics = setAdapterMAC(analytics_vm_name, analytics, vcenter_ip, vcenter_user, vcenter_password)
    chmod = '''\"echo \'versa123\' | sudo -S chmod 777 /etc/network/interfaces\"'''
    networking = firstEth(analytics)
    networking += addEth(analytics)
    networking += addRoute(analytics_gateway, controller_ip, controller_mask, controller_network)
    networking += '\' > /etc/network/interfaces"'
    invokeScript(chmod, analytics_vm_name, 'versa', 'versa123', 20, 30, vcenter_ip, vcenter_user, vcenter_password)
    invokeScript(networking, analytics_vm_name, 'versa', 'versa123', 20, 30, vcenter_ip, vcenter_user, vcenter_password)
    invokeScript(route_script, analytics_vm_name, 'versa', 'versa123', 20, 30, vcenter_ip, vcenter_user, vcenter_password)
    vmPower(analytics_vm_name, 'restart', vcenter_ip, vcenter_user, vcenter_password)
except Exception, e:
    print e