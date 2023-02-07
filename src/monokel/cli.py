#!/usr/bin/env python

"""
Commandline Interface for Monokel

Subcommands:
    build: Create the docker-compose file and all the dependencies that have to be injected into the container
        into a single output directory.
"""


import argparse
import logging
import sys

from pathlib import Path

from .build import (
    build_package,
    SERVICE_NAME_DEFAULT,
    CONFIG_PATH_DEFAULT,
    REQUIREMENTS_PATH_DEFAULT,
    COMPOSE_VERSION_DEFAULT,
    BUILD_PATH_DEFAULT
)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s | %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stdout
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


def cli():
    parser = argparse.ArgumentParser(
        prog="Monokel",
        description="Monkel's Commandline Interface"
    )
    parser.add_argument(
        "-v", "--verbosity",
        choices=logging._nameToLevel.keys(),
        default=logging.INFO
    )

    subparsers = parser.add_subparsers(
        title="subcommands",
        dest="subcommand",
        required=True
    )

    # TODO: add a way to store and pick up cli options
    build_parser = subparsers.add_parser(
        "build",
        help="Create a package with all container dependencies and compose file for docker compose",
    )
    build_parser.add_argument(
        "-sn", "--service-name",
        type=str, default=SERVICE_NAME_DEFAULT,
        help="The name of the docker service."
    )
    build_parser.add_argument(
        "-c", "--config",
        type=ArgType.existing_file, default=CONFIG_PATH_DEFAULT,
        help="Filepath to python config file."
    )
    build_parser.add_argument(
        "-r", "--requirements",
        type=ArgType.existing_file,
        help="Filepath to the pip requirements."
    )
    build_parser.add_argument(
        "-ir", "--infer-requirements",
        action="store_true",
        help="Will parse the given config file and automatically creates a pip requirements file."
    )
    build_parser.add_argument(
        "-o", "--output",
        type=ArgType.path_skeleton, default=BUILD_PATH_DEFAULT,
        help="Build directory path that will be used to create all required outputs."
    )
    build_parser.add_argument(
        "-cv", "--compose-version",
        choices=["3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "4.0"],
        default=COMPOSE_VERSION_DEFAULT,
        help="Version token for the compose file."
    )

    args = parser.parse_args()

    logging.getLogger("monokel").setLevel(
        logging.getLevelName(args.verbosity)
    )

    if args.subcommand == "build":
        if args.requirements and args.infer_requirements:
            parser.error(
                "If you want to use the the option to infer requirements "
                "you can't use the option to provide requirements at the same time."
            )
        if not args.requirements and not args.infer_requirements:
            parser.error(
                "Either a requirements file has to be provided (-r <requirements_file>) "
                "or infer_requirements (-ir) needs to be set."
            )

        build_package(
            config=args.config,
            requirements=args.requirements,
            output=args.output,
            service=args.service_name,
            compose_version=args.compose_version,
            infer_requirements=args.infer_requirements
        )


if __name__ == "__main__":
    cli()
