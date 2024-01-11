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

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src/runtime"))
from deployment.lib import generate_nodeport


def test_generate_nodeport_in_range():
    assert generate_nodeport(1883) == 31883
    assert generate_nodeport(0) == 30000
    assert generate_nodeport(2767) == 32767
    assert generate_nodeport(999) == 30999


def test_generate_nodeport_out_of_range():
    assert generate_nodeport(5555) == 30555
    assert generate_nodeport(2768) == 30768
