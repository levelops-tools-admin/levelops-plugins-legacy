# print("Package: %s" % __package__)
from .util import typechecked
from .results import PluginResults
from .plugins import Plugin
from .runner import Runner


def labels_parser(labels_str):
    labels = ""
    return labels


default_plugin_options = [
  {'args':['--debug'], 'kwords':{'dest': 'debug', 'help':'Enables debug logging', 'action':'store_true'}},
  {'args':['--print-results'], 'kwords':{'dest': 'print_results', 'help':'Wheter or not to print the results in the console.', 'action':'store_true'}},
  {'args':['--json'], 'kwords':{'dest': 'json', 'help':'If present, the output of the script will be in json format.', 'action':'store_true'}},
  {'args':['--csv'], 'kwords':{'dest': 'csv', 'help':'If present, the output of the script will be in csv format.', 'action':'store_true'}},
  {'args':['--out'], 'kwords':{'dest': 'output_file', 'help': 'Path to the destination file/directory. If present and valid, the scanner results will be written to the output file/directory. If the path is a directory, the result(s) will be written inside it with the prefix "levelops-"'}},
  {'args':['--apikey'], 'kwords':{'dest': 'token', 'help': 'If present, the scanner results will be submited to levelops and if the apiKey is correct, the results will be available to be reviewed and acted on at the customer\'s levelops instance.'}},
  {'args':['--submit'], 'kwords':{'dest': 'submit', 'help': 'If present, the results will be submited to levelops.', 'action': 'store_true'}},
  {'args':['--labels'], 'kwords':{'dest': 'labels', 'help': 'If submit is present, the coma separated list of labels will be part of the results sent to levelops.', 'type':labels_parser}},
  {'args':['--endpoint'], 'kwords':{'dest': 'endpoint', 'help': 'If submit is present, the hostname and protocol can be customize with this flag (default: https://api.levelops.io).', 'default': 'https://api.levelops.io'}},
  {'args':['-p', '--product'], 'kwords':{'dest': 'product', 'help': '(Required if submit is enabled) The id of the corresponding product for the execution of this script.'}}
]