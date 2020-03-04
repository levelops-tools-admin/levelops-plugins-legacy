import logging
from requests import post
from ujson import dumps
from . import Plugin
from time import gmtime, strftime, time

log = logging.getLogger(__name__)

# YYYY-MM-DDThh:mm:ssTZD


class Runner(object):
  def __init__(self, base_url=None):
    if not base_url or len(base_url.strip()):
      self.base_url = "https://api.levelops.io"
    else:
      self.base_url = base_url
    self.api_endpoint = '{base_url}/v1/plugins/results'.format(base_url=self.base_url)
    self.metadata = {
        "version": "<runner version>",
        "os": "redhat8",
        "execution": "<ISO 8601  Date>",
        "available_cores": "3ecu",
        "available_memory": "4GB"
    }

  def submit(self, plugin: Plugin, product_id: str, success: bool, results: dict, labels: dict, elapsed_time: int, token: str = None):
    self.metadata['execution'] = elapsed_time
    # for key in results:
    #   if not data[key]:
    #     data.pop(key, None)
    print(dumps(results, indent=2))
    data = dumps({
        "tool" : plugin.name,
        "version" : plugin.version,
        "timestamp": strftime('%Y-%m-%dT%H:%M:%S%z', gmtime(time()) ),
        "labels" : labels,
        "product_id": product_id,
        "successful": success,
        "results": results,
        "metadata": self.metadata
    })
    headers = {"Content-Type": "application/json"}
    if token:
        headers['Authorization'] = 'ApiKey ' + token
    
    response = post(url=self.api_endpoint, data=data, headers=headers)
    if response.status_code == 202:
      log.info("Results submited to the endpoint '%s'", self.api_endpoint)
      log.debug("Response: %s", response.text)
    else:
      log.error("Results not accepted by the endpoint '%s': %s", self.api_endpoint, response.text)
