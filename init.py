#!/usr/bin/env python

"""
Script to initialize the docker-compose.yml file

We want to avoid loading the config.py directly to access the CONFIG dict
information, because we want to have this dependency free, which can only
be guaranteed if we parse it as text.

Script parses the config file and sets up all relevant mount points and injects
their mapping information into the environment.
"""

# TODO: set up logging
# TODO: verify template correctness
# TODO: error handling
# TODO: encapsulate repeating logic

import argparse
import hashlib
import re

MOUNT_POINTS_IDENTIFIER = "paths"
SERVICE_NAME_DEFAULT = "mononel"
COMPOSE_VERSION_DEFAULT = "3.0"


def generate_docker_compose_file(service: str, compose_version: str):
    """

    Args:
        service (str): name of the service to set
        compose_version (str): version token for docker compose

    Returns:

    """
    with open("config.py") as f:
        config = f.read()
        # Let's strip all line breaks and spaces where it matters
        config = re.sub("(\n+\s+|\s*(?=:)|(?<=:)\s*)", "", config)

        mount_points = re.findall(
            r"(?<=\")([^\s,]*?)(?=\")",
            "{}".format(
                " ".join(
                    re.findall(
                        r"(?<=(?:'|\"){}(?:'|\"):\[).*?(?=\])".format(MOUNT_POINTS_IDENTIFIER),
                        config
                    )
                )
            )
        )

    # Let's remove any potential duplicates
    mount_points = set(mount_points)

    # parse template and substitute placeholders
    with open("docker-compose.template") as f:
        template = f.read()
        # Look up our {VOLUMES} placeholder and identify the indent we need to use
        indent_length = len(re.findall(r"(?<=\n)\s+(?=\{VOLUMES\})", template)[0])

        mounts_mapping = {_: hashlib.sha256(_.encode()).hexdigest()[:7] for _ in mount_points}
        replacement = "".join(
            [
                (r"\n" + " " * indent_length) + "- " +
                f"{k}:/{v}" for k, v in mounts_mapping.items()
            ]
        )
        content = re.sub("\s+\{VOLUMES\}", replacement, template)

        # Look up for our {ENVIRONMENT} placeholder and identify the indent we want to use
        indent_length = len(re.findall(r"(?<=\n)\s+(?=\{ENVIRONMENT\})", content)[0])
        replacement = "".join(
            [
                (r"\n" + " " * indent_length) + "- " + "CONTAINER=1"
            ] +
            [
                (r"\n" + " " * indent_length) + "- " +
                f"MOUNT_{v.rsplit('_', 1)[-1]}={k}" for k, v in mounts_mapping.items()
            ]
        )
        content = re.sub("\s+\{ENVIRONMENT\}", replacement, content)

        indent_length = len(re.findall(r"(?<=\n)\s+(?=\{SERVICE\})", content)[0])
        replacement = (r"\n" + " " * indent_length) + service
        content = re.sub("\s+\{SERVICE\}", replacement, content)

        content = re.sub("\{COMPOSE_VERSION\}", compose_version, content)

    # write the .yml file
    with open("docker-compose.yml", "w+") as f:
        f.write(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Monokel Initialization",
        description="",
        epilog="Please use `docker compose` to initialize the service with the .yml file the script created."
    )
    parser.add_argument(
        "-sn", "--service_name",
        type=str, default=SERVICE_NAME_DEFAULT,
        help="Set the root task for the job."
    )
    parser.add_argument(
        "-cv", "--compose_version",
        choices=["3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "4.0"],
        default=COMPOSE_VERSION_DEFAULT,
        help="Version token for the compose file."
    )
    args = parser.parse_args()

    generate_docker_compose_file(
        service=args.service_name,
        compose_version=args.compose_version
    )
