# Copyright (c) 2023 Robert Bosch GmbH
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
from lib import (
    create_nodeport_spec,
    get_script_path,
    get_services,
    parse_service_config,
    generate_nodeport,
    create_cluster_ip_spec,
)
from yaml.loader import SafeLoader

node_port = 30050


def find_service_spec(lst, kind, name):
    """Returns index of spec for given kind and name.
    Args:
        lst: The list of the template specifications.
        kind: The kind of the pod.
        name: The name of the pod.
    """
    return [
        i
        for i, elem in enumerate(lst)
        if elem["kind"] == kind and elem["metadata"]["name"] == name
    ]


def init_template(templates):
    """Initializes podspecs list with non generated podspecs.
    Args:
        templates: The list of the template specifications.
    """
    template = []
    template.append(templates[find_service_spec(templates, "Pod", "bash")[0]])
    template.append(
        templates[find_service_spec(templates, "ConfigMap", "feeder-config")[0]]
    )
    template.append(
        templates[find_service_spec(templates, "PersistentVolume", "pv-volume")[0]]
    )
    template.append(
        templates[find_service_spec(templates, "PersistentVolumeClaim", "pv-claim")[0]]
    )

    return template


def create_podspec(templates, service_spec):
    """Creates podspec for given service specification.

    Args:
        templates: The list of the template specifications.
        service_spec: The specification of the service.
    """
    service_id = service_spec["id"]

    service_config = parse_service_config(service_spec["config"])

    template_pod = templates[find_service_spec(templates, "Pod", service_id)[0]]

    pod = generate_pod_spec(template_pod, service_config)
    pods.append(pod)

    for port in service_config.ports:
        pods.append(generate_nodeport_service(service_id, port))

    if "mosquitto" in service_config.image:
        pods.append(
            create_cluster_ip_spec(service_id, pod["spec"]["containers"][0]["ports"])
        )

    # TBD: mounts

    return pods


def generate_pod_spec(template_pod, service_config):
    pod = template_pod
    pod["spec"]["containers"][0]["image"] = service_config.image
    if service_config.args:
        pod["spec"]["containers"][0]["args"] = (
            "[ " + ", ".join(f'"{arg}"' for arg in service_config.args) + " ]"
        )
    if service_config.env_vars:
        pod["spec"]["containers"][0]["env"] = get_env(service_config)

    if service_config.ports:
        pod["spec"]["containers"][0]["ports"] = generate_port_spec(service_config)
    return pod


def get_env(service_config):
    env = []
    for key, value in service_config.env_vars.items():
        env.append({"name": key, "value": value})


def generate_port_spec(service_config):
    ports = []
    for port in service_config.ports:
        ports.append(
            {
                "name": "default",
                "containerPort": int(port),
                "protocol": "TCP",
            }
        )

    return ports


def generate_nodeport_service(service_id, port):
    nodeport_spec = create_nodeport_spec(service_id)
    nodeport_spec["spec"]["ports"] = []

    targetPort = int(port)
    nodeport_spec["spec"]["ports"].append(
        {
            "port": targetPort,
            "targetPort": targetPort,
            "nodePort": generate_nodeport(targetPort),
        }
    )
    return nodeport_spec


if __name__ == "__main__":
    with open(
        f"{get_script_path()}/runtime/config/podspec/runtime_template.yaml",
        "r",
        encoding="utf-8",
    ) as f:
        templates = list(yaml.load_all(f, Loader=SafeLoader))

    pods = init_template(templates)
    for service in get_services():
        pods.extend(create_podspec(templates, service_spec=service))

    with open(
        f"{get_script_path()}/runtime/config/podspec/runtime_generated.yaml",
        "w",
        encoding="utf-8",
    ) as f:
        yaml.dump_all(pods, f)
