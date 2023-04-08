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
from yaml.loader import FullLoader
import json
import os
import sys

def get_script_path() -> str:
    """Return the absolute path to the directory the invoked Python script
    is located in."""
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def get_services():
    """Return all specified services as Python object."""
    return json.load(open(f"{get_script_path()}/../../runtime.json", encoding="utf-8"))

def create_nodeport(service_id: str):
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

def get_template():
    """Return deployment template from yaml spec."""
    with open(f"{get_script_path()}/runtime/config/helm/templates/deployment_template.yaml", 'r') as f:
        return yaml.load(f, Loader=FullLoader)