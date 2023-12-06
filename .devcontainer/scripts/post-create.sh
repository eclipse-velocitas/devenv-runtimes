#!/bin/bash
# Copyright (c) 2023 Contributors to the Eclipse Foundation
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

echo "#######################################################"
echo "### Install python requirements                     ###"
echo "#######################################################"
# Update pip before installing requirements
pip3 install --upgrade pip
for package in runtime_k3d runtime_kanto runtime_local desired_state_generator; do

    REQUIREMENTS="$package/src/requirements.txt"
    if [ -f $REQUIREMENTS ]; then
        pip3 install -r $REQUIREMENTS
    fi
    REQUIREMENTS="$package/test/requirements.txt"
    if [ -f $REQUIREMENTS ]; then
        pip3 install -r $REQUIREMENTS
    fi

done
