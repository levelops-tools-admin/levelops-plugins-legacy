#!/usr/bin/env python

##################################################################
#  Copyright (C) 2019-2020 LevelOps Inc <support@levelops.io>
#  
#  This file is part of the LevelOps Inc Tools.
#  
#  This tool is licensed under Apache License, Version 2.0
##################################################################


# Objective: discover as many final endpoints as possible from the k8s configuration files.
#   Analyze:
#     - Ingress
#     - Endpoints. TBD
#     - NetworkPolicies. TBD
#     - Gateways. TBD
#     - LodBalancers. TBD

import os
import sys
import logging
import re
import yaml
import inspect
import time
from ujson import loads
from ujson import dump, dumps
from os import walk, path, listdir
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from argparse import ArgumentParser
from sdk.types import Endpoint, API, Report
from sdk.fs_processor import Scanner
from sdk.plugins import Runner, Plugin, labels_parser, default_plugin_options

log = logging.getLogger(__name__)
plugin = Plugin(name="sast_api_k8s", version="1")


# scan directory and subdirectories
# collect yaml, yml and json files and put them in the work queue
# consume files from the work queue
# # parse file
# # collect APIs
# return results

r_types = ["ingress"]


def process_file(f_path):
  # filter by content. only parse if the file actually contains any reource that we are intesrested in.
  # parse file contnents.
  # analize resource definitinon.
  # collect enpoints.
  log.debug("path: %s" % f_path)
  api_found = False
  api = API(name=f_path)
  pattern = re.compile(pattern='^\s*("?kind"?\s*:\s*"?([Ii]ngress)"?).*$', flags=(re.I | re.M))
  resource_found = False
  with open(f_path) as file:
    line = file.readline()
    while line:
      # check if the file contains any type of resource of our interest
      result = pattern.match(line)
      resource_found = result != None and result.group(2).lower() in r_types
      if resource_found:
        break
      line = file.readline()
      continue
  if not resource_found:
    return
  # Parse contents
  if f_path.endswith('yaml') or f_path.endswith('yml'):
    resources = load_yaml_resource(f_path)
  elif f_path.endswith('json'):
    resources = load_json_resource(f_path)
  else:
    log.error("Unsupported file type. No parser found for file '%s'", f_path)
    resources = None
    return
  for resource in resources:
    if not resource:
      continue
    try:
      # collect api paths
      # spec.rules.$
      rules = resource.get('spec', {}).get('rules')
      if not rules:
        return
      for rule in rules:
        host = rule.get('host', '*')
        for path in rule.get('http').get('paths'):
          api_path = path.get('path', '/')
          api_service = path.get('backend').get('serviceName')
          api_service_port = path.get('backend').get('servicePort')
          endpoint = host + '/' + api_path
          api.add_endpoint(Endpoint(path=endpoint))
    except Exception as e:
      log.error(e, exc_info=True)
  if len(api.endpoints) > 0:
    return api


def load_yaml_resource(r_path):
  with open(r_path, 'r') as resource:
    return [ dic for dic in yaml.full_load_all(resource)]


def load_json_resource(r_path):
  with open(r_path, 'r') as resource:
    return loads(resource)


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
  parser = ArgumentParser(prog="Levelops k8s configuration scanner.", usage="./api_discovery_k8s.py (optional <flags>) <directory to scan>")
  parser.add_argument('-t', '--threads', dest='threads', help='Number of threads', type=int, default=5)
  for parser_option in default_plugin_options:
    parser.add_argument(*parser_option['args'], **parser_option['kwords'])

  return parser.parse_known_args()


def handle_output(options, results):
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


if __name__ == "__main__":
  logging.basicConfig(level="INFO", format="[%(threadName)s] [%(levelname)s]: %(message)s")

  options, f_targets = get_options()
  validate_args(options, f_targets)

  runner = Runner(base_url=options.endpoint)
  success = False
  start_time = time.time()
  try:
    s = Scanner(queue_timeout=0.5)
    for f_target in f_targets:
      log.info("scanning path: %s" % f_target)
      s.scan_directory(base_path=f_target, filters=[".yml", ".yaml", ".json"], action=process_file)
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
      runner.submit(success=success, results=results, product_id=options.product, token=options.token, plugin=plugin, elapsed_time=(end_time - start_time), labels=options.labels, tags=options.tags)
  if success:
    sys.exit(0)
  else:
    sys.exit(1)