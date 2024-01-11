# Copyright (c) 2023-2024 Contributors to the Eclipse Foundation
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

# flake8: noqa: E402
import os
import sys

import pytest
from velocitas_lib.services import ServiceSpecConfig

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src/runtime"))
import deployment.gen_helm as gen_helm
from deployment.lib import generate_nodeport


@pytest.mark.parametrize(
    "env_vars",
    [{"CAN": "cansim"}, {"KUKSA_DATA_BROKER_PORT": "55555", "name": "value"}],
)
def test_generate_env_vars_spec(env_vars):
    env_vars_spec = gen_helm.generate_env_vars_spec(
        ServiceSpecConfig(image="image", env_vars=env_vars)
    )
    desired = [
        {
            "name": env[0],
            "value": env[1],
        }
        for env in env_vars.items()
    ]
    assert env_vars_spec == desired


@pytest.mark.parametrize("ports", [["9834"], ["0"], ["4567", "6789"]])
def test_gen_port_spec(ports):
    port_spec = gen_helm.generate_ports_spec(
        ServiceSpecConfig(image="image", ports=ports)
    )
    desired = [
        {
            "port": int(port),
            "nodePort": generate_nodeport(int(port)),
        }
        for port in ports
    ]
    assert port_spec == desired
