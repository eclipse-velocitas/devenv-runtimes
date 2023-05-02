# Copyright (c) 2023 Robert Bosch GmbH and Microsoft Corporation
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

"""Provides methods and functions to download and install dependencies."""
# flake8: noqa: E402 module level import
import os
import subprocess
from pathlib import Path
import sys
sys.path.append(os.path.join(Path(__file__).parents[2], "velocitas_lib"))
from velocitas_lib import get_script_path

def pip(args: list[str]) -> None:
    """Invoke the pip process with the given arguments."""
    subprocess.check_call([sys.executable, "-m", "pip", *args])


def install_packages():
    """Install all required Python packages."""
    script_path = get_script_path()
    pip(["install", "-r", f"{script_path}/requirements.txt"])


if __name__ == "__main__":
    install_packages()
