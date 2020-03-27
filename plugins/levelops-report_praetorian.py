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
from sdk.plugins import Runner, Plugin, labels_parser, default_plugin_options


log = logging.getLogger(__name__)
levelops_module_name = 'praetorian'
plugin = Plugin(name="report_" + levelops_module_name, version="1")

SUMMARY_BY_CAT_COLUMN_COUNT = 7
page_header_matcher = compile(pattern='^.*\s\|\s\d*$', flags=(I | M))
score_module_matcher = compile(pattern='^\((\d*)\)((\s+\w+)+)$', flags=(I | M))
number_matcher = compile(pattern='^\d+$', flags=(I | M))

OUTPUT_TYPES = ((".htm", "html"),
                (".html", "html"),
                (".xml", "xml"),
                (".tag", "tag"))


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
  if (options.json or options.csv) and not options.output_file and not options.print_results:
      log.error("To use --csv or --json pass either the --print-results flag (to print to the console) or the --out flag (to write to a file).")
      sys.exit(1)

  if len(f_targets) < 1:
    log.error("must provide a list of directories to scan (space separated)")
    sys.exit(1)


def get_options():
  parser = ArgumentParser(prog="Levelops Praetorian Report Plugin.", usage="./levelops-report_praetorian.py (optional <flags>) <directory to scan>")
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


def section_starts_with(line: str):
  partial = True
  for section in SECTIONS_MAP:
    if section == line:
      return section, SECTIONS_MAP[section], not partial
    if section.startswith(line):
      return section, SECTIONS_MAP[section], partial
  return None, None, not partial


def finding_starts_with(line: str, titles: dict):
  partial = True
  test_line = line.lower()
  for title in titles:
    if title == test_line:
      return titles[title], not partial
    if title.startswith(test_line):
      return titles[title], partial
  return None, not partial


def is_end_of_page(line: str):
  return line == 'W W W . P R A E T O R I A N . C O M'


def is_start_of_page(line: str):
  return page_header_matcher.match(line) is not None


def is_executive_conclusion(line: str):
  return line == 'CONCLUSION'


def is_at_service_valuation(line: str):
  return 'Service' == line


def is_end_of_service_valuation(prev_line: str):
  return 'Grade' == prev_line


def process_service_valuation(lines: list):
  for line in lines:
    if line == 'Service':
      set_service = True
      continue
    if line == 'Security':
      set_security = True
      continue
    if line == 'Grade':
      set_grade = True
      continue
    if set_service:
      service = line
      set_service = False
      continue
    if set_security:
      security = line
      set_security = False
      continue
    if set_grade:
      grade = line
      set_grade = False
      continue
  return {
    'service': service, 
    'security': security, 
    'grade': grade, 
    'issues_summary': {}, 
    'assesments': {
      'web_application_assesment': {}
    }
  }


def is_at_vuln_table_page(line: str):
  return 'Current State Analysis' == line


def is_start_of_table(lines: list):
  size = len(lines)
  return lines[size-1] == 'Findings' and \
    lines[size-2] == 'Total' and \
    lines[size-3] == 'Info' and \
    lines[size-4] == 'Low' and \
    lines[size-5] == 'Med' and \
    lines[size-6] == 'Critical High'


def is_at_end_of_table(lines: list, cat_count: int):
  line_count = len(lines)
  if line_count < SUMMARY_BY_CAT_COLUMN_COUNT:
    return False
  return (cat_count * SUMMARY_BY_CAT_COLUMN_COUNT) == line_count


def process_summary_by_category(lines: list):
  by_categories = {}
  categories = []
  c_count = len(lines)/SUMMARY_BY_CAT_COLUMN_COUNT
  c_index = 0
  severity_index = 0
  severities = [
    "critical",
    "high",
    "med",
    "low",
    "info",
    "total"
  ]
  for line in lines:
    if number_matcher.match(line) is None:
      by_categories[line.lower()] = {}
      categories.append(line.lower())
      continue
    if c_index == c_count:
      c_index = 0
      severity_index += 1
    by_categories[categories[c_index]][severities[severity_index]] = line
    c_index += 1
  totals = by_categories.pop('total')
  return {
        "total_critical": totals['critical'],
        "total_high": totals['high'],
        "total_med": totals['med'],
        "total_low": totals['low'],
        "total_info": totals['info'],
        "total_issues": totals['total'],
        "by_categories": by_categories
  }


def is_findings_summary_section(line: str):
  if line == 'Summary of Weaknesses':
    return True
  return False


def is_end_findings_summary(line: str, previous_marker_seen: bool):
  new_marker_seen = line == 'Critical Risk Findings'
  return new_marker_seen and previous_marker_seen, new_marker_seen or previous_marker_seen


def normalize_finding_name(line: str):
  return line.strip().lower().replace('  ', ' ').replace(' ', '_')


FINDING_SEVERITY_MAP = {
  'critical risk findings': 'critical_risk',
  'high risk findings': 'high_risk',
  'medium risk findings': 'medium_risk',
  'low risk findings': 'low_risk',
  'informational risk findings': 'informational_risk'
}


def process_findings_summary(lines: list):
  findings_titles = {}
  findings = {"critical_risk": {},"high_risk": {},"medium_risk": {},"low_risk": {},"informational_risk": {}}
  risk = None
  for line in lines:
    if not line.startswith('•'):
      for severity in FINDING_SEVERITY_MAP:
        if severity == line.lower():
          risk = findings[FINDING_SEVERITY_MAP[severity]]
          break
    else:
      finding_name = line[2:]
      if finding_name.lower() == 'none':
        continue
      risk[normalize_finding_name(finding_name)] = section = {}
      findings_titles[finding_name.lower()] = section
  return findings, findings_titles


def is_group_title(line: str):
  for group in FINDING_SEVERITY_MAP:
    if group == line.lower():
      return True
  return False


def text_processor(lines: list):
  return ' '.join(lines)


def category_processor(lines: list):
  if True:
    return {}
  reading_values = False
  set_cat = False
  set_wasc = False
  set_cwe = False
  set_sans = False
  set_owasp = False
  for line in lines:
    if not reading_values and line != 'OWASP Top 10':
      continue
    elif line != 'OWASP Top 10':
      reading_values = True
      set_cat = True
      continue
    line = line.replace('—', '')
    if set_cat:
      category = line
      set_cat = False
      set_wasc = True
      continue
    if set_wasc:
      wasc = line
      set_wasc = False
      set_cwe = True
      continue
    if set_cwe:
      cwe = line
      set_cwe = False
      set_snas = True
      continue
    if set_sans:
      sans = line
      set_sans = False
      set_owasp = True
      continue
    if set_owasp:
      owasp = line
      set_owasp = False
      continue
  return {
    'category': category,
    'WASC': wasc,
    'CWE': cwe,
    'SANS Top 25': sans,
    'OWASP Top 10': owasp 
  }


SCORE_MODULES = [
  "access vector",
  "attack feasibility",
  "authentication",
  "compromise impact",
  "business value"
  ]


def score_processor(lines: list):
  score = {}
  for line in lines:
    if not line.startswith('('):
      for item in SCORE_MODULES:
        if item == line.lower():
          module = normalize_finding_name(item)
          break
    else:
      result = score_module_matcher.match(line)
      if result:
        score[module] = {'value': result.group(1), 'description': result.group(2).strip()}
  return score


SECTIONS_MAP = {
  "Vulnerability Description": text_processor,
  "Impact": text_processor,
  "Application Impacted": text_processor,
  "Verification and Attack Information": text_processor,
  "Recommendation": text_processor,
  "findings_summary_marker_seenerences": text_processor,
  "Category": category_processor,
  "Link Impacted": text_processor,
  "Service Impacted": text_processor,
  "Status": text_processor,
  "Code Impacted": text_processor,
  "Status": text_processor,
  "Instances Impacted": text_processor,
  "GraphQL Query Impacted": text_processor,
  "Cookies Impacted": text_processor,
  "Endpoint Impacted": text_processor,
  "Systems Impacted": text_processor,
  "Cluster Impacted": text_processor
}


def is_end_of_findings(line: str):
  return 'owasp top 10 comparison' == line.lower()


def parse_output(output: str):
  result = None
  findings_summary_marker_seen = False
  with open(output) as text:
    prev_section = None
    section_contents = []
    at_end_of_page = False
    at_findings_summary = False
    at_findings = False
    capture_content = False
    collecting_finding_details = False
    findings = None
    titles = None
    is_title_partial = False
    partial_title = ''
    partial_section_name = ''
    is_section_name_partial = False
    prev_section_processor = None
    at_executive_conclusion = False
    at_service_valuation = False
    at_end_of_service_valuation = False
    prev_line = ''
    at_vuln_table_page = False
    at_table = False
    is_table_number_first_match = True
    at_end_of_table = False
    done_executive_conclusion = False
    for line in text.readlines():
      line = line.strip()
      if len(line) <= 0:
        continue
      # Detecting start of page
      if at_end_of_page:
        if is_start_of_page(line) == True:
          at_end_of_page = False
        continue
      # Detecting end of page
      if is_end_of_page(line):
        at_end_of_page = True
        continue

      # Decting summary
      if not done_executive_conclusion \
        and not at_findings_summary \
        and not at_end_of_table \
        and not at_vuln_table_page \
        and is_executive_conclusion(line):
        at_executive_conclusion = True
        continue
      if not at_service_valuation and not at_end_of_service_valuation and at_executive_conclusion:
        at_service_valuation = is_at_service_valuation(line)
      if at_executive_conclusion and not at_service_valuation:
        continue
      elif at_service_valuation:
        at_end_of_service_valuation = is_end_of_service_valuation(prev_line)
        if at_end_of_service_valuation:
          section_contents.append(line)
          result = process_service_valuation(section_contents)
          section_contents = []
          at_executive_conclusion = False
          at_service_valuation = False
          done_executive_conclusion = True
          continue
        prev_line = line
        section_contents.append(line)
        continue
      # Detecting Vulneravilities Table
      if at_end_of_service_valuation and not at_findings_summary and not at_vuln_table_page:
        at_vuln_table_page = is_at_vuln_table_page(line)
        continue
      if at_vuln_table_page and not at_table:
        section_contents.append(line)
        if not at_table:
          at_table = is_start_of_table(section_contents)
          if at_table:
            section_contents = []
        continue
      if at_table:
        if number_matcher.match(line):
          section_contents.append(line)
          if is_table_number_first_match:
            cat_table_count = len(section_contents)-1
            is_table_number_first_match = False
          else:
            at_end_of_table = is_at_end_of_table(section_contents, cat_table_count)
            if at_end_of_table:
              result['issues_summary'].update(process_summary_by_category(section_contents))
              section_contents = []
              at_table = False
              at_vuln_table_page = False
              at_end_of_service_valuation = False
          continue
        section_contents.append(line)
        continue
      # Decting findings
      if not at_findings_summary and is_findings_summary_section(line) == True:
        at_findings_summary = True
        continue
      if at_findings_summary:
        at_end_of_summary, findings_summary_marker_seen = is_end_findings_summary(line, findings_summary_marker_seen)
        if at_end_of_summary:
          result['assesments']['web_application_assesment']['findings'], titles = process_findings_summary(section_contents)
          section_contents = []
          at_findings_summary = False
          at_findings = True
          capture_content = False
          continue
        if findings_summary_marker_seen:
          section_contents.append(line)
        continue
      # start parsing the findings only if we are past the summary 
      if not at_findings:
        continue
      # skip the finding's severity group title
      if is_group_title(line):
        continue
      # we break if we are done with the findings section
      if is_end_of_findings(line):
        break
      # Decting start of new finding
      if is_title_partial:
        test_line = partial_title + line
      else:
        test_line = line
      new_finding, is_title_partial = finding_starts_with(test_line, titles)

      if new_finding is None and partial_title != '':
        if capture_content:
          section_contents.append(partial_title[:-1])
        partial_title = ''
        new_finding, is_title_partial = finding_starts_with(line, titles)
      if new_finding is not None:
        if is_title_partial:
          partial_title += line + ' '
          continue
        # flush the previous buffer before rolling over to the next finding
        if prev_section == 'Category':
          finding['meta'].update(category_processor(section_contents))
        elif prev_section: 
          finding[normalize_finding_name(prev_section)] = prev_section_processor(section_contents)
        section_contents = []
        prev_section = None
        prev_section_processor = None
        section_processor = None
        is_section_name_partial = False
        partial_section_name = ''
        partial_title = ''
        is_title_partial = False
        finding = new_finding
        capture_content = True
        continue

      if is_section_name_partial:
        test_section_name = partial_section_name + line
      else:
        test_section_name = line
      # Decting start of new section
      new_section, section_processor, is_section_name_partial = section_starts_with(test_section_name)
      if not new_section and partial_section_name != '':
        if capture_content:
          section_contents.append(partial_section_name[:-1])
        partial_section_name = ''
        new_section, section_processor, is_section_name_partial = section_starts_with(line)
      if new_section:
        if is_section_name_partial:
          partial_section_name += line + ' '
          continue
        partial_section_name = ''
        # capture score
        if prev_section is None:
          meta = finding.get('meta', {})
          meta['score'] = score_processor(section_contents)
          finding['meta'] = meta
        elif prev_section == 'Category':
          finding['meta'].update(category_processor(section_contents))
        else:
          finding[normalize_finding_name(prev_section)] = prev_section_processor(section_contents)
        prev_section = new_section
        prev_section_processor = section_processor
        section_contents = []
        capture_content = True
        continue
      if capture_content:
        section_contents.append(line)
  return result


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

      output_file = reports_base.format(base_path=f_target) + '/levelops-praetorian-{uuid}.txt'.format(uuid=uuid4())

      extract_text(
        files=[f_target], 
        boxes_flow=0.5, 
        line_margin=0.5, 
        word_margin=0.1, 
        char_margin=2.0, 
        detect_vertical=True, 
        rotation=0, 
        disable_caching=False, 
        outfile=output_file)

      report = parse_output(output=output_file)

      print(dumps(report, indent=2))
      p_name = report.get('service','default')
      results[f_target] = {p_name: {'project_name': p_name, 'results': report}}
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
        runner.submit(success=success, results={"output": results}, product_id=options.product, token=options.token, plugin=plugin, elapsed_time=(end_time - start_time), labels=labels)
      else:
        for key in results:
          result = results[key]
          labels.update({'project_name': [result['project_name']]})
          runner.submit(success=success, results=result, product_id=options.product, token=options.token, plugin=plugin, elapsed_time=(end_time - start_time), labels=labels)
  if success:
    sys.exit(0)
  else:
    sys.exit(1)