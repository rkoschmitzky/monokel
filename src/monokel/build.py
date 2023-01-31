#!/usr/bin/env python

"""
Script to initialize the docker-compose.yml file

We want to avoid loading the config.py directly to access the CONFIG dict
information, because we want to have this dependency free, which can only
be guaranteed if we parse it as text.

Script parses the config file and sets up all relevant mount points and injects
their mapping information into the environment.
"""

# TODO: verify template correctness
# TODO: error handling
# TODO: encapsulate repeating logic
# TODO: for external watchdog requirement perform merge (user precedence)

import argparse
import hashlib
import os
import logging
import re
import shutil
import sys

from pathlib import Path


MOUNT_POINTS_IDENTIFIER = "paths"
SERVICE_NAME_DEFAULT = "monokel"
COMPOSE_VERSION_DEFAULT = "3.0"

SOURCE_PATH = Path(__file__).parent
TEMPLATES_PATH = SOURCE_PATH.joinpath("templates")

CONFIG_PATH_DEFAULT = SOURCE_PATH.joinpath(os.getenv("MONOKEL_CONFIG", "../../config.py"))
BUILD_PATH_DEFAULT = SOURCE_PATH.joinpath(os.getenv("MONOKEL_BUILD_DIR", "../../build"))
REQUIREMENTS_PATH_DEFAULT = TEMPLATES_PATH.joinpath("requirements.txt")
DOCKER_COMPOSE_TEMPLATE_PATH = TEMPLATES_PATH.joinpath("docker-compose.yml")
DOCKERFILE = TEMPLATES_PATH.joinpath("Dockerfile")
RUN_FILE = SOURCE_PATH.joinpath("run.py")


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s | %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stdout
)

LOG = logging.getLogger("monokel.build")


def generate_docker_compose_file(config, requirements, output, service, compose_version):
    # type: (Path, Path, Path, str, str) -> None
    """

    Args:
        config (Path): path to python config file
        requirements (Path): path to the pip requirements file
        output (Path): path to output directory
        service (str): name of the service to set
        compose_version (str): version token for docker compose

    Returns:

    """

    with config.open() as f:
        config_content = f.read()

        LOG.debug(f"Current config content: \n{config_content}\n")

        # TODO: add more validations during build stage
        if not re.search(r"CONFIG\s*=[\s\n\t\\]*\{", config_content):
            raise ValueError(
                f"Missing CONFIG variable in given config file '{config}'"
            )

        LOG.debug(f"Validated `CONFIG` dict in `{config}`.")

        # Let's strip all line breaks and spaces where it matters
        config_content = re.sub("(\n+\s+|\s*(?=:)|(?<=:)\s*)", "", config_content)

        mount_points = re.findall(
            r"(?<=\")([^\s,]*?)(?=\")",
            "{}".format(
                " ".join(
                    re.findall(
                        r"(?<=(?:'|\"){}(?:'|\"):\[).*?(?=\])".format(MOUNT_POINTS_IDENTIFIER),
                        config_content
                    )
                )
            )
        )

    # Let's remove any potential duplicates
    mount_points = set(mount_points)

    LOG.debug(f"Identified mount pounts: {mount_points}")

    # parse template and substitute placeholders
    with TEMPLATES_PATH.joinpath("docker-compose.yml").open() as f:
        template = f.read()
        # Look up our {VOLUMES} placeholder and identify the indent we need to use
        indent_length = len(re.findall(r"(?<=\n)\s+(?=\{VOLUMES\})", template)[0])

        mounts_mapping = {_: hashlib.sha256(_.encode()).hexdigest()[:8] for _ in mount_points}

        LOG.debug(f"Defined mounts mapping: {mounts_mapping}")

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

    LOG.info(f"Creating output directory '{output}'...")
    output.mkdir(exist_ok=True)

    LOG.info(f"Writing docker-compose.yml...")
    with output.joinpath(DOCKER_COMPOSE_TEMPLATE_PATH.name).open("w+") as f:
        f.write(content)

    config_copy = output.joinpath("config.py")
    LOG.info(f"Copying '{config.resolve()}' -> '{config_copy.resolve()}'...")
    shutil.copy(config, config_copy, follow_symlinks=True)
    LOG.info(f"Copying '{requirements.resolve()}' into '{output.resolve()}'...")
    shutil.copy(requirements, output, follow_symlinks=True)
    LOG.info(f"Copying '{DOCKERFILE.resolve()}' into '{output.resolve()}'...")
    shutil.copy(DOCKERFILE, output)
    LOG.info(f"Copying '{RUN_FILE.resolve()}' into '{output.resolve()}'")
    shutil.copy(RUN_FILE, output)

    LOG.info(
        f"Build finished. Continue from '{output.resolve()}' "
        f"and use docker compose with the included docker-compose.yml."
    )


class ArgType:
    """ Argument type extensions """
    @staticmethod
    def existing_directory(path):
        # type: (str) -> Path

        path = Path(path)
        if path.is_dir():
            return path
        else:
            raise argparse.ArgumentTypeError(f"'{path}' is not a valid path.")

    @staticmethod
    def existing_file(path):
        # type: (str) -> Path

        path = Path(path)
        if path.is_file():
            return path
        else:
            raise argparse.ArgumentTypeError(f"'{path}' is not a valid file.")

    @staticmethod
    def path_skeleton(path):
        # type: (str) -> Path
        return Path(path)


def main():
    parser = argparse.ArgumentParser(
        prog="Monokel Build",
        description="",
        epilog="Please use `docker compose up <BUILD>/docker-compose.yml` to initialize the service that was created."
    )
    parser.add_argument(
        "-sn", "--service_name",
        type=str, default=SERVICE_NAME_DEFAULT,
        help="The name of the docker service."
    )
    # TODO: While these can be optional defaults are good for prototyping
    #  we need to change them to be required without a default once this
    #  will be installed via pip - we might want to consider env vars
    parser.add_argument(
        "-c", "--config",
        type=ArgType.existing_file, default=CONFIG_PATH_DEFAULT,
        help="Filepath to python config file."
    )
    parser.add_argument(
        "-r", "--requirements",
        type=ArgType.existing_file, default=REQUIREMENTS_PATH_DEFAULT,
        help="Filepath to the pip requirements."
    )
    parser.add_argument(
        "-o", "--output",
        type=ArgType.path_skeleton, default=BUILD_PATH_DEFAULT,
        help="Build directory path that will be used to create all required outputs."
    )
    #

    parser.add_argument(
        "-cv", "--compose_version",
        choices=["3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "4.0"],
        default=COMPOSE_VERSION_DEFAULT,
        help="Version token for the compose file."
    )
    parser.add_argument(
        "-v", "--verbosity",
        choices=logging._nameToLevel.keys(),
        default=logging.INFO
    )
    args = parser.parse_args()

    logging.getLogger("monokel").setLevel(
        logging.getLevelName(args.verbosity)
    )

    generate_docker_compose_file(
        config=args.config,
        requirements=args.requirements,
        output=args.output,
        service=args.service_name,
        compose_version=args.compose_version
    )


if __name__ == "__main__":
    main()
