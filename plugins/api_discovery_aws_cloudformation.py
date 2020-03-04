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
import inspect
from ujson import loads, load
from ujson import dump, dumps
import yaml
import time
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from argparse import ArgumentParser
from sdk.types import Endpoint, API, Report
from sdk.fs_processor import Scanner
from sdk.plugins import Runner, Plugin, labels_parser, default_plugin_options


log = logging.getLogger(__name__)
plugin = Plugin(name="sast_api_cloudformation", version="1")


class Node(object):
  def __init__(self, node_id, value, parent=None, children=None):
    self._node_id = node_id
    self.value = value
    self._parent = parent
    if not children:
      self._children = []
    else:
      self._children = children
  
  def get_id(self):
    return self._node_id

  def add_child(self, child):
    if not isinstance(child, Node):
      raise Exception("The child needs to be a Node object")
    self._children.append(child)
    child.set_parent(self)
  
  def set_parent(self, parent):
    if not isinstance(parent, Node):
      raise Exception("The parent needs to be a Node object")
    self._parent = parent
  
  def get_children(self):
    return self._children


class Tree(Node):
  def __init__(self, tree_id, value):
    super().__init__(node_id=tree_id, value=value)
    # self._id = tree_id
    self._index = {}
    # self._root = root
    self._index[tree_id] = self

  def add_to_parent(self, parent_id, node):
    if len(self._index) == 0:
      # error
      return
    p_node = self._index.get(parent_id, None)
    if p_node:
      p_node.add_child(node)
      self._index[node.get_id()] = node
    else:
      # error
      return


def process_file(f_path):
  """
    Root (RestAPI) -> (Resource ->)+ Method
    Type: "AWS::ApiGateway::RestApi"

    "Type": "AWS::ApiGateway::Resource"
      Properties
        PathPart
        ParentId
          Ref
        RestApiId

    "Type": "AWS::ApiGateway::Method"
      Properties
        HttpMethod
        RequestTemplates
        ResourceId
        RestApiId

    "Type": "AWS::ApiGateway::Stage"
      Properties
        MethodSettings
          ResourcePath
        RestApiId
  """
  # filter by content, resurce types(Method, Stage, Recource, RestApi)
  log.debug("path: %s" % f_path)
  content_found = content_filter(f_path=f_path)
  if not content_found:
    return
  # parse file contents and collect APIs
  resources = load_file(r_path=f_path)
  trees = {}
  # Assemble graph with matching restapiIds, resourcesId, and parents
  api = API(name=f_path)
  for r_id in resources:
    resource = resources.get(r_id)
    r_type = resource.get("Type")
    properties = resource.get("Properties", {})
    if r_type.endswith('::RestApi'):
      if not trees.get(r_id):
        trees[r_id] = Tree(tree_id=r_id, value='/')
    elif r_type.endswith('::Resource'):
      value = properties.get("PathPart")
      parent_id = properties.get("ParentId").get("Fn::GetAtt", [''])[0]
      api_id = properties.get("RestApiId").get("Ref")
      tree = trees.get(api_id, None)
      if not tree:
        tree = Tree(tree_id=r_id, value='/')
        trees[api_id] = tree
      tree.add_to_parent(parent_id=parent_id, node=Node(node_id=r_id, value=value))
    elif r_type.endswith('::Method'):
      method = properties.get("HttpMethod")
      properties.get("RequestTemplates")
      properties.get("ResourceId").get("Ref")
      api_id = properties.get("RestApiId").get("Ref")
      pass
    elif r_type.endswith('::Stage'):
      api_id = properties.get("RestApiId").get("Ref")
      root_path = ''
      for setting in properties.get("MethodSettings", [{}]):
        r_path = setting.get("ResourcePath", None)
        if r_path:
          root_path = r_path
      tree = trees.get(api_id, None)
      if tree:
        tree.value = root_path + '/' + tree.value
      else:
        tree = Tree(tree_id=r_id, value=root_path)
        trees[api_id] = tree
    elif r_type.endswith('::ApiImport'):
      api_definition = properties.get('apiDefinition')
      process_openapi(api_definition=api_definition, api=api)
    else:
      continue
  # Build API from Graph
  for tree in trees:
    for path in bundle_path(prefix=('<%s>'%tree.lower()), node=trees[tree]):
      api.add_endpoint( Endpoint( path=re.sub('(\/{2,})', '/', path) ))   
  if len(api.endpoints) > 0:
    return api


def process_openapi(api_definition, api):
  log.debug('OpenApi...')
  # swagger 2.0
  prefix = '<%s>' % api_definition.get('info',{}).get('title','').lower() + '/'
  for path in api_definition.get('paths'):
    api.add_endpoint(Endpoint(path=re.sub('(\/{2,})', '/', prefix+path)))


def bundle_path(prefix, node):
  path = prefix + "/" + node.value
  paths = []
  if len(node.get_children()) > 0:
    for child in node.get_children():
      paths.extend(bundle_path(prefix=path, node=child))
  else:
    paths.append(path)
  return paths


def content_filter(f_path):
  pattern = re.compile(pattern='^\s*"?Type"?\s*:\s*"?(Custom|AWS::ApiGateway)::(ApiImport|Resource|Method|Stage|RestApi)"?[\,\s]*$', flags=(re.I | re.M))
  with open(f_path) as file:
    line = file.readline()
    while line:
      if pattern.match(line):
        return True
      line = file.readline()
  return False


def load_file(r_path):
  with open(r_path, 'r') as resource:
    if r_path.endswith('json'):
      return loads(resource).get("Resources")
    elif r_path.endswith('yaml') or r_path.endswith('yml'):
      return yaml.full_load_all(resource).get("Resources")
    elif r_path.endswith('template'):
      return load(resource).get("Resources")


def validate_args(options, f_targets):
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


def get_options():
  parser = ArgumentParser(prog="Levelops cloudformation configuration scanner.", usage="./api_discovery_aws_cloudformation.py (optional <flags>) <directory to scan>")
  parser.add_argument('-t', '--threads', dest='threads', help='Number of threads', type=int, default=5)
  for parser_option in default_plugin_options:
    parser.add_argument(*parser_option['args'], **parser_option['kwords'])

  return parser.parse_known_args()


def handle_output(options, results):
    if options.json:
      if options.print_results:
        log.info(dumps(results, indent=2))
      if options.output_file:
        with open(options.output_file, 'w') as f:
          dump(results, f, indent=2)

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


if __name__ == "__main__":
  logging.basicConfig(level="INFO", format="[%(threadName)s] [%(levelname)s]: %(message)s")

  options, f_targets = get_options()
  validate_args(options, f_targets)

  runner = Runner(endpoint=options.endpoint)
  success = False
  start_time = time.time()
  try:
    s = Scanner(thread_count=3, queue_timeout=0.5)
    for f_target in f_targets:
      log.info("scanning path: %s" % f_target)
      s.scan_directory(base_path=f_target, filters=[".json", ".yaml", ".yml", ".template"], action=process_file)
    s.wait_and_finish()
    success = True
    results =  s.get_report()

    handle_output(options, results)
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
      runner.submit(success=success, results=results, product_id=options.product, token=options.token, plugin=plugin, elapsed_time=(end_time - start_time), labels=options.labels)
  if success:
    sys.exit(0)
  else:
    sys.exit(1)