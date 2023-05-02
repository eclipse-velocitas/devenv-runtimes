from runtime.controlplane import configure_controlplane
from runtime.runtime import deploy_runtime


def main():
    print("Starting k3d runtime...")
    configure_controlplane()
    deploy_runtime()


if __name__ == "__main__":
    main()
