import logging

from watchdog.events import LoggingEventHandler

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

CONFIG = {
    "watchers": [
        {
            "paths": ["/temp", "/foo"],
            "handler": LoggingEventHandler()
        },
    ]
}