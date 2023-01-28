"""
Monokel's main event loop.

This sets up the watchdog observer and schedules all handlers for the configured paths.
"""

import logging
import os
import time

from watchdog.observers.api import BaseObserver

from config import CONFIG


LOG = logging.getLogger("monokel.main")

HEARTBEAT_RATE = 30


def _validate_config():
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


def _setup_mounts():
    # type: () -> dict
    return {}


def resolve_path(path, mounts_mapping):
    # type: (str, dict) -> str

    if not os.getenv("CONTAINER"):
        return path
    else:
        return mounts_mapping[path]


if __name__ == "__main__":
    _validate_config()
    mounts_mapping = _setup_mounts()

    observer = CONFIG.get("observer")

    for watcher in CONFIG.get("watchers"):
        for path in watcher.get("paths"):
            handler = watcher.get("handler")
            path = resolve_path(path, mounts_mapping)
            recursive = watcher.get("recursive", False)

            observer.schedule(handler, path, recursive)
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
