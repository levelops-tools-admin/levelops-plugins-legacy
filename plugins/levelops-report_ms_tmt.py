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

from bs4 import BeautifulSoup
from bs4 import element
from re import compile, I, M
from shutil import copyfile, copy
from ujson import load, dump, dumps
from argparse import ArgumentParser
from uuid import uuid4

from sdk.fs_processor import Scanner
from sdk.wrapper import ToolRunner
from sdk.plugins import Runner, Plugin, labels_parser, default_plugin_options


log = logging.getLogger(__name__)
levelops_module_name = 'ms_tmt'
levelops_plugin_name = 'report_' + levelops_module_name
plugin = Plugin(name=levelops_plugin_name, version="1")

SUMMARY_BY_CAT_COLUMN_COUNT = 7
page_header_matcher = compile(pattern='^.*\s\|\s\d*$', flags=(I | M))
score_module_matcher = compile(pattern='^\((\d*)\)((\s+\w+)+)$', flags=(I | M))
number_matcher = compile(pattern='^\d+$', flags=(I | M))


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


def handle_output(formats, outputs, output_location, reslults):
  multiformat = len(formats) > 1
  generate_destination = True
  if os.path.isfile(output_location):
    generate_destination = False
    destination = output_location
  for target in results:
    result = results[target]
    project_name = result['project_name']
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
          print(dumps(result, indent=2, escape_forward_slashes=False))
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
          destination = "{dir}/levelops-{levelops_module_name}-{project}.{extension}".format(levelops_module_name=levelops_module_name, dir=output_location, project=project_name, extension=format)
          while os.path.exists(destination):
            tmp = destination
            consecutive += 1
            alt_project_name = project_name + "_" + str(consecutive)
            destination = "{dir}/levelops-{levelops_module_name}-{project}.{extension}".format(levelops_module_name=levelops_module_name, dir=output_location, project=alt_project_name, extension=format)

        with open(destination, 'w') as out:
          if format == "json":
            dump(result, out, indent=2, escape_forward_slashes=False)
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

  if len(f_targets) < 1:
    log.error("must provide a list of directories to scan (space separated)")
    sys.exit(1)


def get_options():
  parser = ArgumentParser(prog="Levelops Microsoft Threat Modeling Tool Report Plugin.", usage="./levelops-" + levelops_plugin_name + ".py (optional <flags>) <directory to scan>")
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


def normalize_field_name(line: str):
  return line.strip().lower().replace('  ', ' ').replace(' ', '_').replace('-','_')


def parse_report(report_file: str):
  with open(report_file) as contents:
    html = contents.read()
  parser = BeautifulSoup(html, 'html.parser')
  threats = {x.h4.attrs['id'].strip(): parse_threat(x) for x in parser.find_all('div', attrs={'class':'threat'})}
  summary, totals = parse_summary(parser)
  report = {
    "summary": {summary['threat_model_name']: totals},
    "metadata": summary,
    "data": threats,
    "aggregations": {}
    }
  report['aggregations'].update({summary['threat_model_name']: classify_threats(threats)})
  return report


def parse_summary(parser: BeautifulSoup):
  summary = {}
  summary_start = parser.find('h1', attrs={'class': 'title'})
  if 'Threat Modeling Report' not in summary_start.text:
    summary_start = parser.find('h1', attrs={'class': 'title'})
    return summary
  # end_of_summary = False
  # while not end_of_summary:
  element = summary_start.next_sibling
  if element.name == 'span' and 'Created on' in element.text:
    summary['created_at'] = element.text.replace('Created on', '').strip()
  summary_elements = [
    'Threat Model Name',
    'Owner',
    'Reviewer',
    'Owner',
    'Contributors',
    'Description',
    'Assumptions',
    'External Dependencies'
  ]
  end_of_summary_description = False
  while not end_of_summary_description:
    element = next_summary_element(element)
    if element.name and element.name == 'p':
      tmp = element.next_element
      if tmp.name and tmp.name  == 'strong':
        item_name = tmp.text.strip().replace(':', '')
        if item_name in summary_elements:
          summary[normalize_field_name(item_name)] = tmp.next_sibling.strip() if tmp.next_sibling else ''
    elif element.name and element.name == 'h3' and 'Threat Model Summary' in element.text:
      end_of_summary_description = True
  while not element or element.name != 'table':
    element = next_summary_element(element)
  totals = {}
  if element:
    for total in element.find_all('tr'):
      tmp = total.td
      value = next_summary_element(tmp)
      log.debug(value)
      totals[normalize_field_name(tmp.text)] = value.string.strip() if value.string else ''
  return summary, totals


def next_summary_element(element: element.Tag):
  element = element.next_sibling
  while not element.name:
    element = element.next_sibling
  return element


def parse_threat(threat: element.Tag):
  log.debug(threat)
  t_json = {normalize_field_name(x.attrs['id'][13:]): threat.find('td', attrs={'class': 'infotd', 'role': 'gridcell', 'headers': x.attrs['id']}).text.strip() for x in threat.find_all('td', attrs={'role': 'rowheader'})}
  t_json['summary'] = threat.h4.span.text
  text = threat.h4.span.next_sibling.string
  if text:
    text = [x.strip() for x in text.splitlines()]
    for line in text:
      if 'State:' in line:
        t_json['state'] = line[line.index('State:')+6:-1].strip()
      if 'Priority:' in line:
        t_json['priority'] = line[line.index('Priority:')+9:-1].strip()
  return t_json


def classify_threats(threats: dict):
  by_state = {}
  by_priority = {}
  for key in threats:
    threat = threats[key]
    priority = normalize_field_name(threat['priority'])
    p_count = by_priority.get(priority, 0)
    p_count += 1
    by_priority[priority] = p_count
    state = normalize_field_name(threat['state'])
    s_count = by_state.get(state, 0)
    s_count += 1
    by_state[state] = s_count
  return {'by_priority': by_priority, 'by_state': by_state}


if __name__ == "__main__":
  logging.basicConfig(level="INFO", format="[%(threadName)s] [%(levelname)s]: %(message)s")

  options, f_targets = get_options()
  validate_args(options, f_targets)

  formats, outputs = get_formats_and_outputs(options)

  output_location, reports_base = get_work_dirs(options)

  if output_location and os.path.isfile(output_location) and len(formats) > 1:
    log.error("Only one output format is allowed when the output location is a file.")
    sys.exit(1)

  # reports_tmp = "{reports_base}/.levelops_tmp".format(reports_base=reports_base)
  # reports_volume = "-v {reports_tmp}:/reports".format(reports_tmp=reports_tmp)

  success = False
  runner = Runner(base_url=options.endpoint)
  start_time = time.time()
  p_names = set()
  results = {}
  try:
    # with ToolRunner(command=cmd, max_concurrent=3, error_codes=set([1,126, 127, 128, 130, 137, 139, 143])) as s:
    for f_target in f_targets:
      log.info("scanning path: %s" % f_target)

      # output_file = reports_base.format(base_path=f_target) + '/levelops-praetorian-{uuid}.txt'.format(uuid=uuid4())

      report = parse_report(report_file=f_target)

      # print(dumps(report, indent=2, escape_forward_slashes=False))

      p_name = report['metadata'].get('threat_model_name','default')
      report['project_name'] = p_name
      results[f_target] = report
      success = True
        # s.wait_and_finish()
        # success = s.are_all_successes()
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