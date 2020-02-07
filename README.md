<p align="center">
  <img src="levelops.png" alt="LevelOps"/>
</p>

- [What are LevelOps Plugins?](#what-are-levelops-plugins)
- [Software License](#software-license)
- [Installation](#installation)
- [Modes of Operation](#modes-of-operation)
- [LevelOps Plugins](#levelops-plugins)
- [Request plugins for new use cases](#request-plugins-for-new-use-cases)


# What are LevelOps Plugins?
LevelOps Plugins are standalone tools, written in Python 3.6 to help developers and security operators with a wide variety of one-off development, security and operations tasks. They can be executed in stand-alone mode (no callback to LevelOps) or in connected mode (callback to LevelOps)
 
# Software License
LevelOps Plugins are licensed under Apache License, Version 2

# Installation

      mkdir -p ~/tools/levelops
      git clone --depth 1 git@github.com:levelops/tools-levelops.git ~/tools/levelops
      pip install virtualenv
      mkdir -p ~/tools/levelops/env
      virtualenv -p /usr/bin/python3 ~/tools/levelops/env
      source ~/tools/levelop/env/bin/activate
      pip install -r ~/tools/levelops/requirements.txt

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
    <td><p>Use this tool to discover services used in multiple GCP Projects and Services deployed within GKE</p><br /> Recommended Use Cases: <br /> <ul><li>New Service Discovery and Workflows</li><li>Resource and PaaS Ownership Discovery Workflows</li><li>Resource Utilization Discovery Workflows</li></ul></td>
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
</table>

# Request plugins for new use cases

Email us at [plugins@levelops.io](mailto:plugin@levelops.io) for new use cases or if you have questions.
