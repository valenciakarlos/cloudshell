from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
# from cloudshell.api.cloudshell_api import InputNameValue

csapi = helpers.get_api_session()
resid = helpers.get_reservation_context_details().id

csapi.EnqueueEnvironmentCommand(resid, commandName='copy_inputs')

csapi.EnqueueEnvironmentCommand(resid, commandName='generate_orchestration_steps_file')

# csapi.EnqueueEnvironmentCommand(resid, commandName='run_orchestration_steps', commandInputs=[
#     InputNameValue('Include_Ranges', 'all'),
#     InputNameValue('Exclude_Ranges', 'none')
# ])

