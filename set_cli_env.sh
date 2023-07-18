#!/bin/bash

PACKAGE_PATH=~/.velocitas/packages/devenv-runtimes/hash_id

rm $PACKAGE_PATH
ln -s $(pwd) $PACKAGE_PATH
export VELOCITAS_WORKSPACE_DIR=.
export VELOCITAS_CACHE_DATA="{\"vspec_file_path\":\"vss.json\"}"
export runtimeFilePath=./runtime.json
export mockFilePath=./mock.py
