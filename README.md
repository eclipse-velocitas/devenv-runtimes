# Velocitas Runtimes Package

[![License: Apache](https://img.shields.io/badge/License-Apache-yellow.svg)](http://www.apache.org/licenses/LICENSE-2.0)

A Velocitas CLI package containing all available and supported Velocitas runtimes.

## Runtime Local

This runtime brings up a local runtime, based on Docker and dapr, consisting of the following items:

* Mosquitto MQTT broker
* Kuksa Vehicle Databroker
* Kuksa Seat Service
* Kuksa Feeder Can

## Runtime K3D

This runtime brings up a Kubernetes cluster into which Velocitas Vehicle Apps can be deployed.
It consists of the following items:

* Mosquitto MQTT broker
* Kuksa Vehicle Databroker
* Kuksa Seat Service
* Kuksa Feeder Can

## Deployment K3D

This deployment enables the development environment to deploy Velocitas Vehicle Apps into the K3D runtime.
