from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from cloudshell.api.cloudshell_api import InputNameValue

csapi = helpers.get_api_session()
resid = helpers.get_reservation_context_details().id

csapi.ExecuteEnvironmentCommand(resid, 'copy_prereq')
csapi.ExecuteEnvironmentCommand(resid, 'copy_inputs')
csapi.ExecuteEnvironmentCommand(resid, 'generate_orchestration_steps_file')
csapi.ExecuteEnvironmentCommand(resid, 'run_orchestration_steps', commandInputs=[
    InputNameValue('IncludeSteps', 'all'),
    InputNameValue('ExcludeSteps', 'none')
])
