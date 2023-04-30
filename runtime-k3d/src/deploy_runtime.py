import argparse
import subprocess

from lib import get_services, parse_service_config
from gen_helm import gen_helm


def is_runtime_installed() -> bool:
    return subprocess.check_call(["helm", "status", "vehicleappruntime"]) == 0


def retag_docker_image(image_name: str):
    subprocess.check_call(["docker", "pull", image_name])
    subprocess.check_call([
        "docker",
        "tag",
        image_name,
        f"localhost:12345/{image_name}"
        ])
    subprocess.check_call(["docker", "push", f"localhost:12345/{image_name}"])


def retag_docker_images():
    services = get_services()
    for service in services:
        service_config = parse_service_config(service)
        retag_docker_image(service_config.image)


def install_runtime(helm_output_path: str):
    subprocess.check_call([
        "helm",
        "install",
        "vehicleappruntime",
        f"{helm_output_path}",
        "--values",
        f"{helm_output_path}/values.yaml",
        "--set",
        "vspecFilePath=$VSPEC_FILE_PATH"
        "--wait",
        "--timeout",
        "60s",
        "--debug"
    ])


def main():
    if not is_runtime_installed():
        gen_helm("./helm")
        retag_docker_images()
        install_runtime("./helm")
    else:
        print("Runtime already installed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("deploy-runtime")
    args = parser.parse_args()

    main()
