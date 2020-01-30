#!/usr/bin/env python
import os
import sys
import logging
import re

from time import sleep
from os import walk, path, listdir
from threading import Thread
from queue import Queue, Empty

from sdk.types import Endpoint, API, Report

log = logging.getLogger(__name__)

# scan directory and subdirectories
# collect java files and put them in the work queue
# consume java files from the work queue
# # parse java file
# # collect APIs
# return results

class Scanner(object):
  def __init__(self, thread_count=5, thread_queue_size=50, default_exclusions=[".git", "build", "target", "bin", "test"], queue_timeout=1):
    self.thread_count = thread_count
    self.thread_queue_size = thread_queue_size
    self.default_exclusions = default_exclusions
    self.pool = []
    self.report = Report()
    self.timeout = queue_timeout
    self.__boot__()
  
  def get_report(self):
    return self.report

  def scan_directory(self, base_path, filters, action, extra_exclusions=None):
    if extra_exclusions:
      exclusions = extra_exclusions + self.default_exclusions
    else:
      exclusions = self.default_exclusions
    _scan_directory(queue=self.queue, base_path=base_path, filters=filters, action=action, exclusions=exclusions, control=self.control)
  
  def wait(self):
    attempt = 0
    while not self.queue.empty() or attempt < 2:
      log.info('Waiting for the queue to be empty')
      sleep(1)
      if self.queue.empty():
        attempt += 1

  def wait_and_finish(self):
    self.wait()
    self.control.stop()
    waiting_for_threads = True
    while waiting_for_threads:
      for t in self.pool:
        waiting_for_threads = t.isAlive()
        if waiting_for_threads:
          log.info("Waiting for threads to complete....")
          sleep(0.5)
          break
    log.info('Qsize: %s', self.queue.qsize())

  def __boot__(self):
    self.queue = Queue(maxsize=self.thread_count*self.thread_queue_size)
    self.control = Control()
    for i in range(0, self.thread_count):
      t = Thread(name="Worker-"+str(i), daemon=True, target=run, args=(self.queue, self.report, self.control, self.timeout))
      t.start()
      self.pool.append(t)


def run(queue, report, control, timeout=2):
    log.debug('Starting...')
    while not control.terminate:
      try:
        task = queue.get(block=True, timeout=timeout)
      except Empty as e:
        log.debug('Empty response from the queue, will try again...')
        continue
      log.debug('Task acquried!')
      try:
        api = task.get('target')(task.get('f_path'))
        if api:
          report.add_api(api)
      except Exception as e:
        log.error("Task failed", exc_info=True)
      finally:
        queue.task_done()
    log.debug("Stopping....")


def _queue_file(queue, control, action, f_path):
  if control.terminate:
    log.error('Canot add new task, already terminating...')
  else:
    queue.put({'target': action, 'f_path': f_path})


def _scan_directory(queue, base_path, filters, action, exclusions=None, control=None):
  log.debug("scanning '%s'" % base_path)
  try:
    dirpath, folders, files = next(walk(top=base_path))
  except Exception as ex:
    log.error('Error - base_path: %s, dirpath: %s', base_path, dirpath, exc_info=True)
    raise ex
  for file in files:
    if isinstance(filters, list):
      for f_filter in filters:
        if file.endswith(f_filter):
          _queue_file(queue=queue, control=control, action=action, f_path=path.join(dirpath,file))
          # queue.put({'target': action, 'f_path': path.join(dirpath,file)})
          break
    elif file.endswith(filters):
      _queue_file(queue=queue, control=control, action=action, f_path=path.join(dirpath,file))
      # queue.put({'target': action, 'f_path': path.join(dirpath,file)})
  for folder in folders:
    if not folder.startswith(".") and folder not in exclusions:
      log.debug("Folder: %s" % folder)
      _scan_directory(queue=queue, base_path=path.join(dirpath,folder), filters=filters, action=action, exclusions=exclusions, control=control)


class Control(object):
  def __init__(self):
    self.terminate = False

  def stop(self):
    self.terminate = True

