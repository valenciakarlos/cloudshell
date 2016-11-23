import time
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers

csapi = helpers.get_api_session()
onracks = csapi.FindResources(resourceFamily="Management Devices", resourceModel="OnrackShell")
reservation_id = helpers.get_reservation_context_details().id
resources = []
bad_onracks = []
for onrack in onracks.Resources:
    if onrack.Name:
        csapi.AddResourcesToReservation(reservationId=reservation_id, resourcesFullPath=[onrack.FullName], shared=True)
        time.sleep(2)
        csapi.WriteMessageToReservationOutput(reservation_id, "Loading information from Onrack: " + str(onrack.Name) + " (" + str(onrack.Address) + ")")
        try:
            csapi.AutoLoad(onrack.FullName)
        except Exception as e:
            csapi.WriteMessageToReservationOutput(reservation_id, "Error: %s (%s): %s" % (str(onrack.Name), str(onrack.Address), str(e)))
            bad_onracks.append(str(onrack.Name))

        csapi.IncludeResource(onrack.FullName)
        resources.append(onrack.FullName)
        time.sleep(5)

if resources > 0:
    csapi.RemoveResourcesFromReservation(reservationId=reservation_id, resourcesFullPath=resources)

if not resources:
    s = 'No OnRack devices have been registered in CloudShell. Create an OnRack under Inventory and enter the address and credentials. It will run an initial discovery during creation. To refresh it in the future, reserve this environment again.'
    print s
    csapi.WriteMessageToReservationOutput(reservation_id, s)
    raise Exception(s)

if bad_onracks:
    s = 'OnRack error(s) occurred. Check OnRack connectivity and the log c:\\ProgramData\\QualiSystems\\Logs\\%s\\Shells.log, then re-run Setup here.' % reservation_id
    print s
    csapi.WriteMessageToReservationOutput(reservation_id, s)
    raise Exception(s)
