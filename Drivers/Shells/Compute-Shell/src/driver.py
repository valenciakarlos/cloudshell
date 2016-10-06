from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.context import InitCommandContext, ResourceCommandContext


class ComputeShellDriver (ResourceDriverInterface):

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        pass

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        pass

    def get_bios_version(self, context):
        """
        A simple example function
        :param ResourceCommandContext context: the context the command runs on
        """
        #return "BIOS version 1.2.10"
        pass

    def update_bios(self, context, bios_version):
        """
        An example function that accepts two user parameters
        :param ResourceCommandContext context: the context the command runs on
        :param str user_param1: A user parameter
        :param str user_param2: A user parameter
        """
        pass

    def _helper_function(self):
        """
        Private functions are always hidden, and will not be exposed to the end user
        """
        pass
