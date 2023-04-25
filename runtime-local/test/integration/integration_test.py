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

from re import compile, Pattern
from threading import Timer
from subprocess import PIPE, Popen

command: str = "velocitas exec runtime-local"
regex_runtime_up: Pattern[str] = compile(r"✔.* Starting runtime")
regex_mqtt: Pattern[str] = compile(r"✔.* Starting service mqtt")
regex_vdb: Pattern[str] = compile(r"✔.* Starting service vehicledatabroker")
regex_seatservice: Pattern[str]= compile(r"✔.* Starting service seatservice")
regex_feedercan: Pattern[str]= compile(r"✔.* Starting service feedercan")
timeout_sec: float = 180


def run_command_until_logs_match(command: str, regex_service: Pattern[str]) -> bool:
    successfully_running: bool = False

    proc: Popen[str] = Popen(command.split(" "), stdout=PIPE, bufsize=1, universal_newlines=True)
    timer: Timer = Timer(timeout_sec, proc.kill)
    timer.start()
    for line in iter(proc.stdout.readline, b""):
        if proc.poll() is not None:
            print(f"Timeout reached after {timeout_sec} seconds, process killed!")
            return False
        print(line)
        if regex_service is not None and regex_service.search(line):
            timer.cancel()
            break
    return True


def test_runtime_up_successfully():
    assert run_command_until_logs_match(f"{command} up", regex_runtime_up)


def test_run_sevices_separately_successfully():
    assert run_command_until_logs_match(f"{command} run-mosquitto", regex_mqtt)
    assert run_command_until_logs_match(f"{command} run-vehicledatabroker", regex_vdb)
    assert run_command_until_logs_match(f"{command} run-vehicleservices", regex_seatservice)
    assert run_command_until_logs_match(f"{command} run-feedercan", regex_feedercan)
