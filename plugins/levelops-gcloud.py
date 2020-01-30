#!/usr/bin/env python

##################################################################
#  Copyright (C) 2019-2020 LevelOps Inc <support@levelops.io>
#  
#  This file is part of the LevelOps Inc Tools.
#  
#  This tool is licensed under Apache License, Version 2.0
##################################################################

import logging
import os
import shlex
import subprocess
from argparse import ArgumentParser
from queue import Empty, Queue
from sys import exit
from threading import Thread
from time import sleep
from uuid import uuid4

from kubernetes import client as k_client
from kubernetes import config as k_config
from kubernetes.client.configuration import Configuration
from kubernetes.client.rest import ApiException
from ujson import dump as jdump
from ujson import dumps
from ujson import load as jload
from ujson import loads
from yaml import dump as ydump
from yaml import dump_all, full_load, full_load_all

log = logging.getLogger(__name__)
excluded_namespaces = ['kube-system']
cleanup = []
p_pool = []
r_pool = []
backup = {}
SUCCESS = 0


items = [
    ["filestore", "instances", "list"],  
    ["pubsub", "topics", "list"], 
    ["bigtable", "instances", "list"], 
    ["bigtable", "clusters", "list"], 
    ["compute", "backend-services", "list"], 
    ["dataflow", "jobs", "list"], 
    ["dataproc", "clusters", "list"], 
    ["dataproc", "jobs", "list"], 
    ["deployment-manager", "deployments", "list"], 
    ["kms", "--location", "us", "list"], 
    ["redis", "instances", "list", "--region", "asia-east1"], 
    ["redis", "instances", "list", "--region", "asia-east2"], 
    ["redis", "instances", "list", "--region", "asia-northeast1"], 
    ["redis", "instances", "list", "--region", "asia-northeast2"], 
    ["redis", "instances", "list", "--region", "asia-south1"], 
    ["redis", "instances", "list", "--region", "asia-southeast1"], 
    ["redis", "instances", "list", "--region", "australia-southeast1"], 
    ["redis", "instances", "list", "--region", "europe-north1"], 
    ["redis", "instances", "list", "--region", "europe-west1"], 
    ["redis", "instances", "list", "--region", "europe-west2"], 
    ["redis", "instances", "list", "--region", "europe-west3"], 
    ["redis", "instances", "list", "--region", "europe-west4"], 
    ["redis", "instances", "list", "--region", "europe-west5"], 
    ["redis", "instances", "list", "--region", "europe-west6"], 
    ["redis", "instances", "list", "--region", "northamerica-northeast1"], 
    ["redis", "instances", "list", "--region", "southamerica-east1"], 
    ["redis", "instances", "list", "--region", "us-central1"], 
    ["redis", "instances", "list", "--region", "us-east1"], 
    ["redis", "instances", "list", "--region", "us-east2"], 
    ["redis", "instances", "list", "--region", "us-west1"], 
    ["redis", "instances", "list", "--region", "us-west2"], 
    ["sql", "instances", "list"]
    # ["resource-manager", "folders"]
    ]


class Control(object):
  def __init__(self):
    self.terminate = False

  def stop(self):
    self.terminate = True


class Report(object):
    def __init__(self):
        self.orgs = []
        self.projects = []
        self.folders = {}
        self.errors = []

    def add_org(self, org):
        self.orgs.append(org)

    def add_project(self, project):
        if not isinstance(project, Project):
            raise Exception("projects need to be of type 'Project'")
        self.projects.append(project)
    
    def add_folder(self, org_id, folder):
        self.folders["%s-%s"%(org_id, folder.id)] = folder
    
    def add_error(self, error):
        self.errors.append(error)


class Resource(object):
    def __init__(self, r_id, name, state=None):
        self.id = r_id
        self.name = name
        self.state = state


class Organization(Resource):
    def __init__(self, r_id, name, state=None):
        super().__init__(r_id=r_id, name=name, state=state)
        self.folders = []
    
    def add_folder(self, folder):
        if not isinstance(folder, Resource):
            raise Exception("a folder needs to be of type 'Resource'")
        self.folders.append(folder)


class Project(Resource):
    def __init__(self, r_id, name, state, parent=None, apis=None, paas=None, services=None, k8s=None):
        super().__init__(r_id=r_id, name=name, state=state)
        if paas:
            self.paas = paas
        else:
            self.paas = []
        if apis:
            self.apis = apis
        else:
            self.apis = []
        if services:
            self.services = services
        else:
            self.services = []
        if k8s:
            self.k8s = k8s
        else:
            self.k8s = []
        self.parent = parent
        self.k8s_total_count = 0
    
    def add_api(self, api):
        if not isinstance(api, Service):
            raise Exception("api needs to be of type 'Service'")
        self.apis.append(api)
    
    def add_paas(self, paas):
        if not isinstance(paas, dict):
            raise Exception("paas needs to be of type 'Resource'")
        self.paas.append(paas)
    
    def add_service(self, service):
        if not isinstance(service, Service):
            raise Exception("service needs to be of type 'Service'")
        self.services.append(service)
    
    def add_k8s_cluster(self, cluster):
        if not isinstance(cluster, KCluster):
            raise Exception("cluster needs to be of type 'KCluster'")
        self.k8s.append(cluster)
    
    def add_all_k8s_clusters(self, clusters):
        if not isinstance(clusters, list):
            raise Exception("clusters needs to be of type 'list[KCluster]' but was '%s'" % str(type(clusters)))
        self.k8s.extend(clusters)


class Service(Resource):
    def __init__(self, r_id, name, state, meta = None):
        super().__init__(r_id=r_id, name=name, state=state)
        # self.meta = meta


class KComponent(Resource):
    def __init__(self, r_id, name, kind, namespace, selectors=None, ports=None, containers=None, labels=None, state=None, meta=None, subtype=None):
        super().__init__(r_id=r_id, name=name, state=state)
        self.meta = meta
        self.kind = kind
        self.labels = labels
        self.namespace = namespace
        self.containers = containers
        self.selectors = selectors
        self.ports = ports
        self.subtype = subtype


class KCluster(Resource):
    def __init__(self, r_id, name, state, zone, location=None, locations=None, creation_time=None, masters_version=None, nodes_version=None, initial_version=None, resources=None):
        super().__init__(r_id=r_id, name=name, state=state)
        self.zone = zone
        self.location = location
        self.locations = locations
        self.creation_time = creation_time
        self.masters_version = masters_version
        self.nodes_version = nodes_version
        self.initial_version = initial_version
        if not resources:
            self.resources = []
        else:
            self.resources = resources
    
    def add_resources(self, resources):
        if not isinstance(resources, list):
            raise Exception("'resources' needs to be of type 'list[KComponent]' but was '%s'" % str(type(resources)))
        self.resources.extend(resources)


def enable_api(apis, project):
    return _change_apis(apis=apis, project=project, state="enable")


def disable_apis(apis, project):
    return _change_apis(apis=apis, project=project, state="disable")


def _change_apis(apis, project, state):
    args = ["gcloud", "services", state,"--project", project, "--quiet"]
    args.extend(apis)
    p_apis = subprocess.run(args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if p_apis.returncode != SUCCESS:
        message = "[%s] Couldn't change the state of the API(s) '%s' to '%s': %s" % (project.name, str(apis), state, p_apis.stderr)
        report.add_error(message)
        log.debug(message)
        return False
    return "finished successfully" in p_apis.stdout


def get_google_credentials(report):
    config_file = "/tmp/%s.google" % str(uuid4())
    log.info("google credentials: %s", config_file)
    p_credentials = subprocess.run(args=shlex.split("gcloud config config-helper --format=json"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    cleanup.append(config_file)
    if p_credentials.returncode != SUCCESS:
        message = "Coudn't get the google credentials for the current user."
        report.add_error(message)
        log.debug(message)
        return None
    with open(config_file,'w') as f:
        f.write(p_credentials.stdout)
    return config_file


def get_cluster_credentials(report, project, zone, cluster_name):
    config_file = "/tmp/%s.config" % str(uuid4())
    log.info("k8s config file: %s", config_file)
    env = {}
    env.update(os.environ)
    env['KUBECONFIG'] = config_file
    p_credentials = subprocess.run(args=["gcloud", "container", "clusters", "get-credentials", cluster_name, "--zone", zone, "--project", project.name, "--quiet"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    cleanup.append(config_file)
    if p_credentials.returncode != SUCCESS:
        message = "[%s] Coudn't get the cluster credentials for the cluster '%s': %s" % (project.name, cluster_name, p_credentials.stderr)
        report.add_error(message)
        log.debug(message)
        return None
    return config_file


def get_k8s_clusters(report, project):
    p_clusters = subprocess.run(args=["gcloud", "container", "clusters", "list", "--project", project.name, "--format", "json", "--quiet"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if p_clusters.returncode != SUCCESS:
        message = "[%s] %s" % (project.name, p_clusters.stderr)
        report.add_error(message)
        log.debug(message)
        return None
    clusters = loads(p_clusters.stdout)
    project.k8s_total_count = len(clusters)
    k8s = []
    for cluster in clusters:
        k8s.append(
            KCluster(
                location=cluster['location'],
                locations=cluster['locations'],
                name=cluster['name'],
                state=cluster['status'],
                zone=cluster['zone'],
                masters_version=cluster['currentMasterVersion'],
                nodes_version=cluster['currentNodeVersion'],
                initial_version=cluster['initialClusterVersion'],
                r_id=cluster['labelFingerprint'],
                creation_time=cluster['createTime']
            )
        )
    return k8s


def get_k8s_resources(report, cluster, project):
    config_file = get_cluster_credentials(report=report, project=project, zone=cluster.zone, cluster_name=cluster.name)
    if not config_file:
        return None
    with open(g_credentials, 'r') as f:
        google = jload(f)
    with open(config_file, 'r') as f:
        kcfg = full_load(f)
    for user in kcfg.get('users'):
        config = user.get('user').get('auth-provider').get('config')
        config['expiry'] = google['credential']['token_expiry']
        config['access-token'] = google['credential']['access_token']
    with open(config_file, 'w') as f:
        ydump(kcfg, f)
    configuration = Configuration()
    k_config.load_kube_config(config_file=config_file, client_configuration=configuration)
    api_client = k_client.ApiClient(configuration=configuration)
    k = k_client.CoreV1Api(api_client=api_client)
    apps = k_client.AppsV1Api(api_client=api_client)

    resources = []
    set_names = [
        "list_deployment_for_all_namespaces", 
        "list_replica_set_for_all_namespaces", 
        "list_daemon_set_for_all_namespaces", 
        "list_stateful_set_for_all_namespaces",
        "list_service_for_all_namespaces"
        ]
    for set_name in set_names:
        if set_name.startswith("list_service"):
            k_set = getattr(k, set_name)()
        else:
            k_set = getattr(apps, set_name)()
        collection = {}
        for s in k_set.items:
            if s.metadata.namespace in excluded_namespaces:
                log.debug("Skipping resource since it is located in the excluded namespace '%s'", s.metadata.namespace)
                continue
            if s.kind:
                kind = s.kind
            elif 'deployment' in str(type(s)).lower():
                kind = "Deployment"
            elif 'service' in str(type(s)).lower():
                kind = "Service"
            elif 'replicaset' in str(type(s)).lower():
                kind = "ReplicaSet"
            elif 'daemonset' in str(type(s)).lower():
                kind = "DaemonSet"
            elif 'statefulset' in str(type(s)).lower():
                kind = "StatefulSet"
            s_type = None
            ports = None
            selectors = None
            meta = None
            containers = None
            if kind == "Service":
                s_type = s.spec.type
                ports = [{'protocol': port.protocol, 'target': port.target_port, 'port': port.port} for port in s.spec.ports]
                selectors = s.spec.selector
                if s_type == 'ExternalName':
                    meta = {"external_ip": s.spec.externalIPs}
            elif kind == "Deployment":
                containers = [x.image for x in s.spec.template.spec.containers]
            else:
                containers = [x.image for x in s.spec.template.spec.containers]
            if kind == "Deployment" or kind == "Service":
                _id = s.metadata.self_link
            else:
                _id = s.metadata.self_link.replace('-'+s.metadata.labels['pod-template-hash'],'')
            version = int(s.metadata.resource_version)
            ref = collection.get(_id, {"version": -1, "resource": None})
            if ref['version'] < version:
                collection[_id] = {"version": version, "resource": KComponent(
                                                r_id=s.metadata.name, 
                                                name=s.metadata.name, 
                                                namespace=s.metadata.namespace, 
                                                kind=kind, 
                                                labels=s.metadata.labels, 
                                                containers=containers, 
                                                ports=ports,
                                                selectors=selectors,
                                                subtype=s_type,
                                                meta=meta)}
        for _id in collection:
            resources.append(collection[_id]["resource"])
    return resources


def restore_permisions(backup_file):
    with open(backup_file, 'r') as f:
        backup = jload(f)
    # get current enabled apis
    # disable apis that should not be enabled


def __boot(name, thread_count, thread_queue_size, pool, control, report, timeout=2):
    queue = Queue(maxsize=thread_count*thread_queue_size)
    for i in range(0, thread_count):
        t = Thread(name=name+"-"+str(i), daemon=True, target=_worker, args=(queue, report, control, timeout))
        t.start()
        pool.append(t)
    return queue


def _worker(queue, report, control, timeout=2):
    log.debug('Starting...')
    while not control.terminate:
      try:
        task = queue.get(block=True, timeout=timeout)
      except Empty as e:
        log.debug('Empty response from the queue, will try again...')
        continue
      log.debug('Task acquried!')
      try:
        action = task.get('action')
        task.pop('action')
        # params = 
        action(**task)
      except Exception as e:
        log.error("Task failed", exc_info=True)
      finally:
        queue.task_done()
    log.debug("Stopping....")


def process_k8_cluster(cluster, project, report):
    log.info("Processing '%s' k8s cluster.", cluster.name)
    try:
        resources = get_k8s_resources(report=report, cluster=cluster, project=project)
        cluster.add_resources(resources=resources)
    except Exception as e:
        log.error(e, exc_info=True)
        report.add_error('[k8s] %s' % str(e))


def process_gcp_service(service, project, report):
    log.info("Processing '%s' gcp service.", service[0])
    try:
        args = ["gcloud"]
        args.extend(service)
        args.extend(["--format", "json", "--project", project.name, "--quiet"])
        p_resources = subprocess.run(args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if p_resources.returncode != SUCCESS:
            report.add_error("[%s - %s] %s" % (project.name, service[0], p_resources.stderr))
            log.debug('[%s - %s] Skipping due to an error in the response', project.name, service[0])
            log.debug('stdout: %s', p_resources.stdout)
            log.debug('stderr: %s', p_resources.stderr)
            log.debug('')
            log.debug('')
            return
        resources = loads(p_resources.stdout)
        for r in resources:
            if 'databaseVersion' in r:
                resource = {"type": service[0], "kind": r.get('kind', service[1]), "name": r['name'], "database_version": r['databaseVersion']}
            else:
                resource = {"type": service[0], "kind": r.get('kind', service[1]), "name": r['name']}
            # resource = Resource(r_id=r['name'],name=r['name'])
            project.add_paas(resource)
            # print("[%s] %s: %s" % (project.name,service[0],resource))
    except Exception as e:
        log.error(e, exc_info=True)
        report.add_error("[%s - %s] %s" % (project.name, service[0], str(e)))


def process_project(project, report, queue):
    log.info("Processing Project: %s", project.name)
    for item in items:
        queue.put({'action': process_gcp_service, 'service': item, 'project': project, 'report': report})
    try:
        clusters = get_k8s_clusters(report=report, project=project)
        if clusters:
            project.add_all_k8s_clusters(clusters=clusters)
            for cluster in clusters:
                queue.put({'action': process_k8_cluster, 'cluster': cluster, 'project': project, 'report': report})
    except Exception as e:
        log.error(e, exc_info=True)
        report.add_error('[project] %s' % str(e))
    try:
        p_services_available = subprocess.run(args=["gcloud", "services", "list", "--enabled", "--project", project.name, "--format", "json", "--quiet"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        s_available = loads(p_services_available.stdout)
        for service in s_available:
            meta = {}
            project.add_api(Service(r_id=service['config']['name'],name=service['config']['title'],state=service['state'],meta=meta))
    except Exception as e:
        log.error(e, exc_info=True)
        report.add_error('[project] %s' % str(e))


def wait_and_stop(name, queue, control, pool):
    attempt = 0
    while not queue.empty() or attempt < 2:
      log.info('Waiting for the %s queue to be empty', name)
      sleep(1)
      if queue.empty():
        attempt += 1
    control.stop()
    waiting_for_threads = True
    while waiting_for_threads:
      for t in pool:
        waiting_for_threads = t.isAlive()
        if waiting_for_threads:
          log.info("Waiting for %s threads to complete....", name)
          sleep(0.5)
          break
    log.info('%s Qsize: %s', name, queue.qsize())


def get_orgs(report):
    p_orgs = subprocess.run(args=["gcloud", "organizations", "list", "--format", "json", "--quiet"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    orgs = loads(p_orgs.stdout)
    for org in orgs:
        org = Organization(r_id=org['name'].replace('organizations/',''), name=org['displayName'], state=org['lifecycleState'])
        report.add_org(org=org)
        try:
            p_folders = subprocess.run(args=["gcloud", "resource-manager", "folders", "list", "--organization", org.id, "--format", "json", "--quiet"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            folders = loads(p_folders.stdout)
            for folder in folders:
                resource = Resource(r_id=folder['name'].replace('folders/',''), name=folder['displayName'], state=folder['lifecycleState'])
                org.add_folder(resource)
                report.add_folder(org_id=org.id, folder=resource)
        except Exception as e:
            report.add_error("[%s - folders] - %s" % (org.name, str(e)))


def process(report, threads, resources_threads, thread_queue_size, resources_thread_queue_size):
    p_queue = __boot(name="p_worker", report=report, thread_count=threads, thread_queue_size=thread_queue_size, pool=p_pool, control=p_control)
    r_queue = __boot(name="k_worker", report=report, thread_count=resources_threads, thread_queue_size=resources_thread_queue_size, pool=r_pool, control=r_control)

    try:
        p_projects = subprocess.run(args=["gcloud", "projects", "list", "--format", "json", "--quiet"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        projects = loads(p_projects.stdout)
        for p in projects:
            log.debug("Proj: %s", p['projectId'])
            project = Project(r_id=p['projectNumber'], name=p['projectId'], state=p['lifecycleState'], parent=p['parent']['id'])
            report.add_project(project)
            # backup[project.id + "-" + project.name] = project.apis
    except Exception as e:
        log.error(e,exc_info=True)
        report.add_error('[projects] %s' % str(e))
    # with open(backup_file, 'w') as f:
    #     jdump(backup, f, indent=2)
    #     log.info("Backup created at %s", backup_file)

    for project in report.projects:
        p_queue.put(item={'action': process_project, 'project': project, 'report': report, 'queue': r_queue}, block=True)
    
    wait_and_stop(name="projects", queue=p_queue, control=p_control, pool=p_pool)
    wait_and_stop(name="resources", queue=r_queue, control=r_control, pool=r_pool)


p_control = Control()
r_control = Control()


if __name__ == "__main__":
    logging.basicConfig(level="INFO", format="[%(threadName)s] [%(levelname)s]: %(message)s")
    parser = ArgumentParser(prog="Levelops GCP reporter", usage="gcloud.py (optional <flags>)")
    parser.add_argument('--debug', dest='debug', help='Enables debug logging', action='store_true')
    parser.add_argument('-t', '--threads', dest='threads', help='Number of threads', type=int, default=5)

    options = parser.parse_args()
    if options.debug:
        log.setLevel('DEBUG')
    target = './'
    target += 'levelops-gcp-report-%s' % str(uuid4())
    target = os.path.realpath(target)
    os.makedirs(target)
    # backup_file = '/tmp/levelops-gcp-backup-%s.json' % str(uuid4())
    log.info('')
    log.info('')
    log.info('***************************************')
    log.info('************ ATTENTION!! **************')
    log.info('***************************************')
    log.info('')
    # log.info('A backup will be created at %s', backup_file)
    log.info('')
    log.info('The report will be written at %s', target)
    log.info('')
    log.info('***************************************')
    log.info('***************************************')
    log.info('')
    log.info('')
    
    report = Report()
    get_orgs(report=report)
    g_credentials = get_google_credentials(report=report)
    process(report=report, threads=options.threads, resources_threads=options.threads*2, thread_queue_size=5, resources_thread_queue_size=10)
    
    for f in cleanup:
        log.info("removing %s", f)
        os.remove(f)
    
    t_k8s_count = 0
    for project in report.projects:
        t_k8s_count += project.k8s_total_count
        paas = project.paas
        summary = {}
        for p in paas:
            paas_type = p.pop('type')
            t = summary.get(paas_type, [])
            t.append(p)
            summary[paas_type] = t
        project.paas = summary
        report_file = '%s/%s.json'%(target,project.name)
        with open(report_file, 'w') as f:
            jdump(project, f, indent=2)

    report_file = '%s/errors.json'%(target)
    with open(report_file, 'w') as f:
        jdump(report.errors, f, indent=2)

    json = {"total_orgs": len(report.orgs), "total_folders": len(report.folders), "total_projects": len(report.projects), "total_k8s_clusters": t_k8s_count}
    json["orgs"] = [x.name for x in report.orgs]
    json["folders"] = [f for f in report.folders]
    json["projects"] = {p.name: {"k8s_clusters": len(p.k8s)} for p in report.projects}

    report_file = '%s/global_summary.json'%(target)
    with open(report_file, 'w') as f:
        jdump(json, f, indent=2)
    
    log.info('')
    log.info('The report has been created at %s', target)
