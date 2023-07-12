# Velocitas Runtimes Package

[![License: Apache](https://img.shields.io/badge/License-Apache-yellow.svg)](http://www.apache.org/licenses/LICENSE-2.0)

A Velocitas CLI package containing all available and supported Velocitas runtimes and deployments.

## Runtimes

This package contains the following runtimes:

* [Local](./runtime-local/README.md)
* [Kubernetes (K3D)](./runtime-k3d/README.md)

## Runtime Configuration (runtime.json)

This JSON file contains an array of services which should be started by all runtimes. Every service entry
consists of a unique `id`, its provided `interfaces` and its key-value based `config`.


### Configuration Values
For config values, here is a list of supported key-value pairs:

| Key | Value examples | Description |
|:----|:--|:------|
`no-dapr` | `"true"`, `"false"` | If set to `"true"` the service will not use dapr when middleware is configured to dapr. Useful for enabling services like MQTT or a database.
`enabled` | `"true"`, `"false"` | If set to `"false"` the service will not be started by the runtimes. Defaults to `"true"`.
`image` | `ghcr.io/eclipse/kuksa.val.feeders/dbc2val:v0.1.1` | A fully qualified URI to a OCI compliant container image located within a container registry
`arg` | `-c` | Argument to be passed to the spawned service. Can be passed multiple times for multiple arguments; arguments are forwarded in the order of definition in that case.
`env` | `foo=bar` | Environment variable key-value pair to be passed to the spawned service.
`mount` | `/config/feedercan/:/data` | Mount `from_host:to_container` pair to pass to the spawned service. Can be passed multiple times for multiple mounts. Both paths need to be **absolute**.
`port` | `8080` | Port exposed by the spawned service. Can be passed multiple times for multiple ports.
`port-forward` | `8080:8080` | Port forwarded from containerized service to the host. Can be passed multiple times for multiple forwards.
`start-pattern` | `".*mosquitto version \\d+\\.\\d+\\.\\d+ running\n"` | Regex pattern which identifies a proper startup of the service. If passed multiple times, all patterns have to match.

### Dynamic value resolution in configuration

Each of the supported keys may need to use dynamic values i.e. from [Velocitas CLI variables](https://github.com/eclipse-velocitas/cli/blob/main/docs/features/VARIABLES.md).

To use these in the `runtime.json`'s config keys, refer to the variable name within a `${{ }}` block, i.e. `${{ myVariable }}`.

In addition to CLI variables, some builtin variables are available:

| Variable name | Description |
|:---|:----|
`builtin.package_dir` | The path to the current package root which contains the package's `manifest.json`
 `builtin.cache.cache_key` | The value of the cache entry with key *cache_key*, e.g. `builtin.cache.vspec_file_path`

Finally, sometimes a single variable substitution is not enough. Among others, you may want to look up a file in a directory and - if it does not exist - fall back to a default file provided by the package. This is where function execution within value entries comes to your rescue.

Available functions:

Function | Description
:---|:---
`$pathInWorkspaceOrPackage( <relative_path> )` | Resolves a path dynamically either to the local project workspace, if the file is available or falls back to a file in the package repository. If none of these files is available an exception is raised.
