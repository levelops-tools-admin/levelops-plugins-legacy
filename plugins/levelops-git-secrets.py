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
import time
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from re import compile, I, M
from shutil import copyfile, copy
from ujson import load, dump, dumps
from argparse import ArgumentParser

from sdk.fs_processor import Scanner
from sdk.wrapper import ToolRunner
from sdk.plugins import Runner, Plugin, labels_parser, default_plugin_options


log = logging.getLogger(__name__)
plugin = Plugin(name="sast_git_secrets", version="1")

result_project_extractor = compile(pattern='^.*(levelops-brakeman-(.*)).json\s*$', flags=(I | M))

def get_formats_and_outputs(options):
  formats = []
  if options.json:
    formats.append("json")
  if options.csv:
    formats.append("csv")
  outputs = []
  if options.output_file:
    outputs.append("file")
  if options.print_results:
    outputs.append("print")
  return formats, outputs


def get_output_files(output_dir, formats):
  files = ""
  for format in formats:
    files += "-o {output_dir}/levelops-brakeman-{project_name}.{format} ".format(output_dir=output_dir, format=format, project_name="{project_name}") # hack to delay replacement of project_name
  return files


def handle_output(formats, outputs, output_location, reslults):
  multiformat = len(formats) > 1
  generate_destination = True
  if os.path.isfile(output_location):
    generate_destination = False
    destination = output_location
  for target in results:
    result = results[target]['results']
    project_name = results[target]['project_name']
    for format in formats:
      if "print" in outputs:
        if multiformat:
          print("")
          print("")
          print("-------------------------")
          print("      %s" % format)
          print("-------------------------")
          print("")
        if format == "json":
          print(dumps(result, indent=2))
        if format == "csv":
          print("type,commit,file_name,secret,lines")
          for file_name in result['hits']:
            for match in result['hits'][file_name]:
              print("current,,%s,%s,\"%s\"" % (file_name,match,','.join(result['hits'][file_name][match]['lines'])))
          for commit in result['historic']:
            for file_name in result['historic'][commit]:
              for match in result['historic'][commit][file_name]:
                print("historic,%s,%s,%s,\"%s\"" % (commit, file_name, match, ','.join(result['historic'][commit][file_name][match]['lines'])))
      consecutive = 0
      if "file" in outputs:
        if generate_destination:
          destination = "{dir}/levelops-git-secrets-{project}.{extension}".format(dir=output_location, project=project_name, extension=format)
          while os.path.exists(destination):
            tmp = destination
            consecutive += 1
            alt_project_name = project_name + "_" + str(consecutive)
            destination = "{dir}/levelops-git-secrets-{project}.{extension}".format(dir=output_location, project=alt_project_name, extension=format)
          
        with open(destination, 'w') as out:
          if format == "json":
            dump(result, out, indent=2)
          if format == "csv":
            out.write("type,commit,file_name,secret,lines\n")
            for file_name in result['hits']:
              for match in result['hits'][file_name]:
                out.write("current,,%s,%s,\"%s\"\n" % (file_name,match,','.join(result['hits'][file_name][match]['lines'])))
            for commit in result['historic']:
              for file_name in result['historic'][commit]:
                for match in result['historic'][commit][file_name]:
                  out.write("historic,%s,%s,%s,\"%s\"\n" % (commit, file_name, match, ','.join(result['historic'][commit][file_name][match]['lines'])))


def validate_args(options, f_targets):
  if options.debug:
      log.setLevel('DEBUG')
  if options.submit:
    if not options.product or not options.token:
      log.error("Both product and token options are required if the submit flag is present.")
      sys.exit(1)
  if (options.json or options.csv) and not options.output_file and not options.print_results:
      log.error("To use --csv or --json pass either the --print-results flag (to print to the console) or the --out flag (to write to a file).")
      sys.exit(1)
  if not options.docker and not options.local:
    log.error("An execution mode is needed. Please select either --docker or --local")
    sys.exit(1)
  if options.docker and options.local:
    log.error("Only one execution mode can be specified per invocation (--docker or --local).")
    sys.exit(1)

  if len(f_targets) < 1:
    log.error("must provide a list of directories to scan (space separated)")
    sys.exit(1)


def get_options():
  parser = ArgumentParser(prog="Levelops git-secrets plugin.", usage="./levelops-git-secrets.py (optional <flags>) <directory to scan>")
  parser.add_argument('--docker', dest='docker', help='Will run in docker mode, "docker" command needs to be in the path and the user that runs the plugin needs to have permissions to run docker containers.', action="store_true")
  parser.add_argument('--local', dest='local', help='Will run in local mode, the git-secrets command needs to be in the path.', action="store_true")
  for parser_option in default_plugin_options:
    parser.add_argument(*parser_option['args'], **parser_option['kwords'])

  return parser.parse_known_args()


def get_work_dirs(options):
  output_location = None
  if options.output_file:
    # if it is a file use the parent folder for mounting and the file name for the output
    if os.path.isfile(options.output_file):
      output_location = os.path.dirname(options.output_file)
      reports_base = output_location
    else:
      output_location = options.output_file
      # if it is a directoty use it as base path
      reports_base = output_location
  else:
    # if no output file specified then we will use the base path of each project to temporarily store the files.
    reports_base = "{base_path}"
    output_location = os.curdir
  return output_location, reports_base


def parse_output(output: str, is_historic: bool=False):
  hits = {}
  historic = {}
  errors = []
  recomendations = []
  result = {"hits": hits, "historic": historic, "errors": errors, "recomendations": recomendations}

  pass_errors = False
  # default container when we are not parsing the results of a history scan
  container = hits
  for line in output.splitlines():
    line = line.strip()
    if len(line) <= 0:
      continue

    # Decting error message line
    if line.startswith('[ERROR]'):
      errors.append(line)
      pass_errors = True
      continue
    # Detecting recomendations
    if pass_errors:
      recomendations.append(line)
      continue

    # Parsing found secrets
    tmp = line
    # check if we are parsing a line that is the result of a history scan
    if is_historic:
      # get the commit
      l_index = tmp.index(':')
      commit = tmp[:l_index]
      tmp = tmp[l_index+1:]
      # get the dictionary for the commit to append to
      h = historic.get(commit, None)
      if not h:
        h = {}
        historic[commit] = h
      container = h

    l_index = tmp.index(':')
    file = tmp[:l_index]
    tmp = tmp[l_index+1:]

    l_index = tmp.index(':')
    number = tmp[:l_index]

    match = tmp[l_index+1:]

    item = container.get(file, {})
    match_results = item.get(match, {'lines': []})
    match_results['lines'].append(number)
    item[match] = match_results
    container[file] = item
    
  return result


def merge_results(c_results, h_results):
  c_results['historic'] = h_results['historic']
  return c_results
    # for file_key in h_result:
    # file_results = c_result.get(file_key, None)
    # if not file_results:
    #   c_result[file_key] = h_result[file_key]
    #   continue
    # historic = file_results.get('historic', {})
    # historic.update(h_result['historic'])
    # file_results['historic'] = historic


def get_results_report(p_names, tmp_locations):
  report = {}
  for location in tmp_locations:
    for f in os.listdir(location):
      if f.startswith("levelops-brakeman") and f.endswith('.json'):
        match = result_project_extractor.match(f)
        if match:
          project_name = match.group(2)
          if project_name not in p_names:
            continue
          with open("{}/{}".format(location, f)) as content:
            report[project_name] = load(content)
  return report


if __name__ == "__main__":
  logging.basicConfig(level="INFO", format="[%(threadName)s] [%(levelname)s]: %(message)s")

  options, f_targets = get_options()
  validate_args(options, f_targets)
  
  formats, outputs = get_formats_and_outputs(options)
  
  output_location, reports_base = get_work_dirs(options)
  
  if output_location and os.path.isfile(output_location) and len(formats) > 1:
    log.error("Only one output format is allowed when the output location is a file.")
    sys.exit(1)

  reports_tmp = "{reports_base}/.levelops_tmp".format(reports_base=reports_base)
  reports_volume = "-v {reports_tmp}:/reports".format(reports_tmp=reports_tmp)

  installation_type = "new"
  if options.local:
    cmd = "git secrets {options}"
    # brakeman_output_dir = reports_tmp
    # output_files = get_output_files(brakeman_output_dir, formats)
    params = {"options": "--scan --no-index"}
    params_historic = {"options": "--scan-historic"}
  if options.docker:
    cmd = 'bash -c "docker run --rm -v {base_path}:/code --user $(id -u):$(id -g) levelops/levelops-git-secrets /bin/levelops-git-secrets {options} /code"'
    # brakeman_output_dir = "/reports"
    # output_files = get_output_files(brakeman_output_dir, formats)
    params = {"options": "{installation_type} current".format(installation_type=installation_type)}
    params_historic = {"options": "{installation_type} historic".format(installation_type=installation_type)}


  success = False
  runner = Runner(base_url=options.endpoint)
  start_time = time.time()
  p_names = set()
  results = {}
  try:
    with ToolRunner(command=cmd, max_concurrent=3, error_codes=set([1,126, 127, 128, 130, 137, 139, 143])) as s:
      for f_target in f_targets:
        log.info("scanning path: %s" % f_target)
        project_name, output, errors = s.scan_directory(base_path=f_target, params=params, tmp_location=reports_tmp)
        c_result = parse_output(output)
        project_name, output, errors = s.scan_directory(base_path=f_target, params=params_historic, tmp_location=reports_tmp)
        h_result = parse_output(output, is_historic=True)
        p_names.add(project_name)
        results[f_target] = {'project_name':project_name, 'results':merge_results(c_result, h_result)}
      s.wait_and_finish()
      success = s.are_all_successes()
      if success: 
        handle_output(formats, outputs, output_location, results)
  except Exception as e:
    message = "Couldn't successfully complete the scanning: %s", e
    log.error(message, exc_info=True)
    results = message
  except:
    error = sys.exc_info()
    message = "Couldn't successfully complete the scanning: %s - %s" % (error[0], error[1])
    log.error(message, error[2])
    results = message
  finally:
    end_time = time.time()
    if options.submit:
      # post success or failure to levelopsfor key in results:
      labels = options.labels if options.labels and type(options.labels) == dict else {}
      if type(results) is not dict:
        runner.submit(success=success, results={"output": results}, product_id=options.product, token=options.token, plugin=plugin, elapsed_time=(end_time - start_time), labels=labels, tags=options.tags)
      else:
        for key in results:
          result = results[key]
          labels.update({'project_name': [result['project_name']]})
        runner.submit(success=success, results=result, product_id=options.product, token=options.token, plugin=plugin, elapsed_time=(end_time - start_time), labels=labels, tags=options.tags)
  if success:
    sys.exit(0)
  else:
    sys.exit(1)