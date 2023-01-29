"""
Monokel's main event loop.

This sets up the watchdog observer and schedules all handlers for the configured paths.
"""

import logging
import os
import re
import time

LOG = logging.getLogger("monokel.run")

HEARTBEAT_RATE = 30


def _validate_config():
    from watchdog.observers.api import BaseObserver

    observer = CONFIG.get("observer")
    if not observer:
        raise KeyError(
            "'observer' entry missing in config.CONFIG or having no value."
        )
    if not isinstance(observer, BaseObserver):
        raise ValueError(
            "'observer entry value is not of type watchdog.observers.api.BaseObserver."
        )

    watchers = CONFIG.get("watchers")
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


def resolve_path(path, volumes_mapping):
    # type: (str, dict) -> str
    """ get the resolved path for the volume

    Args:
        path (str): path to resolve
        volumes_mapping (dict): the mappings required for lookup

    Returns:
        str: the resolved path
    """

    if not os.getenv("CONTAINER"):
        return path
    else:
        LOG.info("Detected in-container run...")
        return volumes_mapping[path]


if __name__ == "__main__":
    """ Start the event loop...
    
    Load configuration (all required dependencies within it have to be installed via 
    requirements.txt), identify the volume mappings and register the associated 
    eventhandlers with the mapped paths.
    """
    volume_mappings = _get_volume_mappings()
    # TODO: monkey-patch watchdogs FilesystemEvent
    #  to refer back to the unmounted path

    from config import CONFIG

    _validate_config()

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
