from cloudshell.api.cloudshell_api import CloudShellAPISession, ReservedResourceInfo

# api = CloudShellAPISession('10.10.111.203', username='admin', password='admin', domain='Global')
api = CloudShellAPISession('localhost', username='admin', password='admin', domain='Global')

# rd = api.GetReservationDetails('e8faf2bd-b6be-4440-84fe-bd934a986c74').ReservationDescription
rd = api.GetReservationDetails('1201c69e-48ab-4d57-a9de-991d0e47d072').ReservationDescription
sd = api.GetResourceDetails('Dell R730 948BRD2')
print rd


