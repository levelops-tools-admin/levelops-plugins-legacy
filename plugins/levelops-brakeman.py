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
from ujson import load
from argparse import ArgumentParser

from sdk.fs_processor import Scanner
from sdk.wrapper import ToolRunner
from sdk.plugins import Runner, Plugin, labels_parser, default_plugin_options


log = logging.getLogger(__name__)
plugin = Plugin(name="sast_brakeman", version="1")

result_project_extractor = compile(pattern='^.*(levelops-brakeman-(.*)).json\s*$', flags=(I | M))

def get_formats_and_outputs(options):
  formats = []
  if options.json or options.submit:
    formats.append("json")
  if options.csv:
    formats.append("csv")
  if options.html:
    formats.append("html")
  if options.table:
    formats.append("table")
  if options.markdown:
    formats.append("md")
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


def handle_output(formats, outputs, output_location, tmp_locations):
  m_files = {}
  # the if is a small optimization
  if not os.path.isfile(output_location):
    for location in tmp_locations:
      for f in os.listdir(location):
        if f.startswith("levelops-brakeman"):
          extension = f[f.rfind(".") + 1:]
          if extension in formats:
            files = m_files.get(extension, [])
            files.append("{}/{}".format(location, f))
            m_files[extension] = files
  multiformat = len(formats) > 1
  for format in m_files:
    sources = m_files[format]
    for source in sources:
      if "print" in outputs:
        if multiformat:
          print("")
          print("")
          print("-------------------------")
          print("      %s" % format)
          print("-------------------------")
          print("")
        with open(source) as f:
          print(f.read())
      if "file" in outputs:
        # if the destination is a file then there should be only one format
        # and we can copy the source file to the destination file.
        # Or
        # if the destination is a directory then we will copy the specific format files
        # from every tmp location to the destination directory
        copy(src=source, dst=output_location)


def validate_args(options, f_targets):
  if options.debug:
      log.setLevel('DEBUG')
  if options.submit:
    if not options.product or not options.token:
      log.error("Both product and token options are required if the submit flag is present.")
      sys.exit(1)
  if (options.json or options.csv or options.html or options.table or options.markdown) and not options.output_file and not options.print_results:
      log.error("To use --csv, --json, --html, --table or --markdown either the --print-results flag (to print to the console) or the --out flag (to write to a file) must be specified.")
      sys.exit(1)
  if not options.docker and not options.gem:
    log.error("A excecution mode is needed. Please select either --docker or --gem")
    sys.exit(1)
  if options.docker and options.gem:
    log.error("Only one excecution mode can be specified per invocation (--docker or --gem).")
    sys.exit(1)

  if len(f_targets) < 1:
    log.error("must provide a list of directories to scan (space separated)")
    sys.exit(1)


def get_options():
  parser = ArgumentParser(prog="Levelops brakeman scanner.", usage="./levelops-brakeman.py (optional <flags>) <directory to scan>")
  parser.add_argument('--docker', dest='docker', help='Will run in docker mode, docker command line needs to be in the path and the user that runs the plugin needs to have permissions to run docker containers.', action="store_true")
  parser.add_argument('--gem', dest='gem', help='Will run in gem mode, the brakeman gem must be installed and available in the env.', action="store_true")
  parser.add_argument('--html', dest='html', help='If present, the output of the script will be in html format.', action='store_true')
  parser.add_argument('--table', dest='table', help='If present, the output of the script will be in table format.', action='store_true')
  parser.add_argument('--markdown', dest='markdown', help='If present, the output of the script will be in markdown format.', action='store_true')
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

  if options.gem:
    cmd = "brakeman --quiet {output_files} {base_path}"
    brakeman_output_dir = reports_tmp
    output_files = get_output_files(brakeman_output_dir, formats)
    params = {"output_files":output_files} 
  if options.docker:
    cmd = 'bash -c "docker run --rm -v {base_path}:/code {reports_volume} --user $(id -u):$(id -g) presidentbeef/brakeman --quiet {output_files}"'
    brakeman_output_dir = "/reports"
    output_files = get_output_files(brakeman_output_dir, formats)
    params = {"reports_volume": reports_volume, "output_files":output_files}


  success = False
  runner = Runner(base_url=options.endpoint)
  start_time = time.time()
  p_names = set()
  try:
    with ToolRunner(command=cmd, max_concurrent=3, error_codes=set([1,126, 127, 128, 130, 137, 139, 143])) as s:
      for f_target in f_targets:
        log.info("scanning path: %s" % f_target)
        project_name, out, errors = s.scan_directory(base_path=f_target, params=params, tmp_location=reports_tmp)
        p_names.add(project_name)
      s.wait_and_finish()
      success = s.are_all_successes()
      if success: 
        if options.submit:
          results = get_results_report(p_names, s.get_tmp_locations())
        handle_output(formats, outputs, output_location, s.get_tmp_locations())
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
          labels.update({'project_name': [key]})
          runner.submit(success=success, results=result, product_id=options.product, token=options.token, plugin=plugin, elapsed_time=(end_time - start_time), labels=labels, tags=options.tags)
  if success:
    sys.exit(0)
  else:
    sys.exit(1)