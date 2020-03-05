
import logging
import shlex
import subprocess
import os

from shutil import rmtree

from sdk.scm import get_project_name

log = logging.getLogger(__name__)
SUCCESS = 0
ERRORS = set([1])


class ToolRunner(object):
    """ ToolsRunner:

        command: the command to be excecuted. can contain template variables that will be dynamicaly replaced at runtime.
                In addition to the global variables available for replacement, more variables/parameters can be specified
                in the template aslong as the values are passed to the 'scan' method in the 'params' field as a map.

        Global vars for replacement:
            - base_path = the path to the directory being scanned
            - project_name = the name of the project being scanned. the name is obtainned from the git config file or from the name of the directory.
    """
    def __init__(self, command: str, max_concurrent: int = 2, error_codes: set = None, keep_tmp_files=False):
        self.command = command
        self.tmp_locations = set()
        self.everything_ok = True
        self.errors = []
        self.error_codes = set()
        self.error_codes.update(ERRORS)
        self.keep_tmp_files = keep_tmp_files
        if error_codes:
            self.error_codes.update(error_codes)

    def scan_directory(self, base_path: str, params: dict, tmp_location: str):
        """ Scans a directory.
            the params will be used to dynamnicaly replace the command template provided during the instantiation of the class ToolRunner.

            templates variables:
                * base_path = the path to the directory being scanned
                * project_name = the name of the project being scanned. the name is obtainned from the git config file or from the name of the directory.
                * params = all variables/values passed as parameters will be used to replace vars in the command template
        """
        # Get project name
        project_name = get_project_name(base_path=base_path)
        # Add tmp location
        t_location = tmp_location.format(base_path=base_path, project_name=project_name , **params).format(base_path=base_path, project_name=project_name)
        self.tmp_locations.add(t_location)
        if not os.path.exists(t_location):
            os.mkdir(t_location)
        # parse cmd template
        cmd = self.command.format(base_path=base_path, project_name=project_name, **params).format(base_path=base_path, project_name=project_name)
        log.debug("Command -> %s", cmd)
        # run command
        tool = subprocess.run(args=shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        log.debug("Args: %s", tool.args)
        if tool.returncode in self.error_codes:
            message = "[%s] %s. scan path: %s" % (project_name, tool.stderr, base_path)
            self.errors.append(message)
            log.debug(message)
            self.everything_ok = False
        return project_name, tool.stdout, tool.stderr
    
    def get_tmp_locations(self):
        return self.tmp_locations

    def are_all_successes(self):
        return self.everything_ok
    
    def wait_and_finish(self):
        pass

    def cleanup(self):
        if self.keep_tmp_files:
            return
        for location in self.tmp_locations:
            rmtree(location)
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
