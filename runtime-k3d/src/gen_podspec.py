# Copyright (c) 2023 Robert Bosch GmbH and Microsoft Corporation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

import yaml
from yaml.loader import SafeLoader
from typing import Optional

from lib import (
    get_services,
    get_script_path,
    create_nodeport
)

node_port = 30050

def find_service_spec(lst, kind, name):
    """Returns index of spec for given kind and name.
    Args:
        lst: The list of the template specifications.
        kind: The kind of the pod.
        name: The name of the pod.
    """
    return [i for i, elem in enumerate(lst) if elem['kind'] == kind and elem['metadata']['name'] == name]

def init_template(templates):
    """Initializes podspecs list with non generated podspecs.
    Args:
        templates: The list of the template specifications.
    """
    template = []
    template.append(templates[find_service_spec(templates, 'Pod', 'bash')[0]])
    template.append(templates[find_service_spec(templates, 'ConfigMap', 'feeder-config')[0]])
    template.append(templates[find_service_spec(templates, 'PersistentVolume', 'pv-volume')[0]])
    template.append(templates[find_service_spec(templates, 'PersistentVolumeClaim', 'pv-claim')[0]])
    
    return template

def create_podspec(templates, service_spec):
    """Creates podspec for given service specification.

    Args:
        templates: The list of the template specifications.
        service_spec: The specification of the service.
    """
    global node_port
    
    service_id = service_spec["id"]
    
    container_image = None
    service_port = None
    env_vars = dict[str, Optional[str]]()
    port_forwards = []
    mounts = []
    args = []
    pods=[]

    for config_entry in service_spec["config"]:
        if config_entry["key"] == "image":
            container_image = config_entry["value"]
        elif config_entry["key"] == "env":
            pair = config_entry["value"].split("=", 1)
            env_vars[pair[0].strip()] = None
            if len(pair) > 1:
                env_vars[pair[0].strip()] = pair[1].strip()
        elif config_entry["key"] == "port":
            service_port = config_entry["value"]
        elif config_entry["key"] == "no-dapr":
            no_dapr = config_entry["value"]
        elif config_entry["key"] == "arg":
            args.append(config_entry["value"])
        elif config_entry["key"] == "port-forward":
            port_forwards.append(config_entry["value"])
        elif config_entry["key"] == "mount":
            mounts.append(config_entry["value"])
    
    template_pod = templates[find_service_spec(templates, "Pod", service_id)[0]]
    template_pod['spec']['containers'][0]['image'] = container_image
    if args:
        template_pod['spec']['containers'][0]['args'] = '[ ' + ', '.join(f'"{arg}"' for arg in args) + ' ]'
    if env_vars:
        template_pod["spec"]["containers"][0]["env"] = []
        for key, value in env_vars.items():
            template_pod["spec"]["containers"][0]["env"].append({"name": key,
                                                                 "value": value})

    pods.append(template_pod)
    if service_port:
        template_pod["spec"]["containers"][0]['ports'] = [{'name': 'default',
                                                           'containerPort': int(service_port),
                                                           'protocol': 'TCP'}]
    
    if port_forwards:
        nodeport_spec = create_nodeport(service_id)
        nodeport_spec["spec"]['ports'] = []        
        for port in port_forwards:
            source_target_ports = port.split(':')
            nodeport_spec["spec"]['ports'].append({
                "port": int(source_target_ports[0]),
                "targetPort": int(source_target_ports[1]),
                "nodePort": node_port
            })
            node_port = node_port + 1
        pods.append(nodeport_spec)
                
    # TBD: mounts
    
    return pods

if __name__ == "__main__":
    with open(f"{get_script_path()}/runtime/config/podspec/runtime_template.yaml", 'r') as f:
        templates = list(yaml.load_all(f, Loader=SafeLoader))
        
    pods = init_template(templates)
    for service in get_services():
        pods.extend(create_podspec(templates, service_spec=service))
        
    with open(f"{get_script_path()}/runtime/config/podspec/runtime_generated.yaml", 'w') as f:
        yaml.dump_all(pods, f)