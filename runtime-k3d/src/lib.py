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
import os
import sys
from typing import List


def get_script_path() -> str:
    """Return the absolute path to the directory the invoked Python script
    is located in."""
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def get_services():
    """Return all specified services as Python object."""
    return json.load(open(f"{get_script_path()}/../../runtime.json", encoding="utf-8"))


def create_nodeport_spec(service_id: str):
    """Creates nodeport spec for the given service_id.

    Args:
        service_id: The id of the service to create nodeport for.
    """
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": service_id + "-nodeport"
        },
        "spec": {
            "type": "NodePort",
            "selector": {
                "app": service_id
            }
        }
    }


def create_cluster_ip_spec(service_id: str, ports: List[dict]):
    """Creates cluster ip spec for the given service_id.

    Args:
        service_id: The id of the service to create cluster ip for.
    """
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": service_id,
            "labels": {
                "app": service_id
            }
        },
        "spec": {
            "type": "ClusterIp",
            "selector": {
                "app": service_id
            },
            "ports": ports
        }
    }


def get_template():
    """Returns deployment template."""
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "",
            "labels": {
                "app": ""
            }
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": ""
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": ""
                    } 
                },
                "spec": {
                    "containers": []
                }
            }
        }
    }