# Monokel
Monokel sits on top of [Watchdog](https://pythonhosted.org/watchdog/) and exposes an easy way on how to register filesystem event handlers that will eventually run inside a [Docker](https://www.docker.com/) container.

## Install

Install and update using [pip](https://pip.pypa.io/en/stable/getting-started/):

```
$ pip install -U monokel
```

## Getting Started

### The build step
To run an event loop that observes filesystem events from within the container we have to configure and build the actual docker-compose file first.

Monokel provides a build script that will do most of that for you and creates everything the resulting compose file needs to set up the final service. 

```
$ monokel build --help
```

The script itself can be used without requiring any dependencies. There are several components you can optionally provide and a mandatory one - the python file we call **_the config_**.

### The (python) config
The idea of **_the config_** is to provide a single entry point as a file for the event loop that will eventually run within the docker container. It defines what [Observer](https://pythonhosted.org/watchdog/api.html#module-watchdog.observers) to run and which [EventHandlers](https://pythonhosted.org/watchdog/api.html#module-watchdog.events) to schedule for given paths. 

As your eventhandlers might become very specific and require external packages it is by intention that you can make use of them from within the config as long as they can be found in PYPI and installed via pip. See [config requirements](https://github.com/rkoschmitzky/monokel/blob/main/README.md#the-config-requirements).

The config file itself can have any name as you can provide the location to the script path.

### The config requirements
TBC...
