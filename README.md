<p align="center">
  <img src="levelops.png" alt="LevelOps"/>
</p>

- [What are LevelOps Plugins?](#what-are-levelops-plugins)
- [Software License](#software-license)
- [Installation](#installation)
  - [With Auto Installation Script](#with-auto-installation-script)
  - [Step By Step](#step-by-step)
  - [Aditional dependencies](#aditional-dependencies)
- [Modes of Operation](#modes-of-operation)
- [LevelOps Plugins](#levelops-plugins)
- [LevelOps GCP Service Discovery](#levelops-gcp-service-discovery)
  - [Description](#description)
  - [Permissions](#permissions)
  - [Supported Services](#supported-services)
  - [Requirements](#requirements)
    - [GCP](#gcp)
    - [Software and tools](#software-and-tools)
  - [Steps](#steps)
- [Request plugins for new use cases](#request-plugins-for-new-use-cases)


# What are LevelOps Plugins?
LevelOps Plugins are standalone tools, written in Python 3.6 to help developers and security operators with a wide variety of one-off development, security and operations tasks. They can be executed in stand-alone mode (no callback to LevelOps) or in connected mode (callback to LevelOps)
 
# Software License
LevelOps Plugins are licensed under Apache License, Version 2

# Installation
## With Auto Installation Script

      curl https://raw.githubusercontent.com/levelops-tools-admin/levelops-plugins/master/autosetup.sh -s -o /tmp/autosetup.sh && chmod +x /tmp/autosetup.sh && /tmp/autosetup.sh

## Step By Step

      mkdir -p ~/tools/levelops
      git clone --depth 1 https://github.com/levelops-tools-admin/levelops-plugins ~/tools/levelops
      cd ~/tools/levelops
      pip install virtualenv # in some environments pip3 is available instead of pip
      mkdir -p env
      virtualenv env # If python 3 is not the default python 'virtualenv -p /usr/bin/python3 env' to specify the path to the python 3 binary
      source env/bin/activate
      pip install -r requirements.txt

## Aditional dependencies

The GCP Service Discovery Tool requires the gcloud cli to be installed and accesible in the path. Please follow Google's instructions to install the gcloud cli which can be found [here](https://cloud.google.com/sdk/docs#install_the_latest_cloud_tools_version_cloudsdk_current_version).

# Modes of Operation
**Standalone Mode:** Use this mode, to test the plug-in locally. The plug-in will output the results locally.  
  
**Connected Mode**: Want to track results over a period of time and diff results to seamlessly enable change management workflows? That’s easy! Email [support@levelops.io](mailto:support@levelops.io) to get an evaluation account and API Token


# LevelOps Plugins
<table style="font-size: 8px!; text-align: left !important;">
  <th>Plug-In</th>
  <th>Class</th>
  <th style="min-with: 200px!">Purpose</th>
  <th>Sample Results</th>
  <th>How to use this tool?</th>
  <tr>
    <td><p>Static API Endpoint Discovery  for Java Spring MVC</p></td>
    <td>API Endpoint Discovery </td>
    <td><p>Use this tool, to discover a list of API endpoints in any Java Spring Project</p> <br /> Recommended Use Cases: <br /> <ul><li>New API Workflows</li></ul></td>
    <td><ul><li>

[json](samples/api_discovery_springmvc.json) 
</li><li>

[csv](samples/api_discovery_springmvc.csv)
</li></ul></td>
    <td>
      <b>Standalone mode:</b>

      # Run the scripts and write the results to a file.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv

      # Run the scripts and write the results to the console.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --csv
      
   <b>Connected mode:</b>

      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv --submit --token <api token>

      Email support@levelops.io to get an evaluation account and API Token
   </td>
  </tr>
  <tr>
    <td><p>Static API Endpoint Discovery for Python Flask</p></td>
    <td>API Endpoint Discovery</td>
    <td><p>Use this tool, to discover a list of API endpoints in any Python Flask Project</p><br /> Recommended Use Cases: <br /> <ul><li>New API Workflows</li></ul></td>
    <td><ul><li>

[json](samples/api_discovery_flask.json) 
</li><li>

[csv](samples/api_discovery_flask.csv)
</li></ul></td>
    <td>
    <b>Standalone mode:</b>

      # Run the scripts and write the results to a file.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv

      # Run the scripts and write the results to the console.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --csv
      
   <b>Connected mode:</b>

      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv --submit --token <api token>

      Email support@levelops.io to get an evaluation account and API Token
   </td>
  </tr>
  <tr>
    <td><p>Static API Endpoint Discovery for NodeJS Express</p></td>
    <td>API Endpoint Discovery</td>
    <td><p>Use this tool, to discover a list of API endpoints in any NodeJS Express Project</p><br /> Recommended Use Cases: <br /> <ul><li>New API Workflows</li></ul></td>
    <td><ul><li>

[json](samples/api_discovery_nodejs_express.json) 
</li><li>

[csv](samples/api_discovery_nodejs_express.csv)
</li></ul></td>
    <td>
    <b>Standalone mode:</b>

      # Run the scripts and write the results to a file.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv

      # Run the scripts and write the results to the console.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --csv
      
   <b>Connected mode:</b>

      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv --submit --token <api token>

      Email support@levelops.io to get an evaluation account and API Token
   </td>
  </tr>
  <tr>
    <td><p>Static API Endpoint Discovery for AWS CloudFormation</p></td>
    <td>API Endpoint Discovery</td>
    <td><p>Use this tool, to discover a list of API endpoints in any AWS CloudFormation Project</p><br /> Recommended Use Cases: <br /> <ul><li>New API Workflows</li></ul></td>
    <td><ul><li>

[json](samples/api_discovery_aws_cloudformation.json) 
</li><li>

[csv](samples/api_discovery_aws_cloudformation.csv)
</li></ul></td>
    <td>
    <b>Standalone mode:</b>

      # Run the scripts and write the results to a file.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv

      # Run the scripts and write the results to the console.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --csv
      
   <b>Connected mode:</b>

      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv --submit --token <api token>

      Email support@levelops.io to get an evaluation account and API Token
   </td>
  </tr>
  <tr>
    <td><p>Static API Endpoint Discovery for Kubernetes</p></td>
    <td>API Endpoint Discovery</td>
    <td><p>Use this tool, to discover a list of API endpoints in any Kubernetes Infrastructure as Code Project</p><br /> Recommended Use Cases: <br /> <ul><li>New API Workflows</li></ul></td>
    <td><ul><li>

[json](samples/api_discovery_k8s.json) 
</li><li>

[csv](samples/api_discovery_k8s.csv)
</li></ul></td>
    <td>
    <b>Standalone mode:</b>

      # Run the scripts and write the results to a file.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv

      # Run the scripts and write the results to the console.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --csv
      
   <b>Connected mode:</b>

      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv --submit --token <api token>

      Email support@levelops.io to get an evaluation account and API Token
   </td>
  </tr>
  <tr>
    <td><p>Static API Endpoint Discovery for ApiGee</p></td>
    <td>API Endpoint Discovery</td>
    <td><p>Use this tool, to discover a list of API endpoints in any ApiGee Infrastructure as Code Project</p><br /> Recommended Use Cases: <br /> <ul><li>New API Workflows</li></ul></td>
    <td><ul><li>

[json](samples/api_discovery_apigee.json) 
</li><li>

[csv](samples/api_discovery_apigee.csv)
</li></ul></td>
    <td>
    <b>Standalone mode:</b>

      # Run the scripts and write the results to a file.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv

      # Run the scripts and write the results to the console.
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --json
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --csv
      
   <b>Connected mode:</b>

      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --print-results --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --json --submit --token <api token>
      ~/tools/levelops/plugins/api_discovery_<...>.py <path to source code directory> --out <output file> --csv --submit --token <api token>

      Email support@levelops.io to get an evaluation account and API Token
   </td>
  </tr>
  <tr>
    <td><p>GCP Service Discovery</p></td>
    <td>Cloud Service Discovery</td>
    <td><p>Use this tool to discover services used in multiple GCP Projects and Services deployed within GKE. [Aditional Information](#levelops-gcp-service-discovery)</p><br /> Recommended Use Cases: <br /> <ul><li>New Service Discovery and Workflows</li><li>Resource and PaaS Ownership Discovery Workflows</li><li>Resource Utilization Discovery Workflows</li></ul></td>
    <td><ul><li>

[json](samples/gcp_service_discovery) 
</li></ul></td>
    <td>

      ~/tools/levelops/plugins/levelops-gcloud.py
   </td>
  </tr>
  <tr>
    <td><p>Jenkins Security Posture Checker</p></td>
    <td>CI/CD Tool Hardening</td>
    <td><p>Use this tool to check the security posture of your Jenkins environments, against 40+ security spanning across access, permissions, settings and plug-ins</p><br /> Recommended Use Cases: <br /> <ul><li>Tool Hardening</li></ul></td>
    <td><ul><li>

[html](samples/jenkins_security_hardening_plugin/LevelOps_Jenkins_Security_Report.html)
</li></ul></td>
    <td>
    <b>Standalone mode:</b>

      Install LevelOps Jenkins Security Plugin.
      In Jenkins UI go to "Manage Jenkins" -> "LevelOps Plugin" & configure the Plugin.
      e.g. The report directory path. Frequency to run the report. (cron schedule) etc.
      To run report immediately click on "Run Report Now".
      To view report click on "Download Report".
      
   <b>Connected mode:</b>

      Install LevelOps Jenkins Security Plugin.
      In Jenkins UI go to "Manage Jenkins" -> "LevelOps Plugin" & configure the Plugin.
      e.g. The report directory path. Frequency to run the report. (cron schedule) etc.
      To send data to LevelOps, click on the optional check "Send data to LevelOps".
      To run report immediately click on "Run Report Now".
      To view report click on "Download Report".
    
   </td>
  </tr>
  <tr>
    <td><p>LevelOps GitSecret Plugin</p></td>
    <td>Source Code Audit</td>
    <td><p>Use this tool to easily run git-secrets in your source code to find sensitive information like aws credentials.</p><br /> Recommended Use Cases: <br /> <ul><li>Code pre-commit validation</li><li>Pull request pre-merge validation</li><li>CI/CD Workflow</li></ul></td>
    <td><ul>
      <li>--<!-- [json](samples/levelops-git-secrets.json)  --></li>
      <li>--<!-- [csv](samples/levelops-git-secrets.csv) --></li>
    </ul></td>
    <td>
    <b>Standalone mode:</b>

      # Run the scripts and write the results to a file.
      ~/tools/levelops/plugins/levelops-git-secrets.py <path to source code directory> --out <output file>
      ~/tools/levelops/plugins/levelops-git-secrets.py <path to source code directory> --out <output file> --json
      ~/tools/levelops/plugins/levelops-git-secrets.py <path to source code directory> --out <output file> --csv

      # Run the scripts and write the results to the console.
      ~/tools/levelops/plugins/levelops-git-secrets.py <path to source code directory> --print-results
      ~/tools/levelops/plugins/levelops-git-secrets.py <path to source code directory> --print-results --json
      ~/tools/levelops/plugins/levelops-git-secrets.py <path to source code directory> --print-results --csv
      
   <b>Connected mode:</b>

      ~/tools/levelops/plugins/levelops-git-secrets.py <path to source code directory> --submit -p 23 --token <api token>
      ~/tools/levelops/plugins/levelops-git-secrets.py <path to source code directory> --print-results --submit -p 23  --token <api token>
      ~/tools/levelops/plugins/levelops-git-secrets.py <path to source code directory> --out <output file> --json --submit -p 23  --token <api token>
      ~/tools/levelops/plugins/levelops-git-secrets.py <path to source code directory> --out <output file> --csv --submit -p 23  --token <api token>

      Email support@levelops.io to get an evaluation account and API Token
   </td>
  </tr>
  <tr>
    <td><p>LevelOps Brakeman Plugin</p></td>
    <td>Source Code Audit</td>
    <td><p>Use this tool to easily run brakeman in your source code to find security vulnerabilities.</p><br /> Recommended Use Cases: <br /> <ul><li>Code pre-commit validation</li><li>Pull request pre-merge validation</li><li>CI/CD Workflow</li></ul></td>
    <td><ul>
      <li>--<!-- [json](samples/levelops-brakeman.json)  --></li>
      <li>--<!-- [csv](samples/levelops-brakeman.csv) --></li>
    </ul></td>
    <td>
    <b>Standalone mode:</b>

      # Run the scripts and write the results to a file.
      ~/tools/levelops/plugins/levelops-brakeman.py <path to source code directory> --out <output file>
      ~/tools/levelops/plugins/levelops-brakeman.py <path to source code directory> --out <output file> --json
      ~/tools/levelops/plugins/levelops-brakeman.py <path to source code directory> --out <output file> --csv

      # Run the scripts and write the results to the console.
      ~/tools/levelops/plugins/levelops-brakeman.py <path to source code directory> --print-results
      ~/tools/levelops/plugins/levelops-brakeman.py <path to source code directory> --print-results --json
      ~/tools/levelops/plugins/levelops-brakeman.py <path to source code directory> --print-results --csv
      
   <b>Connected mode:</b>

      ~/tools/levelops/plugins/levelops-brakeman.py <path to source code directory> --submit -p 23 --token <api token>
      ~/tools/levelops/plugins/levelops-brakeman.py <path to source code directory> --print-results --submit -p 23  --token <api token>
      ~/tools/levelops/plugins/levelops-brakeman.py <path to source code directory> --out <output file> --json --submit -p 23  --token <api token>
      ~/tools/levelops/plugins/levelops-brakeman.py <path to source code directory> --out <output file> --csv --submit -p 23  --token <api token>

      Email support@levelops.io to get an evaluation account and API Token
   </td>
  </tr>
  <tr>
    <td><p>LevelOps Praetorian Report Plugin</p></td>
    <td>Security Audit</td>
    <td><p>Use this tool to easily convert a praetorian pdf report into structured data.</p><br /> Recommended Use Cases: <br /> <ul><li>Security Audit</li><li>Security Tracking</li></ul></td>
    <td><ul>
      <li>--<!-- [json](samples/levelops-git-secrets.json)  --></li>
      <li>--<!-- [csv](samples/levelops-git-secrets.csv) --></li>
    </ul></td>
    <td>
    <b>Standalone mode:</b>

      # Run the scripts and write the results to a file.
      ~/tools/levelops/plugins/levelops-report_praetorian.py <path to pdf report> --out <output file>
      ~/tools/levelops/plugins/levelops-report_praetorian.py <path to pdf report> --out <output file> --json

      # Run the scripts and write the results to the console.
      ~/tools/levelops/plugins/levelops-report_praetorian.py <path to pdf report> --print-results
      ~/tools/levelops/plugins/levelops-report_praetorian.py <path to pdf report> --print-results --json
      
   <b>Connected mode:</b>

      ~/tools/levelops/plugins/levelops-report_praetorian.py <path to pdf report> --submit -p 23 --token <api token>
      ~/tools/levelops/plugins/levelops-report_praetorian.py <path to pdf report> --print-results --submit -p 23  --token <api token>
      ~/tools/levelops/plugins/levelops-report_praetorian.py <path to pdf report> --out <output file> --json --submit -p 23  --token <api token>

      Email support@levelops.io to get an evaluation account and API Token
   </td>
  </tr>
  <tr>
    <td><p>LevelOps Microsoft Threat Modeling Tool Plugin</p></td>
    <td>Security Audit</td>
    <td><p>Use this tool to easily convert a microsft threat modeling tool report into json data for easy changes tracking.</p><br /> Recommended Use Cases: <br /> <ul><li>Security Audit</li><li>Security Tracking</li></ul></td>
    <td><ul>
      <li>--<!-- [json](samples/levelops-git-secrets.json)  --></li>
      <li>--<!-- [csv](samples/levelops-git-secrets.csv) --></li>
    </ul></td>
    <td>
    <b>Standalone mode:</b>

      # Run the scripts and write the results to a file.
      ~/tools/levelops/plugins/levelops-report_ms_tmt.py <path to htm report file> --out <output file>
      ~/tools/levelops/plugins/levelops-report_ms_tmt.py <path to htm report file> --out <output file> --json

      # Run the scripts and write the results to the console.
      ~/tools/levelops/plugins/levelops-report_ms_tmt.py <path to htm report file> --print-results
      ~/tools/levelops/plugins/levelops-report_ms_tmt.py <path to htm report file> --print-results --json
      
   <b>Connected mode:</b>

      ~/tools/levelops/plugins/levelops-report_ms_tmt.py <path to htm report file> --submit -p 23 --token <api token>
      ~/tools/levelops/plugins/levelops-report_ms_tmt.py <path to htm report file> --print-results --submit -p 23  --token <api token>
      ~/tools/levelops/plugins/levelops-report_ms_tmt.py <path to htm report file> --out <output file> --json --submit -p 23  --token <api token>

      Email support@levelops.io to get an evaluation account and API Token
   </td>
  </tr>
</table>

# LevelOps GCP Service Discovery
## Description
The tool generates a report of running GCP resources per project and a global summary.
The GCP resources collected depend on the permissions of the user executing the script and on the enabled APIs on each of the projects.

## Permissions
The tool expects at least read only access for the supported services for every project to be scanned. It also expects to have APIs enabled for all the supported services.


## Supported Services
- bigtable
- compute
- dataflow
- dataproc
- filestore
- gke
- kms
- redis
- sql
- pubsub

## Requirements

### GCP
The user executing the tool should have access to GCP projects and services.

### Software and tools
- python >= 3.6
- gcloud cli 

## Steps
1.- Ensure gcloud cli is in the path and is authorized.
   >
      gcloud auth login

2.- Complete the plugins [installation](#installation).

3.- Run the levelops gcloud reporting tool, the tool will autogenerate a directory with the results.
   >
      .~/tools/levelops/plugins/levelops-gcloud.py

# Request plugins for new use cases

Email us at [plugins@levelops.io](mailto:plugin@levelops.io) for new use cases or if you have questions.
