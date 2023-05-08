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
import gen_podspec
from lib import ServiceSpecConfig


@pytest.mark.parametrize("ports", [["1234"], ["0"], ["4567", "1234"]])
def test_gen_port_spec(ports):
    port_spec = gen_podspec.generate_port_spec(
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


@pytest.mark.parametrize("ports", [["1234"], ["0"], ["4567", "1234"]])
def test_gen_clusterIp_port_spec(ports):
    port_spec = gen_podspec.generate_clusterIP_port_spec(
        ServiceSpecConfig(None, None, None, None, ports, None)
    )
    desired = [
        {
            "name": f"port{port}",
            "port": int(port),
            "targetPort": int(port),
            "protocol": "TCP",
        }
        for port in ports
    ]
    assert port_spec == desired


@pytest.mark.parametrize("service_id,port", [("test", "1234"), ("", "0")])
def test_gen_mqtt_pubsub(service_id, port):
    gen = gen_podspec.gen_mqtt_pubsub(service_id, port)
    desired = {
        "apiVersion": "dapr.io/v1alpha1",
        "kind": "Component",
        "metadata": {"name": "mqtt-pubsub", "namespace": "default"},
        "spec": {
            "type": "pubsub.mqtt",
            "version": "v1",
            "metadata": [
                {
                    "name": "url",
                    "value": f"tcp://{service_id}.default.svc.cluster.local:{port}",
                },
                {"name": "qos", "value": 1},
                {"name": "retain", "value": "false"},
                {"name": "cleanSession", "value": "false"},
            ],
        },
    }
    assert gen == desired


@pytest.mark.parametrize(
    "mount",
    [
        "test:test",
        "/test/test/test:test",
        pytest.param("test/test.json:test.json", marks=pytest.mark.xfail),
    ],
)
def test_get_mount_folder(mount):
    path, _ = gen_podspec.get_mount_folder_and_file(mount)
    expected = mount.split(":")[1]

    assert path == expected


@pytest.mark.parametrize(
    "mount",
    [
        pytest.param("test:test", marks=pytest.mark.xfail),
        "test/test.json:test.json",
    ],
)
def test_get_mount_file(mount):
    _, file = gen_podspec.get_mount_folder_and_file(mount)
    expected = mount.split(":")[1]
    assert file == expected
