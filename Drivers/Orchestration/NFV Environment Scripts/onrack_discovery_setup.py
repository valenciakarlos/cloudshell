import time
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers

csapi = helpers.get_api_session()
onracks = csapi.FindResources(resourceFamily="Management Devices", resourceModel="OnrackShell")
reservation_id = helpers.get_reservation_context_details().id
resources = []

for onrack in onracks.Resources:
    if onrack.Name:
        csapi.AddResourcesToReservation(reservationId=reservation_id, resourcesFullPath=[onrack.FullName], shared=True)
        time.sleep(2)
        csapi.WriteMessageToReservationOutput(reservation_id, "Loading information from Onrack: " + str(onrack.Name) + " (" + str(onrack.Address) + ")")
        csapi.AutoLoad(onrack.FullName)
        csapi.IncludeResource(onrack.FullName)
        resources.append(onrack.FullName)
        time.sleep(5)

if len(resources) > 0:
    csapi.RemoveResourcesFromReservation(reservationId=reservation_id, resourcesFullPath=resources)

if len(resources) == 0:
    s = 'No OnRack devices have been registered in CloudShell. Create an OnRack and enter the address and credentials, then re-run Setup here.'
    print s
    csapi.WriteMessageToReservationOutput(reservation_id, s)
    raise Exception(s)