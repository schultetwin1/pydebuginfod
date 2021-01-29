# pydebuginfod

pydebuginfod is a Python client implementation of the [debuginfod
spec](https://www.mankier.com/8/debuginfod).

![PyPI](https://img.shields.io/pypi/v/pydebuginfod)
![Build](https://github.com/schultetwin1/pydebuginfod/workflows/CI/badge.svg)

```python
import pydebuginfod

client = pydebuginfod.Client()
dbginfo = client.get_debuginfo("c0e8c127f1f36dd10e77331f46b6e2dbbbdb219b")
dbginfo
>>> '/home/matt/.cache/debuginfod/buildid/c0e8c127f1f36dd10e77331f46b6e2dbbbdb219b/debuginfo'

client = pydebuginfod.Client()
executable = client.get_executable("c0e8c127f1f36dd10e77331f46b6e2dbbbdb219b")
dbginfo
>>> '/home/matt/.cache/debuginfod/buildid/c0e8c127f1f36dd10e77331f46b6e2dbbbdb219b/executable'
```

pydebuginfod allows you to easily get started with debuginfod.

## Configurations

pydebuginfod allows configurations to passed in via:

* A configuration file
* ENV variables
* Member variables

Configurations are set in that order (config file < env vars < direct).

The following items can be configured:

* URLs: The URLs of the servers you are querying
* Cache-Path: The cache location to store the downloaded artifacts
* Verbose: Sets the logging level to verbose
* Timeout: How long to wait on a connection before giving up
* Progress: Show download progress via stdout during download?

### Configuration File

The configuraton file follows the
[XDG](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
specification. pydebuginfod will look for a file named `pydebuginfo.yml`
under the `XDG_CONFIG_HOME` directory.

The structure of the yaml file is as follows

```yml
cache-path: /opt/cache
verbose: false
timeout: 90
progress: true
urls:
    - "https://server1.com"
    - "https://server2/com"
```

### Environment Variables

* DEBUGINFOD_CACHE_PATH
* DEBUGINFOD_VERBOSE
* DEBUGINFOD_TIMEOUT
* DEBUGINFOD_PROGRESS
* DEBUGINFOD_URLS

### Member variables

```python
client = pydebuginfod.Client()
client.cache = "/opt/cache"
client.verbose = False
client.timeout = 90
client.progress = True
client.urls = ["https://server1.com"]
```