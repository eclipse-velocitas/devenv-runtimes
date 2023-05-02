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

import re
import yaml
import os
from lib import (
    get_script_path,
    get_services,
    parse_service_config,
    generate_nodeport
)


def generate_env_vars_spec(service_spec_config):
    envs = []
    for env in service_spec_config.env_vars.items():
        envs.append({"name": env[0], "value": env[1]})

    return envs


def generate_ports_spec(service_spec_config):
    ports = []
    i = 1
    for port in service_spec_config.ports:
        ports.append(
            {
                "port": int(port),
                "nodePort": generate_nodeport(int(port)),
            }
        )
        i = i + 1
    return ports


def generate_values(service_spec):
    """Generates values specification from the given service spec.
    Args:
        service_spec: The spec of the service.
    """
    service_id = re.sub(r"[^a-zA-Z\s]", "", service_spec["id"])

    service_spec_config = parse_service_config(service_spec["config"])

    value_spec_key = f"image{service_id.capitalize()}"
    value_spec = {value_spec_key: {}}

    value_spec[value_spec_key]["name"] = service_id
    value_spec[value_spec_key]["repository"] = service_spec_config.image.split(":")[0]
    value_spec[value_spec_key]["tag"] = service_spec_config.image.split(":")[1]
    value_spec[value_spec_key]["pullPolicy"] = "Always"

    if service_spec_config.env_vars:
        value_spec[value_spec_key]["environmentVariables"] = generate_env_vars_spec(
            service_spec_config
        )

    if service_spec_config.args:
        value_spec[value_spec_key]["args"] = service_spec_config.args

    if service_spec_config.ports:
        value_spec[value_spec_key]["ports"] = generate_ports_spec(service_spec_config)

    return value_spec


def gen_helm(output_path: str):
    services = []
    for service in get_services():
        services.append(generate_values(service))

    os.makedirs(output_path, exist_ok=True)
    print(f"Outputting helm to {output_path!r}")

    with open(
        f"{output_path}/values.yaml", "w",
        encoding="utf-8"
    ) as f:
        f.write(yaml.dump_all(services).replace("---", ""))

    print("Generation has been finished!")


if __name__ == "__main__":
    gen_helm(f"{get_script_path()}/runtime/config/helm")
