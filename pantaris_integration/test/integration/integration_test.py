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
import subprocess
from pathlib import Path


def test_output():
    file_path = f"{Path.cwd()}/pantaris_integration/test/integration"
    file = f"{file_path}/sampleapp_manifest_v1.json"
    subprocess.run(
        [
            "velocitas",
            "exec",
            "pantaris-integration",
            "generated-desired-state",
            "-s",
            "ghcr.io/eclipse-velocitas/vehicle-app-python-template/sampleapp:v1",
            "-o",
            file_path,
        ]
    )
    assert os.path.isfile(file)
    with open(f"{file_path}/sampleapp_manifest_v1.json") as f:
        data = json.load(f)
        assert data == {
            "name": "SampleApp",
            "source": "ghcr.io/eclipse-velocitas/vehicle-app-python-template/sampleapp:v1",  # noqa E501
            "type": "binary/container",
            "requires": [
                "vss-source-default-vss:v3.0",
                "data-broker-grpc:v3.0",
                "mqtt:2.0.14",
            ],
            "provides": ["sampleapp:v1"],
        }
