#!/bin/bash
# Copyright (c) 2022 Robert Bosch GmbH and Microsoft Corporation
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

if ! helm status vehicleappruntime &> /dev/null
then
    DEPENDENCIES=$(echo $VELOCITAS_APP_MANIFEST | jq .dependencies)
    SERVICES=$(echo $DEPENDENCIES | jq '.services')

    SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    CONFIG_DIR="$(dirname "$SCRIPT_DIR")/runtime/config"

    docker pull $DATABROKER_IMAGE:$DATABROKER_TAG
    docker tag $DATABROKER_IMAGE:$DATABROKER_TAG localhost:12345/vehicledatabroker:$DATABROKER_TAG
    docker push localhost:12345/vehicledatabroker:$DATABROKER_TAG

    docker pull $FEEDERCAN_IMAGE:$FEEDERCAN_TAG
    docker tag $FEEDERCAN_IMAGE:$FEEDERCAN_TAG localhost:12345/feedercan:$FEEDERCAN_TAG
    docker push localhost:12345/feedercan:$FEEDERCAN_TAG

    readarray -t SERVICES_ARRAY < <(echo $SERVICES | jq -c '.[]')

    for service in ${SERVICES_ARRAY[@]}; do
        SERVICE_NAME=$(echo $service | jq '.name' | tr -d '"' )
        SERVICE_IMAGE=$(echo $service | jq '.image' | tr -d '"')
        SERVICE_TAG=$(echo $service | jq '.version' | tr -d '"')
        if [ $SERVICE_IMAGE = "null" ] || [ $SERVICE_TAG = "null" ];then
            echo "Missing configuration in AppManifest.json for Service: $SERVICE_NAME"
        else
            echo "Pulling and pushing service docker image to local registry for: $SERVICE_NAME"
            docker pull $SERVICE_IMAGE:$SERVICE_TAG
            docker tag $SERVICE_IMAGE:$SERVICE_TAG localhost:12345/$SERVICE_NAME:$SERVICE_TAG
            docker push localhost:12345/$SERVICE_NAME:$SERVICE_TAG
        fi
    done

    VSPEC_FILE_PATH=$(echo $VELOCITAS_CACHE_DATA | jq .vspec_file_path | tr -d '"')

    if [ ! "$VSPEC_FILE_PATH" == null ] && [ -n "$VSPEC_FILE_PATH" ]
        then
            echo "Creating configmap for vspec file"
            kubectl create configmap vspec-config --from-file=$VSPEC_FILE_PATH
    fi

    # We set the tag to the version from the variables above in the script. This overwrites the default values in the values-file.
    helm install vehicleappruntime \
        $CONFIG_DIR/helm \
        --values $CONFIG_DIR/helm/values.yaml \
        --set imageSeatService.tag=$SEATSERVICE_TAG \
        --set imageVehicleDataBroker.tag=$DATABROKER_TAG \
        --set imageFeederCan.tag=$FEEDERCAN_TAG \
        --set vspecFilePath=$VSPEC_FILE_PATH \
        --wait \
        --timeout 60s \
        --debug

else
    echo "Runtime already deployed. To redeploy the components, run the task 'K3D - Uninstall runtime' first."
fi

helm status vehicleappruntime
kubectl get svc --all-namespaces
kubectl get pods
