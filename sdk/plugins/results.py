from .util import typechecked

class PluginResults(object):
    def __init__(self):
        self.metadata = {
            'plugin': {'id': '', 'name': '', 'version': ''},
            'project_id': '',
            'product_id': '',
            'failure_cause': '',
            'run_date': '',
            'env_name': ''
            }
        self.results = {}
        self.metrics = {
            'os': '',
            'available_cores': '',
            'execution_millis': '',
            'available_memory': '',
            '': '',
            '': ''
            }
        self.success = True
    
    @typechecked([dict])
    def set_results(self, results):
        self.results = results


class Metadata(dict):
    def __init__(self):
        super().__init__(self)
        self['plugin'] = dict
        self.metrics = {}
        self.success = true

