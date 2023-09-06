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
import hashlib
import json
import re
from typing import Any, Dict, List

import requests
import velocitas_lib
import velocitas_lib.services


def is_uri(path: str) -> bool:
    """Check if the provided path is a URI.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the path is a URI. False otherwise.
    """
    return re.match(r"(\w+)\:\/\/(\w+)", path) is not None


def parse_vehicle_signal_interface(config: Dict[str, Any]) -> List[str]:
    """Parses the vehicle signal interface config.

    Args:
        config: The json-config of the interface, as defined in the appManifest.json.

    Returns:
        List[str]: A list of requirements defined by the config.
    """
    requirements = []
    src = str(config["src"])
    vss_release_prefix = (
        "https://github.com/COVESA/vehicle_signal_specification/releases/download/"
    )
    if vss_release_prefix in src:
        version = src.removeprefix(vss_release_prefix).split("/")[0]
        requirements.append(f"vss-source-default-vss:{version}")
        # assuming that databroker and vss have same version
        requirements.append(f"data-broker-grpc:{version}")
    elif is_uri(src):
        requirements.append(f"vss-source-custom-vss:{get_md5_from_uri(src)}")
    else:
        requirements.append(f"vss-source-custom-vss:{get_md5_for_file(src)}")

    datapoints = config["datapoints"]["required"]
    for datapoint in datapoints:
        path = str(datapoint["path"]).lower().replace(".", "-")
        access = datapoint["access"]
        requirements.append(f"vss-{access}-{path}")

    return requirements


def parse_grpc_interface(config: Dict[str, Any]) -> str:
    """Parses the grpc interface config.

    Args:
        config: The json-config of the interface, as defined in the appManifest.json.

    Returns:
        str: The requirement with md5-hash of the proto-file as version.
    """
    src = str(config["src"])

    return f"dataprovider-proto-grpc:{get_md5_from_uri(src)}"


def get_md5_from_uri(src: str) -> str:
    """Get the md5-hash of a file defined by an URI.

    Args:
        str: The URI of the file.

    Returns:
        str: The md5-hash of the file.
    """
    md5 = hashlib.md5(usedforsecurity=False)
    with requests.get(src) as source:
        for chunk in source.iter_content(chunk_size=4096):
            md5.update(chunk)

    return md5.hexdigest()


def get_md5_for_file(file_path: str):
    """Get the md5-hash of a local file defined by a path.

    Args:
        str: The local path to the file.

    Returns:
        str: The md5-hash of the file.
    """
    md5 = hashlib.md5(usedforsecurity=False)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)

    return md5.hexdigest()


def get_mqtt_version() -> str:
    """Get the version of the used mqtt-broker.

    Returns:
        str: The version of the mqtt-broker defined in the runtime.json.
    """
    mqtt_config = velocitas_lib.services.get_specific_service("mqtt-broker").config
    mqtt_version = mqtt_config.image.split(":")[-1]
    return mqtt_version


def parse_interfaces(interfaces: List[Dict[str, Any]]) -> List[str]:
    """Parses the defined interfaces.

    Args:
        interfaces: The json-array of interfaces, as defined in the appManifest.json.

    Returns:
        List[str]: A list of requirements defined by the interface definitions.
    """
    requirements = []
    for interface in interfaces:
        interface_type = interface["type"]
        if interface_type == "vehicle-signal-interface":
            requirements += parse_vehicle_signal_interface(interface["config"])
        elif interface_type == "pubsub":
            requirements.append(f"mqtt:{get_mqtt_version()}")
        elif interface_type == "grpc-interface":
            requirements.append(parse_grpc_interface(interface["config"]))

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
