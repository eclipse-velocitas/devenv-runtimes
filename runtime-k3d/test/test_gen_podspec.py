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

# flake8: noqa: E402
import os
import sys
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from gen_podspec import generate_port_spec
from lib import ServiceSpecConfig


@pytest.mark.parametrize("ports", [["1234"], ["0"], ["4567", "1234"]])
def test_gen_port_spec(ports):
    port_spec = generate_port_spec(
        ServiceSpecConfig(None, None, None, None, ports, None)
    )
    desired = [
        {
            "name": f"port{port}",
            "containerPort": int(port),
            "protocol": "TCP",
        }
        for port in ports
    ]
    assert port_spec == desired
