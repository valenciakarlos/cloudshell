# from cloudshell.api.cloudshell_api import CloudShellAPISession, ReservedResourceInfo
#
# # api = CloudShellAPISession('10.10.111.203', username='admin', password='admin', domain='Global')
# api = CloudShellAPISession('localhost', username='admin', password='admin', domain='Global')
#
# # rd = api.GetReservationDetails('e8faf2bd-b6be-4440-84fe-bd934a986c74').ReservationDescription
# rd = api.GetReservationDetails('1201c69e-48ab-4d57-a9de-991d0e47d072').ReservationDescription
# sd = api.GetResourceDetails('Dell R730 948BRD2')
# print rd
#
#

import json

out = json.loads(
    '''{"SKU": "To be filled by O.E.M.", "BiosVersion": "S2B_3A17 5.6 11/07/2014", "PowerState": "Off", "Processors": {"@odata.type": "#ProcessorCollection.ProcessorCollection", "Oem": {}, "Members@odata.navigationLink": {"@odata.id": null}, "Members@odata.count": 2.0, "@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/Processors", "@odata.context": null, "Members": [{"@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/Processors/Socket0"}, {"@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/Processors/Socket1"}], "Description": null, "Name": "Processors Collection"}, "SerialNumber": null, "Boot": {"BootSourceOverrideTarget": null, "UefiTargetBootSourceOverride": null, "BootSourceOverrideEnabled": null}, "PartNumber": null, "ProcessorSummary": {"Status": {"HealthRollup": "OK", "State": null, "Health": "OK", "Oem": {"StatesAsserted": []}}, "Count": 2.0, "Model": "Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz"}, "@odata.type": "#ComputerSystem.1.0.0.ComputerSystem", "Description": null, "HostName": null, "@odata.context": null, "SimpleStorage": {"@odata.type": "#SimpleStorageCollection.SimpleStorageCollection", "Oem": {}, "Members": [{"@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/SimpleStorage/0"}, {"@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/SimpleStorage/1"}], "Members@odata.count": 2.0, "@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/SimpleStorage", "@odata.context": null, "Members@odata.navigationLink": {"@odata.id": null}, "Name": "SimpleStorage Collection", "Description": null}, "Oem": {"EMC": {"VisionID_System": "QTF3J052100191", "VisionID_Chassis": "QTFCJ05260027", "VisionID_Ip": "10.10.111.11"}}, "Manufacturer": "Quanta Computer Inc", "Status": {"HealthRollup": null, "State": null, "Health": "Down", "Oem": {"StatesAsserted": null}}, "Name": "Quanta D51", "AssetTag": " ", "@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88", "IndicatorLED": "Off", "LogServices": {"@odata.type": "#LogServiceCollection.LogServiceCollection", "Oem": {}, "Members@odata.count": 1.0, "@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/LogService", "@odata.context": null, "Members@odata.navigationLink": {"@odata.id": null}, "Description": null, "Name": "Log Service Collection", "Members": [{"@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/LogService/sel"}]}, "MemorySummary": {"Status": {"HealthRollup": null, "State": null, "Health": null, "Oem": {"StatesAsserted": []}}, "TotalSystemMemoryGiB": 256.0}, "Model": "D51B-2U (dual 1G LoM)", "EthernetInterfaces": {"@odata.type": null, "Description": null, "Members": [], "Members@odata.navigationLink": {"@odata.id": null}, "Members@odata.count": null, "@odata.id": null, "@odata.context": null, "Oem": {}, "Name": null}, "UUID": "51C208A2-7C18-1000-B48B-2C600C989213", "Links": {"PoweredBy": [{"@odata.id": "/redfish/v1/Chassis/582a28eb5db8528c07d97c88/Power"}], "Chassis@odata.count": 1.0, "Chassis@odata.navigationLink": {"@odata.id": null}, "ManagedBy@odata.count": 1.0, "PoweredBy@odata.count": 1.0, "ManagedBy@odata.navigationLink": {"@odata.id": null}, "ManagedBy": [{"@odata.id": "/redfish/v1/Managers/582a28eb5db8528c07d97c88"}], "Chassis": {"@odata.id": "/redfish/v1/Chassis/582a28eb5db8528c07d97c88"}, "CooledBy@odata.navigationLink": {"@odata.id": null}, "Oem": {}, "CooledBy@odata.count": 0.0, "CooledBy": [], "PoweredBy@odata.navigationLink": {"@odata.id": null}}, "SystemType": null, "Actions": {"#ComputerSystem.Reset": {"target": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/Actions/ComputerSystem.Reset", "title": null}, "Oem": {"OnRack.BootImage": {"target": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/OEM/OnRack/Actions/BootImage", "title": null}}}, "Id": "582a28eb5db8528c07d97c88"}''')

if out['Oem']['EMC']['VisionID_System']:
    name = out['Name']
    model = out.get('Model', None)
    if model:
        model = name + ' ' + model.strip()
    else:
        model = name

    a = {
        "OnRackID": out['Id'],
        "ResourceName": out['Name'] + ' ' + out['Oem']['EMC']['VisionID_Chassis'],
        "ResourceAddress": out['Id'],
        "ResourceFamily": "Compute Server",
        "ResourceModel": "ComputeShell",
        "ResourceFolder": "Compute/" + 'name',
        "ResourceDescription": out['Oem']['EMC']['VisionID_System'],
        "ResourceSubresources": [],

        # "ResourceDescription": '\n'.join([s[2:]
        #                                   for s in re.sub(r'[{}"\[\]]', '', json.dumps(out, indent=2, separators=('', ': '))).split('\n')
        #                                   if s.strip()]).strip()[0:1999],
        "Number of CPUs": str(out['ProcessorSummary']['Count']),
        "Memory Size": str(out['MemorySummary']['TotalSystemMemoryGiB']),
        "BIOS Version": str(out['BiosVersion']),
        "Vendor": out['Manufacturer'],
        "Serial Number": out['SerialNumber'],
        "Model": model,
        "VisionID IP": out['Oem']['EMC']['VisionID_Ip'],
        "Location": '',
    }