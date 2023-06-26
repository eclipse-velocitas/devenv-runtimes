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

import json
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

from velocitas_lib import get_package_path, get_workspace_dir, require_env
from velocitas_lib.variables import ProjectVariables


class ServiceSpecConfig(NamedTuple):
    image: str
    is_enabled: bool = True
    env_vars: Dict[str, Optional[str]] = dict()
    use_dapr: bool = True
    args: List[str] = list()
    ports: List[str] = list()
    port_forwards: List[str] = list()
    mounts: List[str] = list()
    startup_log_patterns: List[str] = list()


class Service(NamedTuple):
    id: str
    config: ServiceSpecConfig


def parse_service_config(service_spec_config: Dict) -> ServiceSpecConfig:
    """Parse service spec configuration and return it as an named tuple.

    Args:
        service_spec_config: The specificon of the services from config file.
    """

    is_enabled = True
    use_dapr = True
    container_image = None
    env_vars = dict[str, Optional[str]]()
    ports = []
    port_forwards = []
    mounts = []
    args = []
    patterns = []

    variables = ProjectVariables()

    for config_entry in service_spec_config:
        key = config_entry["key"]
        value = config_entry["value"]

        if isinstance(value, str):
            value = variables.replace_occurrences(value)

        if key == "enabled":
            is_enabled = value is True or value == "true"
        elif key == "image":
            container_image = value
        elif key == "env":
            pair = value.split("=", 1)
            inner_key = pair[0].strip()
            env_vars[inner_key] = None
            if len(pair) > 1:
                env_vars[inner_key] = pair[1].strip()
        elif key == "no-dapr":
            if isinstance(value, str):
                use_dapr = not value == "true"
            elif isinstance(value, bool):
                use_dapr = not value
            else:
                raise ValueError("Unsupported value type!")
        elif key == "arg":
            args.append(value)
        elif key == "port":
            ports.append(value)
        elif key == "port-forward":
            port_forwards.append(value)
        elif key == "mount":
            mounts.append(value)
        elif key == "start-pattern":
            patterns.append(value)

    if container_image is None:
        raise RuntimeError("Container image needs to be provided!")

    return ServiceSpecConfig(
        image=container_image,
        is_enabled=is_enabled,
        env_vars=env_vars,
        use_dapr=use_dapr,
        args=args,
        ports=ports,
        port_forwards=port_forwards,
        mounts=mounts,
        startup_log_patterns=patterns,
    )


def get_services() -> List[Service]:
    """Return all specified services as Python object."""
    path = Path(f"{get_package_path()}/runtime.json")
    variable_value = require_env("runtimeFilePath")

    if variable_value is not None:
        overwritten_path = Path(variable_value)
        if not overwritten_path.is_absolute():
            overwritten_path = Path(get_workspace_dir()).joinpath(overwritten_path)

        if overwritten_path.exists():
            path = overwritten_path
            print(f"runtime.json path redirected to {path}")

    json_array: List[Dict] = json.load(
        open(
            path,
            encoding="utf-8",
        )
    )

    services: List[Service] = list()
    for service_json in json_array:
        service_id = service_json["id"]
        # service_interfaces = service_json['interfaces']
        service_config = ServiceSpecConfig(image="none")
        is_service_enabled = True
        if "config" in service_json:
            service_config = parse_service_config(service_json["config"])
            is_service_enabled = service_config.is_enabled

        if is_service_enabled:
            services.append(Service(service_id, service_config))

    return services
