# Copyright (c) 2023-2024 Contributors to the Eclipse Foundation
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

import argparse
import os
import sys
from typing import Any, Tuple

import ruamel.yaml as yaml
from velocitas_lib import get_script_path, get_workspace_dir  # noqa: E402
from velocitas_lib.services import ServiceSpecConfig, get_services

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "deployment"))

from lib import create_cluster_ip_spec, generate_nodeport  # noqa: E402


def find_service_spec_index(lst: list[dict[str, Any]], kind: str, name: str) -> int:
    """Returns index of spec for given kind and name.
    Args:
        lst: The list of the template specifications.
        kind: The kind of the pod.
        name: The name of the pod.
    """
    for i, elem in enumerate(lst):
        if elem["kind"] == kind and elem["metadata"]["name"] == name:
            return i

    raise IndexError(f"No index for {kind=} {name=}")


def init_template(templates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Initializes podspecs list with non generated podspecs.
    Args:
        templates: The list of the template specifications.
    """
    template = []
    template.append(templates[find_service_spec_index(templates, "Pod", "bash")])
    template.append(
        templates[find_service_spec_index(templates, "PersistentVolume", "pv-volume")]
    )
    template.append(
        templates[
            find_service_spec_index(templates, "PersistentVolumeClaim", "pv-claim")
        ]
    )

    return template


def create_podspec(templates, service_spec) -> list[dict[str, Any]]:
    """Creates podspec for given service specification.

    Args:
        templates: The list of the template specifications.
        service_spec: The specification of the service.
    """
    pods = []
    service_id = service_spec.id
    service_config = service_spec.config

    template_pod = templates[
        find_service_spec_index(templates, "Deployment", service_id)
    ]

    pod = generate_pod_spec(template_pod, service_config)
    pods.append(pod)

    for port in service_config.ports:
        pods.append(generate_nodeport_service(service_id, port))

    for mount in service_config.mounts:
        _, file = get_mount_folder_and_file(mount)
        if file != "":
            pods.append(generate_configmap(mount.split(":")[0], file))

    if "mosquitto" in service_config.image:
        pods.append(
            create_cluster_ip_spec(
                service_id, generate_clusterIP_port_spec(service_config)
            )
        )
        # mqtt_pubsub uses first specified port in runtime.json
        pods.append(gen_mqtt_pubsub(service_id, service_config.ports[0]))

    return pods


def generate_pod_spec(
    template_pod: dict[str, Any], service_config: ServiceSpecConfig
) -> dict[str, Any]:
    """Generate the spec for a single pod.

    Args:
        template_pod: The spec of the pod taken from the template
        service_config: The parsed configuration from the runtime.json
    """
    spec = template_pod["spec"]["template"]["spec"]["containers"][0]
    spec["image"] = service_config.image

    if service_config.args:
        spec["args"] = service_config.args

    if service_config.env_vars:
        spec["env"] = get_env(service_config)

    if service_config.ports:
        spec["ports"] = generate_port_spec(service_config)

    if service_config.mounts:
        spec["volumeMounts"] = generate_container_mount(service_config)
        template_pod["spec"]["template"]["spec"]["volumes"] = get_volumes(
            service_config
        )

    template_pod["spec"]["template"]["spec"]["containers"][0] = spec
    return template_pod


def get_volumes(service_config: ServiceSpecConfig) -> list[dict[str, Any]]:
    volumes = []
    for mount in service_config.mounts:
        _, file = get_mount_folder_and_file(mount)
        if file != "":
            file_name = os.path.splitext(file)[0]
            volumes.append(
                {
                    "name": f"{file_name}",
                    "configMap": {"name": f"{file_name}-config"},
                }
            )
        else:
            volumes.append(
                {
                    "name": "pv-storage",
                    "persistentVolumeClaim": {"claimName": "pv-claim"},
                }
            )
    return volumes


def generate_configmap(local_path: str, file: str):
    data = ""
    with open(local_path) as f:
        data = f.read()

    return {
        "apiVersion": "v1",
        "data": {f"{file}": data},
        "kind": "ConfigMap",
        "metadata": {
            "name": f"{os.path.splitext(file)[0]}-config",
            "namespace": "default",
        },
    }


def generate_container_mount(service_config: ServiceSpecConfig) -> list[dict[str, Any]]:
    """Generate the mount spec for a pod.

    Args:
        service_config: The parsed configuration from the runtime.json
    """
    mounts = []
    for mount in service_config.mounts:
        mount_path, file = get_mount_folder_and_file(mount)
        print(mount)
        if file != "":
            mounts.append(
                {
                    "name": f"{os.path.splitext(file)[0]}",
                    "mountPath": f"{os.path.join(mount_path, file)}",
                    "subPath": f"{file}",
                }
            )
        else:
            mounts.append({"mountPath": f"{mount_path}", "name": "pv-storage"})

    return mounts


def get_mount_folder_and_file(mount: str) -> Tuple[str, str]:
    mount_path = mount.split(":")[1]
    file = ""
    if "." in mount_path.split(os.sep)[-1]:
        file = os.path.basename(mount_path)
        mount_path = os.path.dirname(mount_path)
    return (mount_path, file)


def get_env(service_config: ServiceSpecConfig) -> list[dict[str, Any]]:
    """Generate the spec for the environment variables for a pod.

    Args:
        service_config: The parsed configuration from the runtime.json
    """
    env = []
    for key, value in service_config.env_vars.items():
        env.append({"name": key, "value": value})
    return env


def generate_port_spec(service_config: ServiceSpecConfig) -> list[dict[str, Any]]:
    """Generate the port spec for the used ports.

    Args:
        service_config: The parsed configuration from the runtime.json
    """
    ports = []
    for port in service_config.ports:
        ports.append(
            {
                "name": f"port{port}",
                "containerPort": int(port),
                "protocol": "TCP",
            }
        )

    return ports


def generate_clusterIP_port_spec(
    service_config: ServiceSpecConfig,
) -> list[dict[str, Any]]:
    """Generate the port spec for a clusterIP service.

    Args:
        service_config: The parsed configuration from the runtime.json
    """
    ports = []
    for port in service_config.ports:
        port_i = int(port)
        ports.append(
            {
                "name": f"port{port}",
                "port": port_i,
                "targetPort": port_i,
                "protocol": "TCP",
            }
        )

    return ports


def generate_nodeport_service(service_id: str, port: str) -> dict[str, Any]:
    """Generate the port spec for a nodeport service.

    Args:
        service_config: The parsed configuration from the runtime.json
        port: The port to be published
    """
    nodeport_spec = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": f"{service_id}-nodeport{port}"},
        "spec": {"type": "NodePort", "selector": {"app": f"{service_id}"}},
    }

    ports = []

    targetPort = int(port)
    ports.append(
        {
            "port": targetPort,
            "targetPort": targetPort,
            "nodePort": generate_nodeport(targetPort),
        }
    )
    nodeport_spec["spec"]["ports"] = ports
    return nodeport_spec


def gen_mqtt_pubsub(service_id, port):
    return {
        "apiVersion": "dapr.io/v1alpha1",
        "kind": "Component",
        "metadata": {"name": "mqtt-pubsub", "namespace": "default"},
        "spec": {
            "type": "pubsub.mqtt",
            "version": "v1",
            "metadata": [
                {
                    "name": "url",
                    "value": f"tcp://{service_id}.default.svc.cluster.local:{port}",
                },
                {"name": "qos", "value": 1},
                {"name": "retain", "value": "false"},
                {"name": "cleanSession", "value": "false"},
            ],
        },
    }


def gen_podspec(output_file_path: str):
    """Generate the spec of the all the pods needed for the runtime.

    Args:
        output_file_path: The path the spec is written to.
    """
    with open(
        f"{get_script_path()}/config/podspec/runtime_template.yaml",
        "r",
        encoding="utf-8",
    ) as f:
        templates = list(yaml.safe_load_all(f))

    pods = init_template(templates)
    for service in get_services():
        pods.extend(create_podspec(templates, service_spec=service))

    with open(
        output_file_path,
        "w",
        encoding="utf-8",
    ) as f:
        yaml.dump_all(pods, f, default_flow_style=False)


def main():
    parser = argparse.ArgumentParser("generate-podspec")
    parser.add_argument(
        "-o",
        "--output-file-path",
        type=str,
        required=False,
        help="Full path including name and file extension of the output file.",
    )
    args = parser.parse_args()

    output_file_path = args.output_file_path
    if output_file_path is None:
        output_file_path = os.path.join(get_workspace_dir(), "podspec.yaml")

    gen_podspec(output_file_path)


if __name__ == "__main__":
    main()
