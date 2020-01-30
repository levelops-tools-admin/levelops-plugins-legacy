from requests import post
from ujson import dumps
from . import Plugin
from time import gmtime, strftime, time


# YYYY-MM-DDThh:mm:ssTZD


class Runner(object):
  def __init__(self):
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
        headers['Authorization'] = 'Bearer ' + token
    
    respons = post(url='https://api.levelops.io/v1/plugins/results', data=data, headers=headers)

    print("Response: " + str(respons.text))
