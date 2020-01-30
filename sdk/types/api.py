from functools import reduce

class Endpoint(object):
  def __init__(self, path, headers=None, params=None, produced_type=None, accepted_type=None, method=''):
    self.path=path
    # self.headers=headers
    # self.params=params
    # self.produced_type=produced_type
    # self.accepted_type=accepted_type
    self.method = method
  
  def __eq__(self, other):
    # type: (API) -> bool
    return self.path == other.path \
            and self.method == other.method 
            # and self.headers == other.headers \
            # and self.params == other.params \
            # and self.produced_type == other.produced_type \
            # and self.accepted_type == other.accepted_type \
  
  def __hash__(self):
    # return hash((self.path, self.headers, self.params, self.produced_type, self.accepted_type))
    return hash((self.path))

  def __str__(self):
    return "path=%s, headers=%s, params=%s, produced_type=%s, accepted_type=%s" % (self.path, self.headers, self.params, self.produced_type, self.accepted_type)


class API(object):
  def __init__(self, name, endpoints=None, base_path='', repo=None):
    self.name = name
    self.base_path = base_path
    if not endpoints:
      endpoints = set()
    self.endpoints = endpoints
    # self.repo = repo
  
  def add_endpoint(self, endpoint):
    self.endpoints.add(endpoint)
  
  def __eq__(self, other):
    # type: (API) -> bool
    return self.name == other.name \
            and self.base_path == other.base_path \
            and self.endpoints == other.endpoints
            # and self.repo == other.repo \
  
  def __hash__(self):
    if len(self.endpoints) > 0:
      end_h = reduce(lambda x,y: x.__hash__() + y.__hash__(), self.endpoints)
    else:
      end_h = ""
    # return hash((self.name, self.base_path, self.repo, end_h ))
    return hash((self.name, self.base_path, end_h ))
  
  def __str__(self):
    # return "name=%s, base_path=%s, repo=%s, endpoints=%s" % (self.name, self.base_path, self.repo, [str(x) for x in self.endpoints])
    return "name=%s, base_path=%s, repo=%s, endpoints=%s" % (self.name, self.base_path, [str(x) for x in self.endpoints])



"""
Report:
  repo:
  commit:
  tags:
  apis:
  - name
    base_path:
    endpoints:
    - path
      headers
      params
      produced_type
      accepted_type
    - Endpoint
    - Endpoint
  - API 
  - API
"""