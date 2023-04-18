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
from subprocess import PIPE, Popen, check_call

command: str = "velocitas exec runtime-local"
regex_dapr_app: Pattern[str] = compile(r".*You\'re up and running! Both Dapr and your app logs will appear here\.\n")
regex_mqtt: Pattern[str] = compile(r".*mosquitto version \d+\.\d+\.\d+ running\n")
regex_vdb: Pattern[str] = compile(r".*Listening on \d+\.\d+\.\d+\.\d+:\d+")
regex_client: Pattern[str]= compile(r".*[cC]onnected to data broker.*")
timeout_sec: float = 180


def run_command_until_logs_match(command: str, regex_service: Pattern[str], run_with_dapr: bool = False) -> bool:
    successfully_running_dapr: bool = True if not run_with_dapr else False
    successfully_running: bool = False

    proc: Popen[str] = Popen(command.split(" "), stdout=PIPE, bufsize=1, universal_newlines=True)
    timer: Timer = Timer(timeout_sec, proc.kill)
    timer.start()
    for line in iter(proc.stdout.readline, b""):
        if proc.poll() is not None:
            print(f"Timeout reached after {timeout_sec} seconds, process killed!")
            return False
        print(line)
        if run_with_dapr and regex_dapr_app.search(line):
            successfully_running_dapr = True
        if regex_service is not None and regex_service.search(line):
            successfully_running = True
        if successfully_running and successfully_running_dapr:
            timer.cancel()
            break
    return True


def test_scripts_run_successfully():
    assert 0 == check_call(f"{command} ensure-dapr", shell=True)
    assert run_command_until_logs_match(f"{command} run-mosquitto", regex_mqtt)
    assert run_command_until_logs_match(f"{command} run-vehicledatabroker", regex_vdb, True)
    assert run_command_until_logs_match(f"{command} run-feedercan", regex_client, True)
    assert run_command_until_logs_match(f"{command} run-vehicleservices", regex_client, True)