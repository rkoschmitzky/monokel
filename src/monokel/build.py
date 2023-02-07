# TODO: verify template correctness
# TODO: error handling
# TODO: encapsulate repeating logic
# TODO: for external watchdog requirement perform merge (user precedence)

import hashlib
import os
import logging
import re
import shutil

from typing import Optional
from pathlib import Path

from pipreqs.pipreqs import init as create_requirements


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


LOG = logging.getLogger("monokel.build")


def build_package(config, output, service, compose_version, requirements=None, infer_requirements=False):
    # type: (Path, Path, str, str, Optional[Path], Optional[bool]) -> None
    """

    We want to avoid loading the config.py directly to access the CONFIG dict
    information, because we want to have this dependency free, which can only
    be guaranteed if we parse it as text.

    Script parses the config file and sets up all relevant mount points and injects
    their mapping information into the environment.

    Args:
        config (Path): path to python config file
        output (Path): path to output directory
        service (str): name of the service to set
        compose_version (str): version token for docker compose
        requirements (Path): path to the pip requirements file
        infer_requirements (bool): if True it will try to infer the package requirements automatically
            using the pipreqs package

    Returns:

    """

    with config.open() as f:
        config_content = f.read()

        LOG.debug(f"Current config content:\n{'-' * 50}\n{config_content}\n{'-' * 50}\n")

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
            ] +
            [
                (r"\n" + " " * indent_length) + "- " + "COMPOSE_PROJECT_NAME"
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

    LOG.info(f"Copying '{DOCKERFILE.resolve()}' into '{output.resolve()}'...")
    shutil.copy(DOCKERFILE, output)
    LOG.info(f"Copying '{RUN_FILE.resolve()}' into '{output.resolve()}'")
    shutil.copy(RUN_FILE, output)

    # if given and not handled upfront the given requirements file will have precedence
    if requirements:
        LOG.info(f"Copying '{requirements.resolve()}' into '{output.resolve()}'...")
        shutil.copy(requirements, output, follow_symlinks=True)
    elif infer_requirements:
        pipreqs_args = {
            "<path>": str(output.resolve()),
            "--pypi-server": None,
            "--proxy": None,
            "--use-local": False,
            "--debug": False,
            "--ignore": ",".join([".hg", ".svn", ".git", ".tox", "__pycache__", "env", "venv"]),
            "--no_follow_links": False,
            "--encoding": None,
            "--savepath": str(output.joinpath("requirements.txt").resolve()),
            "--print": None,
            "--force": True,
            "--diff": None,
            "--clean": None,
            "--mode": None
        }
        LOG.info(f"Inferring requirements and writing into '{pipreqs_args['--savepath']}'")
        create_requirements(pipreqs_args)
    else:
        raise AssertionError(
            "Either a requirements file has to be provided or infer_requirements needs to be set to True."
        )

    LOG.info(
        f"Build finished. Continue from '{output.resolve()}' "
        f"and use docker compose with the included docker-compose.yml."
    )
