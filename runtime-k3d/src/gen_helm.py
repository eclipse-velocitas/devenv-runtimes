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

import argparse
import os
import re
import shutil

import ruamel.yaml as yaml
from lib import generate_nodeport, parse_service_config

from velocitas_lib import get_script_path, get_services, get_workspace_dir


def generate_env_vars_spec(service_spec_config):
    envs = []
    for env in service_spec_config.env_vars.items():
        envs.append({"name": env[0], "value": env[1]})

    return envs


def generate_ports_spec(service_spec_config):
    ports = []
    for port in service_spec_config.ports:
        ports.append(
            {
                "port": int(port),
                "nodePort": generate_nodeport(int(port)),
            }
        )
    return ports


def generate_values_by_service(service_spec):
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


def generate_values_file(output_path: str):
    services = []
    for service in get_services():
        services.append(generate_values_by_service(service))
    with open(f"{output_path}/values.yaml", "w", encoding="utf-8") as f:
        f.write(yaml.dump_all(services).replace("---", ""))


def copy_helm_chart(output_path: str):
    shutil.copytree(
        f"{get_script_path()}/runtime/config/helm",
        output_path,
        symlinks=False,
        ignore=None,
        copy_function=shutil.copy2,
        ignore_dangling_symlinks=False,
        dirs_exist_ok=True,
    )


def gen_helm(output_path: str):
    os.makedirs(output_path, exist_ok=True)
    copy_helm_chart(output_path)
    generate_values_file(output_path)


def main():
    parser = argparse.ArgumentParser("generate-helm")
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        required=False,
        help="Destination Path for the generated Helm Chart and templates.",
    )
    args = parser.parse_args()

    output_path = args.output_path
    if output_path is None:
        output_path = os.path.join(get_workspace_dir(), "./helm")

    gen_helm(output_path)


if __name__ == "__main__":
    main()
