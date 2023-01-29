# Monokel
Monokel sits on top of [Watchdog](https://pythonhosted.org/watchdog/) and exposes an easy way on how to register filesystem event handlers that will eventually run inside a [Docker](https://www.docker.com/) container.

## Getting Started

### The build step
To run an event loop that listens from within a docker container we have to set up and build the actual docker-compose file first.

Monokel provides a build script that creates everything the resulting compose file needs to set up the final service. The script itself can be used without requiring any dependencies. There are several components you can optionally provide and a mandatory python file we call the "config".

### The (python) config
The idea of the config file is to provide a single entry point for the event loop that will eventually run within the docker container. It defines what [Observer](https://pythonhosted.org/watchdog/api.html#module-watchdog.observers) to run and which [eventhandlers](https://pythonhosted.org/watchdog/api.html#module-watchdog.events) to schedule for given paths. 

As your eventhandlers might become very specific and require external packages it is by intention that you can make use of them from within the config as long as they can be found in PYPI and installed via pip. See [config requirements](https://github.com/rkoschmitzky/monokel/blob/main/README.md#the-config-requirements).

The config file itself can have any name as you can provide the location to the script path.

### The config requirements
TBC...
