
class Report(object):
  def __init__(self, apis=None, repo=None, commit=None, tags=None):
    # self.repo = repo
    # self.commit = commit
    # self. tags = tags
    if not apis:
      apis = set()
    self.apis = apis
  
  def add_api(self, api):
    self.apis.add(api)
  
  def __str__(self):
    # return "repo=%s, commit=%s, tags=%s, apis=%s" % (self.repo, self.commit, self.tags, [str(x) for x in self.apis])
    return "apis=%s" % ([str(x) for x in self.apis])