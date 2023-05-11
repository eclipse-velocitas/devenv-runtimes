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
from typing import Optional

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src/runtime"))
import deployment.gen_podspec as gen_podspec
from deployment.lib import ServiceSpecConfig, generate_nodeport


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
        "test/test.json:test/test.json",
        "test/test.json:test.json",
    ],
)
def test_get_mount_file(mount):
    _, file = gen_podspec.get_mount_folder_and_file(mount)
    expected = os.path.basename(mount.split(":")[1])
    assert file == expected


@pytest.mark.parametrize(
    "mount",
    [
        pytest.param("test:test", marks=pytest.mark.xfail),
        "test/test.json:test/test.json",
        "test/test.json:test.json",
    ],
)
def test_get_volumes_file(mount):
    volumes = gen_podspec.get_volumes(
        ServiceSpecConfig(None, None, None, None, None, [mount])
    )
    file_name = os.path.splitext(gen_podspec.get_mount_folder_and_file(mount)[1])[0]
    desired = [
        {
            "name": f"{file_name}",
            "configMap": {"name": f"{file_name}-config"},
        }
    ]
    assert volumes == desired


@pytest.mark.parametrize(
    "mount",
    [
        pytest.param("test/test.json:test.json", marks=pytest.mark.xfail),
        "test/test:test/test",
        "test/test:test",
    ],
)
def test_get_volumes_folder(mount):
    volumes = gen_podspec.get_volumes(
        ServiceSpecConfig(None, None, None, None, None, [mount])
    )
    desired = [
        {
            "name": "pv-storage",
            "persistentVolumeClaim": {"claimName": "pv-claim"},
        }
    ]
    assert volumes == desired


@pytest.mark.parametrize(
    "mount",
    [
        pytest.param("test:test", marks=pytest.mark.xfail),
        "test/test.json:test/test.json",
        "test/test.json:test.json",
    ],
)
def test_get_container_mount_file(mount):
    mounts = gen_podspec.generate_container_mount(
        ServiceSpecConfig(None, None, None, None, None, [mount])
    )
    path, file = gen_podspec.get_mount_folder_and_file(mount)
    desired = [
        {
            "name": f"{os.path.splitext(file)[0]}",
            "mountPath": f"{path}/{file}",
            "subPath": f"{file}",
        }
    ]
    assert mounts == desired


@pytest.mark.parametrize(
    "mount",
    [
        pytest.param("test/test.json:test.json", marks=pytest.mark.xfail),
        "test/test:test/test",
        "test/test:test",
    ],
)
def test_get_container_mount_folder(mount):
    mounts = gen_podspec.generate_container_mount(
        ServiceSpecConfig(None, None, None, None, None, [mount])
    )
    path, _ = gen_podspec.get_mount_folder_and_file(mount)
    desired = [{"mountPath": f"{path}", "name": "pv-storage"}]
    assert mounts == desired


@pytest.mark.parametrize(
    "key,value",
    [("test_key", "test_value"), ("", None)],
)
def test_get_env(key, value):
    env = dict[str, Optional[str]]()
    env[key] = value
    env_array = gen_podspec.get_env(
        ServiceSpecConfig(None, env, None, None, None, None)
    )

    desired = [{"name": key, "value": value}]
    assert env_array == desired


@pytest.mark.parametrize(
    "service_id,port",
    [("test", "1234"), ("", "0")],
)
def test_get_nodeport_service(service_id, port):
    service = gen_podspec.generate_nodeport_service(service_id, port)

    desired = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": f"{service_id}-nodeport{port}"},
        "spec": {
            "type": "NodePort",
            "selector": {"app": f"{service_id}"},
            "ports": [
                {
                    "port": int(port),
                    "targetPort": int(port),
                    "nodePort": generate_nodeport(int(port)),
                }
            ],
        },
    }
    assert service == desired
