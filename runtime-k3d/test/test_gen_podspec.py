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
import os
import sys

sys.path.append(os.path.abspath("/workspaces/devenv-runtimes/runtime-k3d/src"))
from gen_podspec import generate_port_spec
from lib import ServiceSpecConfig


def test_gen_port_spec():
    port_spec = generate_port_spec(
        ServiceSpecConfig(None, None, None, None, ["1234", "5678", "0"], None)
    )
    desired = [
        {
            "name": "port1234",
            "containerPort": 1234,
            "protocol": "TCP",
        },
        {
            "name": "port5678",
            "containerPort": 5678,
            "protocol": "TCP",
        },
        {
            "name": "port0",
            "containerPort": 0,
            "protocol": "TCP",
        },
    ]
    assert port_spec == desired
