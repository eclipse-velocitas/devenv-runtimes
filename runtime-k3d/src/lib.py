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

from typing import Dict, List, NamedTuple, Optional

from velocitas_lib import (
    get_cache_data,
    get_package_path,
    json_obj_to_flat_map,
    replace_variables,
)


def generate_nodeport(port: int):
    """Creates nodeport from the last 3 digits of the targetport in the range
    of 30000-32767.

    Args:
        port: The port to be used to generate the nodeport.
    """
    nodeport = f"{(port%1000):03d}"
    return int(f"30{nodeport}")


def create_cluster_ip_spec(service_id: str, ports: List[dict]):
    """Creates cluster ip spec for the given service_id.

    Args:
        service_id: The id of the service to create cluster ip for.
    """
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": service_id, "labels": {"app": service_id}},
        "spec": {"type": "ClusterIP", "selector": {"app": service_id}, "ports": ports},
    }


class ServiceSpecConfig(NamedTuple):
    image: Optional[str]
    env_vars: Dict[str, Optional[str]]
    no_dapr: bool
    args: List[str]
    ports: List[str]
    mounts: List[str]


def parse_service_config(service_spec_config: dict):
    """Parses service spec configuration and returns it as an named tuple.

    Args:
        service_spec_config: The specificon of the services from config file.
    """

    no_dapr = False
    container_image = None
    env_vars = dict[str, Optional[str]]()
    ports = []
    mounts = []
    args = []

    variables = json_obj_to_flat_map(get_cache_data(), "builtin.cache")
    variables["builtin.package_dir"] = get_package_path()

    for config_entry in service_spec_config:
        if not isinstance(config_entry["value"], (int, float, bool)):
            if "builtin" in config_entry["value"]:
                config_entry["value"] = replace_variables(
                    config_entry["value"], variables
                )
        match config_entry["key"]:  # noqa: E999
            case "image":
                container_image = config_entry["value"]
            case "env":
                pair = config_entry["value"].split("=", 1)
                env_vars[pair[0].strip()] = None
                if len(pair) > 1:
                    env_vars[pair[0].strip()] = pair[1].strip()
            case "no-dapr":
                no_dapr = config_entry["value"] == "true"
            case "arg":
                args.append(config_entry["value"])
            case "port":
                ports.append(config_entry["value"])
            case "mount":
                mounts.append(config_entry["value"])

    return ServiceSpecConfig(container_image, env_vars, no_dapr, args, ports, mounts)
