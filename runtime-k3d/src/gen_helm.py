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
import os

from lib import (
    get_services,
    get_script_path,
    create_nodeport_spec,
    create_cluster_ip_spec,
    get_template
)

node_port = 30050

def find_service_spec_index(lst, name):
    """Returns index of spec for the given name.
    Args:
        lst: The list of the template specifications.
        name: The name of the pod.
    """
    for i, elem in enumerate(lst):
        dict_keys = list(lst[i].keys())
        if elem[dict_keys[0]]['name'] == name:
            return i    


def generate_values_and_templates(values_template, service_spec):
    """Generates values specification from the given templates and service specification and generates helm templates for each service spec.
    Args:
        lst: The list of the template specifications.
        kind: The kind of the pod.
        name: The name of the pod.
    """
    global node_port    
    service_id = service_spec["id"]
    
    no_dapr=False
    container_image = None
    service_port = None
    env_vars = dict[str, Optional[str]]()
    port_forwards = []
    mounts = []
    args = []

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

    value_spec = values_template[find_service_spec_index(values_template, service_id)]
    value_spec_key = list(value_spec.keys())[0]
    value_spec[value_spec_key]['repository'] = container_image.split(':')[0]
    value_spec[value_spec_key]['tag'] = container_image.split(':')[1]
    
    for env in env_vars.items():
        if "FILE" in env[0]:
            value_spec[value_spec_key][env[0].replace('_', '').lower()] = env[1]
    
    if args:
        value_spec[value_spec_key]['args'] = args
    
    if service_port:
        value_spec[value_spec_key]['port'] = int(service_port)
            
    template = get_template()
    template['metadata']['name'] = f"{{{{.Values.{value_spec_key}.name}}}}"
    template['metadata']['labels']['app'] = template['metadata']['name']
    template['spec']['selector']['matchLabels']['app'] = template['metadata']['name']
    template['spec']['template']['metadata']['labels']['app'] = template['metadata']['name']
    
    if not no_dapr:
        template['spec']['template']['metadata']['annotations'] = {
            "dapr.io/enabled": "true",
            "dapr.io/config": "config",
            "dapr.io/app-protocol": "grpc",
            "dapr.io/app-id": f"{{{{.Values.{value_spec_key}.name}}}}",
            "dapr.io/app-port": f"{{{{.Values.{value_spec_key}.port}}}}",
            "dapr.io/log-level": f"{{{{.Values.{value_spec_key}.daprLogLevel}}}}"
        }
    
    container_spec = {
        "name": f"{{{{.Values.{value_spec_key}.name}}}}",
        "image": f"{{{{.Values.{value_spec_key}.repository}}}}:{{{{.Values.{value_spec_key}.tag}}}}",
        "imagePullPolicy": f"{{{{.Values.{value_spec_key}.pullPolicy}}}}"
        }
    template['spec']['template']['spec']['containers'].append(container_spec)
   
    if args:
        template['spec']['template']['spec']['containers'][0]['args'] = f"{{{{- range .Values.{value_spec_key}.args}}}}- {{{{.}}}}{{{{- end }}}}"
    
    if service_port:
        template['spec']['template']['spec']['containers'][0]['ports'] = [{
            'name': 'default',
            'containerPort': f"{{{{.Values.{value_spec_key}.port}}}}",
            'protocol': 'TCP' 
        }]

    if env_vars:
        template['spec']['template']['spec']['containers'][0]['env'] = []
        for env in env_vars.items():
            env_var = {
                'name': env[0],
                'value': env[1]
            }
            if "FILE" in env[0]:
                env_var['value'] = f"{{{{.Values.{value_spec_key}.{env[0].replace('_', '').lower()}}}}}"
            template['spec']['template']['spec']['containers'][0]['env'].append(env_var)    
    
    if mounts:
        template['spec']['template']['spec']['containers'][0]['volumeMounts'] = []
        template['spec']['template']['spec']['volumes'] = []
        for mount in mounts:
            mount_value = mount.split("/")[-1]
            if "." in mount_value:
                mount_dict = {
                    "name": mount_value.split(".")[0],
                    "mountPath": f"""/{mount_value}"""
                }     
            else:
                mount_dict = {
                    "mountPath": f"""/{mount_value}""",
                    "name": "pv-storage"
                }
                if not template['spec']['template']['spec']['volumes']:
                    volume_dict = {
                        "name": "pv-storage",
                        "persistentVolumeClaim": {
                            "claimName": "pv-claim"
                        }
                    }
                    template['spec']['template']['spec']['volumes'].append(volume_dict)
            template['spec']['template']['spec']['containers'][0]['volumeMounts'].append(mount_dict)
    
    service_spec_lst = []
    service_spec_lst.append(template)
    if port_forwards:  
        nodeport_spec = create_nodeport_spec(f"{{{{.Values.{value_spec_key}.name}}}}")
        i = 1
        nodeport_spec['ports'] = []
        for port in port_forwards:
            source_target_ports = port.split(':')
            if int(source_target_ports[0]) == int(service_port):
                value_spec[value_spec_key]['targetPort'] = f"{{{{.Values.{value_spec_key}.targetPort}}}}"
                value_spec[value_spec_key]['nodePort'] = f"{{{{.Values.{value_spec_key}.nodePort}}}}"
                port_spec = {
                    'port': f"{{.Values.{value_spec_key}.port}}",
                    'targetPort': f"{{{{.Values.{value_spec_key}.targetPort}}}}",
                    'nodePort': f"{{{{.Values.{value_spec_key}.nodePort}}}}"
                }
            else:
                value_spec[value_spec_key]['port' + str(i)] = f"{{{{.Values.{value_spec_key}.port{i}}}}}"
                value_spec[value_spec_key]['targetPort' + str(i)] = f"{{{{.Values.{value_spec_key}.targetPort{i}}}}}"
                value_spec[value_spec_key]['nodePort' + str(i)] = f"{{{{.Values.{value_spec_key}.nodePort{i}}}}}"
                template['spec']['template']['spec']['containers'][0]['ports'].append({
                    'name': f"""port{i}""",
                    'containerPort': f"{{{{.Values.{value_spec_key}.port{i}}}}}",
                    'protocol': 'TCP' 
                })
                port_spec = {
                    'port': f"{{{{.Values.{value_spec_key}.port{i}}}}}",
                    'targetPort': f"{{{{.Values.{value_spec_key}.targetPort{i}}}}}",
                    'nodePort': f"{{{{.Values.{value_spec_key}.nodePort{i}}}}}"
                }
                i = i + 1
            nodeport_spec['ports'].append(port_spec)
            node_port = node_port + 1
        service_spec_lst.append(nodeport_spec)
    
    # create cluster ip if needed
    if service_id == "mqtt-broker":
        cluster_ip_port_spec = nodeport_spec['ports']
        for port in cluster_ip_port_spec:
            port_spec = port.copy()
            del port_spec['nodePort']
            port_spec['protocol'] = "TCP"
        cluster_ip_port_spec = create_cluster_ip_spec(f"{{{{.Values.{value_spec_key}.name}}}}", port_spec)
        service_spec_lst.append(cluster_ip_port_spec)
    
    if not os.path.exists(f"{get_script_path()}/runtime/config/helm/templates_generated/"):
        os.mkdir(f"{get_script_path()}/runtime/config/helm/templates_generated/")
    with open(f"{get_script_path()}/runtime/config/helm/templates_generated/{service_id}.yaml", 'w') as f:
        yaml.dump_all(service_spec_lst, f)
            
    return value_spec    


if __name__ == "__main__":
    with open(f"{get_script_path()}/runtime/config/helm/values.yaml", 'r') as f:
        values_template = list(yaml.load_all(f, Loader=SafeLoader))
        
    services = []
    for service in get_services():
        services.append(generate_values_and_templates(values_template, service_spec=service))
    
    with open(f"{get_script_path()}/runtime/config/helm/values.yaml", 'w') as f:
        yaml.dump_all(services, f)
    
    print("Generation has been finished!")