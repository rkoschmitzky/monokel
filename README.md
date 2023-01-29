# Monokel
A simple but flexible observer pipeline for filesystem events from within a docker container.

Monokel sits on top of [Watchdog](https://pythonhosted.org/watchdog/) and exposes an easy way how to register filesystem event handlers that will run inside a [Docker](https://www.docker.com/) container.

## Getting Started

### The build step
Monokel provides a build script that creates everything the resulting docker compose file needs to set up the final service. The buildscript itself can be used without requiring any depdendencies. There are several components you can optionally provide and a mandatory python file we can call the "config".

### The (python) config
The idea of the config file is to provide a single entry point that defines what [Observer](https://pythonhosted.org/watchdog/api.html#module-watchdog.observers) you want to run and which [eventhandlers](https://pythonhosted.org/watchdog/api.html#module-watchdog.events) you want to schedule for given paths. 
As your eventhandlers might become complex you can use other packages easily as long as they can be installed via pip.

### The config requirements
TBC...
