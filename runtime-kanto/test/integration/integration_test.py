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

from re import Pattern, compile
from subprocess import check_call, check_output

BASE_COMMAND_RUNTIME = "velocitas exec runtime-kanto"
BASE_COMMAND_DEPLOYMENT = "velocitas exec deployment-kanto"

kubectl_regs = {
    compile(r".*Kubernetes control plane is running"): False,
    compile(r".*CoreDNS is running"): False,
    compile(r".*Metrics-server is running"): False,
}

image_reg = {compile(r"localhost:12345/sampleapp\s+local.+"): False}

container_regs = {
    compile(r".*mqttbroker-.+-.+\s+1/1\s+Running.*"): False,
    compile(r".*bash-.+-.+\s+1/1\s+Running.*"): False,
    compile(r".*seatservice-.+-.+\s+2/2\s+Running.*"): False,
    compile(r".*feedercan-.+-.+\s+2/2\s+Running.*"): False,
    compile(r".*vehicledatabroker-.+-.+\s+2/2\s+Running.*"): False,
    compile(r".*zipkin-.+-.+\s+1/1\s+Running.*"): False,
    compile(r".*sampleapp-.+-.+\s+2/2\s+Running.*"): False,
}


def escape_ansi(line):
    ansi_escape = compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")
    return ansi_escape.sub("", line)


def matches_any_regex(regex_dict: dict[Pattern, bool], input: str) -> bool:
    final_flag = True
    print(input)
    for reg in regex_dict:
        if not regex_dict[reg]:
            if reg.search(input):
                regex_dict[reg] = True
        final_flag = final_flag and regex_dict[reg]
    return final_flag


def check_image_if_created(image_reg: Pattern) -> bool:
    command_get_images_logs = check_output(["docker", "images"]).decode()
    return matches_any_regex(image_reg, command_get_images_logs)


def check_containers(container_regs: dict) -> bool:
    command_get_pods_logs = check_output(["kanto-cm", "list"]).decode()
    return matches_any_regex(container_regs, command_get_pods_logs)


def run_command(command: str) -> bool:
    return check_call(command.split(" ")) == 0


def test_scripts_run_successfully():
    assert run_command(f"{BASE_COMMAND_RUNTIME} install-deps")
    assert run_command(f"{BASE_COMMAND_RUNTIME} up")
    assert run_command(f"{BASE_COMMAND_DEPLOYMENT} build-vehicleapp")
    assert check_image_if_created(image_reg)
    assert run_command(f"{BASE_COMMAND_DEPLOYMENT} deploy-vehicleapp")
    assert check_containers(container_regs)
    assert run_command(f"{BASE_COMMAND_RUNTIME} down")
