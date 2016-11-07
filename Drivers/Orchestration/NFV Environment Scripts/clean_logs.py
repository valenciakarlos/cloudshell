import time
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
import os

resid = helpers.get_reservation_context_details().id

logdir = r'c:\ProgramData\QualiSystems\Logs\%s' % resid

for logname in ['shells', 'orchestration']:
    oldname = os.path.join(logdir, logname) + '.log'
    newname = os.path.join(logdir, logname) + ('_%s.log' % time.strftime('%Y-%m-%d__%H%M%S'))
    try:
        os.rename(oldname, newname)
        print 'Moved %s to %s' % (oldname, newname)
    except Exception as e:
        print str(e)
