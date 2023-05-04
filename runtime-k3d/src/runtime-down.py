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

from runtime.controlplane import reset_controlplane
from runtime.runtime import undeploy_runtime
from yaspin import yaspin


def runtime_down():
    """Stop the K3D runtime."""
    with yaspin(text="Stopping k3d runtime...") as spinner:
        try:
            reset_controlplane(spinner)
            undeploy_runtime(spinner)
            spinner.ok()
        except Exception as err:
            spinner.fail(err)


if __name__ == "__main__":
    runtime_down()
