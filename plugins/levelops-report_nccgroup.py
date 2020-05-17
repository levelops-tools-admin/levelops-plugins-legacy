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
import pdfminer.high_level
import pdfminer.layout
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from re import compile, I, M
from shutil import copyfile, copy
from ujson import load, dump, dumps
from argparse import ArgumentParser
from uuid import uuid4

from sdk.fs_processor import Scanner
from sdk.wrapper import ToolRunner
from sdk.parser import SectionedTextParser, Section, SectionType
from sdk.plugins import Runner, Plugin, labels_parser, default_plugin_options


log = logging.getLogger(__name__)
levelops_module_name = 'nccgroup'
plugin = Plugin(name="report_" + levelops_module_name, version="1")

footnote_matcher = compile(pattern='^.*\/\sNCC Group Confidential$', flags=(I | M))
wattermark_matcher = compile(pattern='^.*\/\sNCC Group Confidential$', flags=(I | M))
page_footer_matcher = compile(pattern='^\d+\s\|\s.+$', flags=(I | M))
title_date_matcher = compile(pattern='^(\w+\s[0,1,2,3]?\d,\s[1,2][9,0][6,7,8,9,0,1,2]\d).*$', flags=(I | M))

CONTINUE_COLLECTING = True
DO_NOT_CONTINUE_COLLECTING = False


def is_start_of_findings(line: str, previous_line: str, contents: list, completed_sections: list):
  # need to return whether the start of the section is in the current line or the privous one..
  # potentially adding also next line check
  return line == "Finding Details" or line == 'Vulnerability Details'


def is_end_of_findings(line: str, previous_line: str, contents: list, completed_sections: list):
  return line.startswith('Appendix A:')


def is_start_of_finding(line: str, previous_line: str, contents: list, completed_sections: list):
  return line.startswith('Finding') or line.startswith('Vulnerability') or (line.startswith('Risk')
          and (previous_line.startswith('Finding') or previous_line.startswith('Vulnerability')))


def is_end_of_finding(line: str, previous_line: str, contents: list, completed_sections: list):
  return line.startswith('Finding') or line.startswith('Vulnerability')


def collect_subs(title, line, previous_line, sub_contents, fields):
  if previous_line.startswith(title):
    sub_contents.append(previous_line)
  for field in fields:
    if field == title:
      continue
    if line.startswith(field):
      return DO_NOT_CONTINUE_COLLECTING, DO_NOT_CONTINUE_COLLECTING, ' '.join(sub_contents).replace(title + ' ', '')
  sub_contents.append(line)
  return CONTINUE_COLLECTING, CONTINUE_COLLECTING, None


def finding_parser(last_line: str, contents: list):
  section_name = None
  risk = None
  identifier = None
  category = None
  component = None
  location = None
  status = None
  impact = None
  impact_description = None
  description = None
  recommendation = None
  steps = None
  exploitability = None
  collecting_risk = False
  collecting_description = False
  collecting_location = False
  collecting_impact_description = False
  collecting_recommendation = False
  collecting_steps = False
  collecting = False
  previous_line = ''
  sub_contents = []
  fields = ['Identifier', 'Identiﬁer', 'Category', 'Location', 'Impact', 'Client Vulnerability ID', 'Description', 'Recommendation', 'Reproduction Steps']
  for line in contents:
    if (collecting and collecting_risk) or (not collecting and line.startswith('Risk') and (not risk or len(risk) < 1)):
      for field in fields:
        if field == 'Risk':
          continue
        if line.startswith(field) and not line.startswith('Impact:'):
          collecting_risk = False
          collecting = False
          risk = ' '.join(sub_contents).replace('Risk ', '')
          impact_index = risk.index('Impact:')
          exploitability_index = risk.index('Exploitability:')
          impact = normalize_finding_name(risk[impact_index + 7:exploitability_index].strip().replace(',', ''))
          exploitability = normalize_finding_name(risk[exploitability_index + 15:].strip())
          risk = normalize_finding_name(risk[:impact_index].strip())
          sub_contents = []
          break
        else:
          collecting_risk = True
      if collecting_risk:
        collecting = True
        sub_contents.append(line)
        previous_line = line
        continue
    if (collecting and collecting_description) or (not collecting and (line.startswith('Description') or previous_line.startswith('Description')) and (not description or len(description) < 1)):
      collecting, collecting_description, description = collect_subs('Description', line, previous_line, sub_contents, fields)
      if collecting_description:
        previous_line = line
        continue
      sub_contents = []
    if (collecting and collecting_location) or (not collecting and (line.startswith('Location') or previous_line.startswith('Location')) and (not location or len(location) < 1)):
      collecting, collecting_location, location = collect_subs('Location', line, previous_line, sub_contents, fields)
      if collecting_location:
        previous_line = line
        continue
      sub_contents = []
    if (collecting and collecting_impact_description) or (not collecting and (line.startswith('Impact') or previous_line.startswith('Impact')) and (not impact_description or len(impact_description) < 1)):
      collecting, collecting_impact_description, impact_description = collect_subs('Impact', line, previous_line, sub_contents, fields)
      if collecting_impact_description:
        previous_line = line
        continue
      sub_contents = []
    if (collecting and collecting_recommendation) or (not collecting and (line.startswith('Recommendation') or previous_line.startswith('Recommendation')) and (not recommendation or len(recommendation) < 1)):
      collecting, collecting_recommendation, recommendation = collect_subs('Recommendation', line, previous_line, sub_contents, fields)
      if collecting_recommendation:
        previous_line = line
        continue
      sub_contents = []
    if (collecting and collecting_steps) or (not collecting and (line.startswith('Reproduction Steps') or previous_line.startswith('Reproduction Steps')) and (not steps or len(steps) < 1)):
      collecting, collecting_steps, steps = collect_subs('Reproduction Steps', line, previous_line, sub_contents, fields)
      if collecting_steps:
        previous_line = line
        continue
      sub_contents = []
    elif line.startswith('Finding') or line.startswith('Vulnerability') and not section_name:
      section_name = line.replace('Finding ', '').replace('Vulnerability ', '').strip()
    elif (line.startswith('Identifier') or line.startswith('Identiﬁer') or previous_line.startswith('Identifier') or previous_line.startswith('Identiﬁer')) and (not identifier or len(identifier) < 1):
      identifier = line.replace('Identifier ', '').replace('Identifier', '').replace('Identiﬁer ', '').replace('Identiﬁer', '').strip()
    elif line.startswith('Category') or previous_line.startswith('Category') and (not category or len(category) < 1):
      category = line.replace('Category ', '').replace('Category', '').strip()
    elif line.startswith('Component') or previous_line.startswith('Component') and (not component or len(component) < 1):
      component = line.replace('Component ', '').replace('Component', '').strip()
    elif line.startswith('Status') or previous_line.startswith('Status') and (not status or len(status) < 1):
      status = line.replace('Status ', '').replace('Status', '').strip()
    previous_line = line

  if len(sub_contents) > 0:
    if collecting_description:
      description = ' '.join(sub_contents).replace('Descripton ', '')
    if collecting_impact_description:
      impact_description = ' '.join(sub_contents).replace('Impact ', '')
    if collecting_location:
      location = ' '.join(sub_contents).replace('Location ', '')
    if collecting_recommendation:
      recommendation = ' '.join(sub_contents).replace('Recommendation ', '')
    if collecting_risk:
      risk = ' '.join(sub_contents).replace('Risk ', '')
    if collecting_steps:
      steps = ' '.join(sub_contents).replace('Reproduction Steps ', '')
  
  if exploitability and 'Identifier ' in exploitability:
    identifier_index = exploitability.index('Identifier ')
    identifier = exploitability[identifier_index + 10:].strip()
    exploitability = exploitability[:identifier_index].strip()
  return 'data', {
    section_name: {'risk': risk,
      'identifier': identifier,
      'component': component,
      'category': category,
      'location': location,
      'status': status,
      'description': description,
      'exploitability': exploitability,
      'impact': impact,
      'impact_description': impact_description,
      'recommendation': recommendation,
      'reproduction_steps': steps
    }
  }


def ignore_line_evaluator(line):
  return page_footer_matcher.match(line) is not None or wattermark_matcher.match(line) is not None


def is_start_of_title(line: str, previous_line: str, contents: list, completed_sections: list):
  return len(completed_sections) == 0 and len(contents) == 0


def is_end_of_title(line: str, previous_line: str, contents: list, completed_sections: list):
  if len(completed_sections) == 0:
    return title_date_matcher.match(line) is not None


def parse_title(last_line: str, contents: list):
  date = title_date_matcher.match(last_line).group(1)
  title = ' '.join(contents[:-1])
  return 'metadata', {'title': title, 'date': date}


sections = [
  Section(
    SectionType.METADATA,
    is_start_of_title,
    is_end_of_title,
    None,
    parse_title
    ),
  Section(
    SectionType.ISSUES,
    is_start_of_findings,
    is_end_of_findings,
    Section(
      SectionType.ISSUE,
      is_start_of_finding,
      is_end_of_finding,
      None,
      finding_parser
    ),
    None
  )
]


def extract_text(files=[], outfile='-',
                 no_laparams=False, all_texts=None, detect_vertical=None,
                 word_margin=None, char_margin=None, line_margin=None,
                 boxes_flow=None, output_type='text', codec='utf-8',
                 strip_control=False, maxpages=0, page_numbers=None,
                 password="", scale=1.0, rotation=0, layoutmode='normal',
                 output_dir=None, debug=False, disable_caching=False,
                 **kwargs):
    if not files:
        raise ValueError("Must provide files to work upon!")

    # If any LAParams group arguments were passed,
    # create an LAParams object and
    # populate with given args. Otherwise, set it to None.
    if not no_laparams:
        laparams = pdfminer.layout.LAParams()
        for param in ("all_texts", "detect_vertical", "word_margin",
                      "char_margin", "line_margin", "boxes_flow"):
            paramv = locals().get(param, None)
            if paramv is not None:
                setattr(laparams, param, paramv)
    else:
        laparams = None

    if output_type == "text" and outfile != "-":
        for override, alttype in OUTPUT_TYPES:
            if outfile.endswith(override):
                output_type = alttype

    if outfile == "-":
        outfp = sys.stdout
        if outfp.encoding is not None:
            codec = 'utf-8'
    else:
        outfp = open(outfile, "wb")

    for fname in files:
        with open(fname, "rb") as fp:
            pdfminer.high_level.extract_text_to_fp(fp, **locals())
    return outfp


def get_formats_and_outputs(options):
  formats = []
  if options.json:
    formats.append("json")
  # if options.csv:
  #   formats.append("csv")
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
          destination = "{dir}/levelops-{levelops_module_name}-{project}.{extension}".format(levelops_module_name=levelops_module_name, dir=output_location, project=project_name, extension=format)
          while os.path.exists(destination):
            tmp = destination
            consecutive += 1
            alt_project_name = project_name + "_" + str(consecutive)
            destination = "{dir}/levelops-{levelops_module_name}-{project}.{extension}".format(levelops_module_name=levelops_module_name, dir=output_location, project=alt_project_name, extension=format)

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
  if options.json and not options.output_file and not options.print_results:
      log.error("To use --csv or --json pass either the --print-results flag (to print to the console) or the --out flag (to write to a file).")
      sys.exit(1)

  if len(f_targets) < 1:
    log.error("must provide a list of directories to scan (space separated)")
    sys.exit(1)


def get_options():
  parser = ArgumentParser(prog="Levelops Praetorian Report Plugin.", usage="./levelops-report_praetorian.py (optional <flags>) <directory to scan>")
  parser.add_argument("--resubmit-report", dest="resubmit_report", help="Will resubmit the report passes in the command line (path to file) with the product, tags, and labels specified.", action="store_true")
  for parser_option in default_plugin_options:
    if parser_option['kwords']['dest'] == 'csv': # CSV not supported for now
      continue
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


def normalize_finding_name(line: str):
  return line.strip().lower().replace('  ', ' ').replace(' ', '_')


def handle_submit(options, results, elapsed_time, success=False):
  runner = Runner(base_url=options.endpoint)
  if options.submit:
    # post success or failure to levelopsfor key in results:
    labels = options.labels if options.labels and type(options.labels) == dict else {}
    if type(results) is not dict:
      runner.submit(success=success, results={"output": results}, product_id=options.product, token=options.token, plugin=plugin, elapsed_time=elapsed_time, labels=labels, tags=options.tags)
    else:
      for key in results:
        result = results[key]
        labels.update({'project_name': [result['project_name']]})
        runner.submit(success=success, results=result, product_id=options.product, token=options.token, plugin=plugin, elapsed_time=elapsed_time, labels=labels, tags=options.tags)


if __name__ == "__main__":
  logging.basicConfig(level="INFO", format="[%(threadName)s] [%(levelname)s]: %(message)s")

  options, f_targets = get_options()
  validate_args(options, f_targets)

  if options.resubmit_report:
    results = {}
    for f_target in f_targets:
      with open(f_target) as file:
        result = load(file)
        # p_name = result.get('metadata',{}).get('title', 'default')
        # result['project_name'] = p_name
        results[f_target] = result
    handle_submit(options, results, 0, success=True)
    sys.exit(0)
  formats, outputs = get_formats_and_outputs(options)

  output_location, reports_base = get_work_dirs(options)

  if output_location and os.path.isfile(output_location) and len(formats) > 1:
    log.error("Only one output format is allowed when the output location is a file.")
    sys.exit(1)

  # reports_tmp = "{reports_base}/.levelops_tmp".format(reports_base=reports_base)
  # reports_volume = "-v {reports_tmp}:/reports".format(reports_tmp=reports_tmp)
  
  success = False
  start_time = time.time()
  p_names = set()
  results = {}
  try:
    # with ToolRunner(command=cmd, max_concurrent=3, error_codes=set([1,126, 127, 128, 130, 137, 139, 143])) as s:
    for f_target in f_targets:
      log.info("scanning path: %s" % f_target)
      
      output_file = reports_base.format(base_path=f_target) + '/levelops-{module}-{uuid}.txt'.format(module=levelops_module_name, uuid=uuid4())

      # extract_text(
      #   files=[f_target], 
      #   boxes_flow=0.5, 
      #   line_margin=0.5, 
      #   word_margin=0.1, 
      #   char_margin=2.0, 
      #   detect_vertical=True, 
      #   rotation=0, 
      #   disable_caching=False, 
      #   outfile=output_file)

      # parser = SectionedTextParser(sections=sections, file_location=output_file, ignore_line=ignore_line_evaluator)

      parser = SectionedTextParser(sections=sections, file_location='/tmp/ncc2.txt', ignore_line=ignore_line_evaluator)

      report = parser.parse()

      # print(dumps(report, indent=2, escape_forward_slashes=False))
      
      # result = normalize_report(report)

      # p_name = report.get('service','default')
      report['project_name'] = report.get('metadata', {}).get('title', 'NCC Group Report')
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
    handle_submit(options, results, (end_time - start_time), success=True)
  if success:
    sys.exit(0)
  else:
    sys.exit(1)