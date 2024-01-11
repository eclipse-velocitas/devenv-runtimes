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

from typing import Any, List


def generate_nodeport(port: int) -> int:
    """Create nodeport from the last 4 digits of the passed port in the range
    of 30000-32767. If the port is out of range it will just take the last 3 digits.

    Args:
        port: The port to be used to generate the nodeport.
    """
    nodeport = port % 10000
    if nodeport > 2767:
        nodeport = nodeport % 1000

    return int(f"3{nodeport:04d}")


def create_cluster_ip_spec(service_id: str, ports: List[dict]) -> dict[str, Any]:
    """Create cluster ip spec for the given service id.

    Args:
        service_id: The id of the service to create cluster ip for.
    """
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": service_id, "labels": {"app": service_id}},
        "spec": {"type": "ClusterIP", "selector": {"app": service_id}, "ports": ports},
    }
