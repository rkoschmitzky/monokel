"""
This presents an example of Monokel's config file.

As it is Python you can use any site-package as long as this is
available via pip and will be passes in the requirements file.

Monokel sits on top of watchdog (https://pythonhosted.org/watchdog/).
Please use this reference on how to create your own event handlers.
"""


import logging

from watchdog.events import LoggingEventHandler
from watchdog.observers import Observer


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# a CONFIG dict instance is required
CONFIG = {
    # an Observer instance is required
    "observer": Observer(),
    # a list with multiple watcher specification's ad dict
    "watchers": [
        {
            # multiple paths can be associated with the same handler
            "paths": ["/temp", "/foo"],
            # recursive watch is optional and defaults to `False`
            "recursive": True,
            # the
            "handler": LoggingEventHandler(),
        },
    ]
}
