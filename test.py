from cloudshell.api.cloudshell_api import CloudShellAPISession, ReservedResourceInfo

api = CloudShellAPISession('localhost', username='admin', password='admin', domain='Global')

rd = api.GetReservationDetails('48f9d2c2-7786-4296-9ddd-2953d373682c').ReservationDescription
sd = api.GetResourceDetails('Dell R730 948BRD2')
print rd