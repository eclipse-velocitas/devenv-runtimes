#!/bin/bash

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

PACKAGE_PATH=~/.velocitas/packages/devenv-runtimes/hash_id

rm $PACKAGE_PATH
ln -s $(pwd) $PACKAGE_PATH
export VELOCITAS_WORKSPACE_DIR=.
export VELOCITAS_CACHE_DATA="{\"vspec_file_path\":\"vss.json\"}"
export runtimeFilePath=./runtime.json
export mockFilePath=./mock.py
