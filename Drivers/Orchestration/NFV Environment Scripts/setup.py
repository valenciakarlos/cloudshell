from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
import cloudshell.api.cloudshell_api
from cloudshell.api.cloudshell_api import InputNameValue

csapi = helpers.get_api_session()
resid = helpers.get_reservation_context_details().id

