import os
from configparser import ConfigParser

ORIGIN_SECTION = 'remote "origin"'

def get_project_name(base_path):
    return _extract_project_name_from_git_config(base_path)


def _extract_project_name_from_git_config(base_path):
  git_config = "{}/.git/config".format(base_path)
  # if it is a git repo then get the project name from the remotes
  if not os.path.exists(git_config):
    return None
  config = ConfigParser()
  config.read(git_config)
  sections = [x for x,y in config.items()]
  if ORIGIN_SECTION in sections:
    project_name = _extract_project_name_from_git_remote(config[ORIGIN_SECTION])
    if project_name:
      return project_name
  for section_name, section in config.items():
    if "remote" in section_name:
      project_name = _extract_project_name_from_git_remote(section)
      if project_name:
        return project_name
  return None


def _extract_project_name_from_git_remote(section):
  url = section.get('url', None)
  if not url:
    return None
  project_name = url[url.rfind('/') + 1:].strip().replace('.git', '')
  if len(project_name) > 0:
    return project_name
  return None