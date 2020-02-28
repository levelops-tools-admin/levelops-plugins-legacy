import os
from .git import get_project_name as get_git_project_name


def get_project_name(base_path):
  project_name = get_git_project_name(base_path)
  if project_name:
    return project_name
  # use the sources directory name as project name
  full_path = os.path.realpath(base_path)
  return full_path[full_path.rfind('/') + 1:]