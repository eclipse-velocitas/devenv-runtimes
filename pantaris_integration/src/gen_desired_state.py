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
import json
from typing import Any, Dict, List
import velocitas_lib


def parse_vehicle_signal_interface(config: Dict[str, Any]) -> List[str]:
    requirements = []
    src = str(config["src"])
    vss_release_prefix = (
        "https://github.com/COVESA/vehicle_signal_specification/releases/download/"
    )
    if vss_release_prefix in src:
        version = src.removeprefix(vss_release_prefix).split("/")[0]
        requirements.append(f"vss-source-default-vss:{version}")
        # assuming that databroker and vss have same version
        requirements.append(f"dataprovider-proto-grpc:{version}")
    else:
        requirements.append("vss-source-custom-vss:latest")

    datapoints = config["datapoints"]["required"]
    for datapoint in datapoints:
        path = str(datapoint["path"]).lower().replace(".", "-")
        access = datapoint["access"]
        requirements.append(f"vss-{access}-{path}")

    return requirements


def parse_interfaces(interfaces):
    requirements = []
    for interface in interfaces:
        interface_type = interface["type"]
        if interface_type == "vehicle-signal-interface":
            requirements += parse_vehicle_signal_interface(interface["config"])
        elif interface_type == "pubsub":
            requirements.append("mqtt:v3")

    return requirements


def main():
    parser = argparse.ArgumentParser("generate-desired-state")
    parser.add_argument(
        "-o",
        "--output-file-path",
        type=str,
        required=False,
        help="Path to the folder where the manifest should be placed.",
    )
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        required=True,
        help="The URL of the image including the tag.",
    )
    args = parser.parse_args()

    output_file_path = args.output_file_path
    source = args.source
    imageName = source.split(":")[0].split("/")[-1]
    version = source.split(":")[1]

    app_manifest = velocitas_lib.get_app_manifest()
    appName = app_manifest["name"]
    interfaces = app_manifest["interfaces"]

    requirements = []
    requirements += parse_interfaces(interfaces)

    if output_file_path is None:
        output_file_path = velocitas_lib.get_workspace_dir()
    output_file_path = f"{output_file_path}/{appName.lower()}_manifest_{version}.json"

    data = {
        "name": appName,
        "source": source,
        "type": "binary/container",
        "requires": requirements,
        "provides": [f"{imageName}:{version}"],
    }
    with open(
        output_file_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(data, f)


if __name__ == "__main__":
    main()
