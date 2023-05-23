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

from controlplane import reset_controlplane
from runtime import undeploy_runtime
from yaspin import yaspin

from velocitas_lib import create_log_file


def runtime_down():
    """Stop the K3D runtime."""

    log_output = create_log_file("runtime-down", "runtime-k3d")
    with yaspin(text="Stopping k3d runtime...") as spinner:
        try:
            reset_controlplane(spinner, log_output)
            undeploy_runtime(spinner, log_output)
            spinner.ok("✔")
        except Exception as err:
            spinner.fail(err)


if __name__ == "__main__":
    runtime_down()
