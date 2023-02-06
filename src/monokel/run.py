"""
Monokel's main event loop.

This sets up the watchdog observer and schedules all handlers for the configured paths.
"""

import logging
import os
import re
import time


LOG = logging.getLogger("monokel.run")
HEARTBEAT_RATE = 60


def _patch_events(volumes_mapping):
    # type: (dict) -> None
    """ To support our volumes mapping we need to patch FileSystemEvents

    This ensures we keep track of the actual location by resolving our
    dynamic volume mounts from within the container.

    Args:
        volumes_mapping (dict): the mappings required for lookup
    """
    from watchdog.events import (
        FileSystemEvent,
        FileSystemMovedEvent
    )

    FileSystemEvent.src_path = property(
        lambda self: resolve_path(self._src_path, volumes_mapping, revert=True)
    )
    FileSystemMovedEvent.dest_path = property(
        lambda self: resolve_path(self._dest_path, volumes_mapping, revert=True)
    )


def _validate_config(config):
    from watchdog.observers.api import BaseObserver

    observer = config.get("observer")
    if not observer:
        raise KeyError(
            "'observer' entry missing in config.CONFIG or having no value."
        )
    if not isinstance(observer, BaseObserver):
        raise ValueError(
            "'observer entry value is not of type watchdog.observers.api.BaseObserver."
        )

    watchers = config.get("watchers")
    if not watchers:
        raise ValueError(
            "'watchers' entry missing in config.CONFIG or having no value."
        )


def _get_volume_mappings():
    # type: () -> dict
    """ get the mounted volume mappins

        Returns:
            dict: volume mappings
        """

    mappings = {}

    for key, value in os.environ.items():
        if re.match(r"^MOUNT_[a-fA-F0-9]{8}", key):
            mappings[value] = f"/{key.strip('MOUNT_')}"
            LOG.info(f"Detected mapping for given path '{value}' -> '{mappings[value]}'")

    return mappings


def resolve_path(path, volumes_mapping, revert=False):
    # type: (str, dict, bool) -> str
    """ get the resolved path for the volume

    Args:
        path (str): path to resolve
        volumes_mapping (dict): the mappings required for lookup
        revert (bool): False - origin -> mounted; True - mounted -> origin

    Returns:
        str: the resolved path
    """
    # TODO: this needs proper handling if a given path can't be resolved
    if not os.getenv("CONTAINER"):
        return path
    else:
        LOG.debug("Detected in-container run...")

        if not revert:
            # directory case
            result = volumes_mapping.get(path)
            if result:
                return result
            else:
                # file case
                return os.path.join(
                    volumes_mapping.get(os.path.split(path)[0]),
                    os.path.split(path)[1]
                )
        else:
            # directory case
            result = next((k for k, v in volumes_mapping.items() if v == path), None)
            if result:
                return result
            else:
                # file case
                return os.path.join(
                    next((k for k, v in volumes_mapping.items() if v == os.path.split(path)[0]), None),
                    os.path.split(path)[1]
                )


def main():
    """ Start the event loop...
    
    Load configuration (all required dependencies within it have to be installed via 
    requirements.txt), identify the volume mappings and register the associated 
    eventhandlers with the mapped paths.
    """
    volume_mappings = _get_volume_mappings()

    # TODO: while this works when build we should make this
    #  configurable via envvar - users might have their config.py for testing elsewhere
    from config import CONFIG

    _validate_config(CONFIG)
    _patch_events(volume_mappings)

    observer = CONFIG.get("observer")

    for watcher in CONFIG.get("watchers"):
        for path in watcher.get("paths"):
            handler = watcher.get("handler")

            resolved_path = resolve_path(path, volume_mappings)
            recursive = watcher.get("recursive", False)

            observer.schedule(handler, resolved_path, recursive)
            LOG.info(
                f"Observer scheduled {handler} for path '{path}' "
                f"in {'recursive' if recursive else 'non-recursive'} mode."
            )

    observer.start()
    LOG.info("Observer started...")
    try:
        i = 0
        while True:
            time.sleep(1)
            i += 1
            if i / HEARTBEAT_RATE == 1.0:
                LOG.info("Main event loop still running.")
                i = 1
    finally:
        LOG.info("Observer stopped...")
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
