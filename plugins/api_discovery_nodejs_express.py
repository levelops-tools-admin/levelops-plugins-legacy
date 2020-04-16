#!/usr/bin/env python

##################################################################
#  Copyright (C) 2019-2020 LevelOps Inc <support@levelops.io>
#  
#  This file is part of the LevelOps Inc Tools.
#  
#  This tool is licensed under Apache License, Version 2.0
##################################################################

import logging
import sys
import re
import os
import io
import time
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from ujson import dump, dumps
from argparse import ArgumentParser
from sdk.types import Endpoint, API, Report
from sdk.fs_processor import Scanner
from sdk.plugins import Runner, Plugin, labels_parser, default_plugin_options


log = logging.getLogger(__name__)
plugin = Plugin(name="sast_api_express", version="1")

express_pattern = re.compile(pattern='^\s*var\s*(\w*)\s*=\s*(require\(\s*\'express\'\s*\))\s*.*;?$', flags=(re.I | re.M))
require_pattern = re.compile(pattern='^\s*var\s*(\w*)\s*=\s*(require\(\s*\'([\.\/\w]+)\'\s*\))\s*;?.*$', flags=(re.I | re.M))
router_pattern = re.compile(pattern='^\s*var\s*(\w*)\s*=\s*(require\(\s*\'express\'\s*\)|\w*)\s*\.Router\(.*\)\s*;?$', flags=(re.I | re.M))
use_pattern = re.compile(pattern='^.*\.\s*use\(\s*\'([\/\w]+)\'\s*,\s*(require\s*[=(]\'([\/\.\w]+)\'|\w+).*$', flags=(re.I | re.M))
endpoint_pattern1 = re.compile(pattern='^\s*.*\w+\s*\.\s*(get|post|delete|put)\s*\(\s*\'(\/[\/\w\:\}\{]*)\'\s*.*$', flags=(re.I | re.M))
endpoint_pattern2 = re.compile(pattern='^\s*.*\w+\s*\.\s*route\s*\(\s*\'(\/[\/\w\:\}\{]*)\'\s*\)\s*\.\s*(get|post|delete|put)\s*\(.*$', flags=(re.I | re.M))
resources = {}


def process_file(f_path):
  """
  Supported annotations:
    require('express')
    require('express').Router();

    app.use(express.static(__dirname + '/public'))

    router.use('/api', require('./api'));
    app.use('/api', require='./api')
    router.use('/users', require='../users.js')

    router.get('/list', function
    app.post('/update', function
    app.delete('/:user', function
    router.get('/:id', function

    app.get('/', function

    itemRouter.route('/add').get(function
      itemRouter.route('/add').post(function
  """
  # detect the variable used for the routes index.js
  # detect routes directly in the file (get('/...'),post('/...'),delete('/...'),etc)
  # detect all the 'use' calls
    # parse the use files and complement the api
  #
  # router var: ^\s*var\s*(\w*)\s*=\s*(require\(\s*\'express\'\s*\)|\w*)\s*\.Router\(.*\)\s*;?$
  # use def: ^.*\.\s*use\(\s*'([\/\w]+)'\s*,\s*(require\s*[=(]'([\/\.\w]+)'|\w+).*$
  # endpoints1: ^\s*.*\w+\s*\.\s*(get|post|delete|put)\s*\(\s*'([\/\w\:\}\{]+)'\s*.*$
  # endpoints2: ^\s*.*\w+\s*\.\s*route\s*\(\s*'([\/\w\:\}\{]+)'\s*\)\s*\.\s*(get|post|delete|put)\s*\(.*$
  # require resources def = ^\s*var\s*(\w*)\s*=\s*(require\(\s*\'([\.\/\w]+)\'\s*\)|\w*)\s*\s*;?$
  # express def = ^\s*var\s*(\w*)\s*=\s*(require\(\s*\'express\'\s*\)|\w*)\s*\s*;?$
  log.debug("path: %s" % f_path)
  # extract all resources...

  api_found = False
  prefix = ""
  api = API(name=f_path)
  with io.open(f_path) as file:
    try:
      content = file.read()
    except Exception as e:
      log.error('Error processing FILE: %s', f_path, exc_info=True)
      return
  
  result = express_pattern.findall(content)
  if not result:
    log.debug('skipping: %s', f_path)
    return

  requires = require_pattern.findall(content)
  routers = router_pattern.findall(content)
  uses = use_pattern.findall(content)
  endpoints1 = endpoint_pattern1.findall(content)
  endpoints2 = endpoint_pattern2.findall(content)
  
  r_id=f_path[:f_path.rindex('.')]
  resource = Resource(r_id=r_id, path=f_path)
  resource_found = False
  if endpoints1:
    for method,endpoint in endpoints1:
      resource.add_endpoint(Endpoint(path=endpoint,method=method))
      # api.add_endpoint(Endpoint(path=("%s - %s"%(method,endpoint) ) ) )
  if endpoints2:
    for endpoint,method in endpoints2:
      # api.add_endpoint(Endpoint(path=("%s - %s"%(method,endpoint) ) ) )
      resource.add_endpoint(Endpoint(path=endpoint,method=method))
  if requires:
    requires = {x:v for x,y,v in requires}
  if uses:
    for use_path, match, use_definition in uses:
      # Path base reference
      if "/" in use_definition:
        u_id=os.path.normpath(os.path.dirname(f_path) + "/" + use_definition)
      elif match in requires:
        # if the use definition is not a require statement, the definition is located in the match var.
        u_id=os.path.normpath(os.path.dirname(f_path) + "/" + requires[match])
      else:
        log.error("Couldn't resolve the use '%s' -> '%s'", match, use_path)
        continue
      resource.add_import(Import(id=u_id,target=use_path))
      # Resource(name=path, method=None, endpoint=None)
      # api.add_endpoint(Endpoint(path=("%s - %s - %s"%('use', use_path, use_definition) ) ) )
  if len(resource.endpoints) > 0 or len(resource.imports)>0:
    resources[resource.r_id]=resource
    parent_resource = os.path.normpath(f_path + "/../")
    parent = resources.get(parent_resource, None)
    if not parent:
      parent = Resource(r_id=parent_resource, path=parent_resource)
      resources[parent_resource] = parent
    parent.add_resource(resource)
  # api_found = True
  # log.debug("API!! %s, %s", f_path, result.group(5))
  # api.add_endpoint( Endpoint( path=(prefix+result.group(5)).replace('//', '/') ))
  # # if there was only the root mapping we add it as a single endpoint
  # if prefix != "" and not api_found:
  #   api.add_endpoint( Endpoint(path=prefix))
  #   api_found = True
  # if api_found:
  #   return api


class Import(object):
  def __init__(self, id, target):
    self.id = id
    self.target = target


class Resource(object):
  def __init__(self, r_id, path, endpoints=None, imports=None, resources=None):
    self.r_id = r_id
    self.path = path
    if not endpoints:
      self.endpoints = []
    else:
      self.endpoints = endpoints
    if not imports:
      self.imports = []
    else:
      sel.imports = imports
    if not resources:
      self.resources = []
    else:
      sel.resources = resources
  
  def add_import(self, r_import):
    if not isinstance(r_import, Import):
      raise Exception('Imports must be of type "Import"')
    self.imports.append(r_import)
  
  def add_endpoint(self, endpoint):
    if not isinstance(endpoint, Endpoint):
      raise Exception('endpoints must be of type "Endpoint"')
    self.endpoints.append(endpoint)
  
  def add_resource(self, resource):
    if not isinstance(resource, Resource):
      raise Exception('resource must be of type "Resource"')
    self.resources.append(resource)


def bundle_resources(prefix, resource):
  endpoints = []
  if resource in used_resource:
      return []
    # resource = Resource()
  for r_import in resource.imports:
    # r_import = Import()
    r = resources[r_import.id]
    path = os.path.normpath(prefix + "/" + r_import.target)
    endpoints.extend(bundle_resources(prefix=path, resource=r))
    used_resource.add(r)
  if prefix and prefix != '':
    for endpoint in resource.endpoints:
      endpoint.path = os.path.normpath(prefix + "/" + endpoint.path)
    for r in resource.resources:
      endpoints.extend(bundle_resources(prefix=prefix, resource=r))
      used_resource.add(r)
  endpoints.extend(resource.endpoints)
  return endpoints


if __name__ == "__main__":
  logging.basicConfig(level="INFO", format="[%(threadName)s] [%(levelname)s]: %(message)s")

  parser = ArgumentParser(prog="Levelops nodejs express configuration scanner.", usage="./api_discovery_nodejs_express.py (optional <flags>) <directory to scan>")
  parser.add_argument('-t', '--threads', dest='threads', help='Number of threads', type=int, default=5)
  for parser_option in default_plugin_options:
    parser.add_argument(*parser_option['args'], **parser_option['kwords'])

  options, f_targets = parser.parse_known_args()

  if options.debug:
      log.setLevel('DEBUG')
  if options.submit:
    if not options.product or not options.token:
      log.error("Both product and token options are required if the submit flag is present.")
      sys.exit(1)
  if options.json and options.csv:
      log.error("Only one output format can be selected at one time. Either pass the flag --json or --csv or no flag for standard output.")
      sys.exit(1)
  if (options.json or options.csv) and not options.output_file and not options.print_results:
      log.error("To use --csv or --json, either the --print-results flag (to print to the console) or the --out flag (to write to a file) must be specified.")
      sys.exit(1)

  if len(f_targets) < 1:
    log.error("must provide a list of directories to scan (space separated)")
    sys.exit(1)
  runner = Runner(base_url=options.endpoint)
  success = False
  start_time = time.time()
  try:
    s = Scanner(queue_timeout=0.5)
    for f_target in f_targets:
      log.info("scanning path: %s" % f_target)
      s.scan_directory(base_path=f_target, filters=".js", action=process_file)
    s.wait_and_finish()

    # assemble report
    report = Report()
    used_resource = set()
    for r_name in resources:
      resource = resources[r_name]
      endpoints = bundle_resources(prefix='',resource=resource)
      report.add_api(API(name=resource.path, endpoints=endpoints))

    success = True
    results =  report

    if options.json:
      if options.print_results:
        log.info(dumps(results, indent=2, escape_forward_slashes=False))
      if options.output_file:
        with open(options.output_file, 'w') as f:
          dump(results, f, indent=2, escape_forward_slashes=False)

    elif options.csv:
      if options.print_results:
        log.info("reference, api_endpoint")
        for api in results.apis:
          for endpoint in api.endpoints:
            log.info("%s,%s", api.name, endpoint.path)
      if options.output_file:
        with open(options.output_file, 'w') as f:
          f.write("reference, api_endpoint\n")
          for api in results.apis:
            for endpoint in api.endpoints:
              f.write("%s,%s\n" % (api.name, endpoint.path))

    elif options.print_results or options.output_file:
      if options.output_file:
        with open(options.output_file, 'w') as f:
          for api in results.apis:
            for endpoint in api.endpoints:
              f.write("%s     %s\n" % (api.name, endpoint.path))
      if options.print_results:
        log.info("======================================")
        log.info("Report:")
        # log.info("%s", report)
        for api in results.apis:
          for endpoint in api.endpoints:
            log.info("%s     %s", api.name, endpoint.path)
  except Exception as e:
    log.error("Couldn't successfully complete the scanning.", e, exc_info=True)
    results = str(e)
  except:
    error = sys.exc_info()
    log.error("Couldn't successfully complete the scanning: %s - %s", error[0], error[1], error[2])
    results = str(e)
  finally:
    end_time = time.time()
    if options.submit:
      # post failure to levelops
      runner.submit(success=success, results=results, product_id=options.product, token=options.token, plugin=plugin, elapsed_time=(end_time - start_time), labels=options.labels, tags=options.tags)
  if success:
    sys.exit(0)
  else:
    sys.exit(1)
      