import logging
import os
from pathlib import Path
import requests
import shutil
import sys
import tempfile
from urllib.parse import urljoin, quote
import xdg

verbose = os.getenv("DEBUGINFOD_VERBOSE") is not None
if verbose:
    logging.getLogger().setLevel(logging.DEBUG)


def _sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def _download_file(url, destination):
    logging.info("Downloading {0} to {1}".format(url, destination))

    # Download to a temporary file first
    temp = tempfile.NamedTemporaryFile()

    response = requests.get(url, stream=True, timeout=timeout())
    if response.status_code != 200:
        if response.status_code == 404:
            logging.info("{0} not found".format(url))
            return None
        else:
            raise RuntimeError(
                f'Request to {url} returned status code {response.status_code}'
            )

    bytes_downloaded = 0

    for data in response.iter_content(chunk_size=None):
        temp.write(data)
        bytes_downloaded += len(data)
        sys.stdout.write(
            '\r[debuginfod] Downloading... {} bytes'
            .format(_sizeof_fmt(bytes_downloaded))
        )
        sys.stdout.flush()
    sys.stdout.write("\n")
    temp.flush()

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy(temp.name, str(destination))

    return str(destination)


def _get_key(build_id, type):
    build_id = build_id.lower()
    # Check cache
    cache_key = os.path.join("buildid", build_id, type)
    cached_file = os.path.join(cache_dir(), cache_key)
    if os.path.exists(cached_file):
        logging.info("Found {0} in cache".format(cache_key))
        return cached_file

    # File not cached, attempt to download for server
    url_key = f"buildid/{build_id}/{type}"

    for server in servers():
        url = urljoin(server, quote(url_key))
        dest_file = _download_file(url, cached_file)
        if dest_file is not None:
            return dest_file
    return None


def cache_dir():
    # Default cache of symbol files is:
    # ~/.cache/debuginfod/.build-id
    env_cache_dir = os.getenv("DEBUGINFOD_CACHE_PATH")
    if env_cache_dir is not None:
        return env_cache_dir
    else:
        return os.path.join(str(xdg.xdg_cache_home()), 'debuginfod')


def servers():
    DEFAULT_SYMBOL_SERVER_URL = "https://debuginfod.elfutils.org/"

    env = os.getenv('DEBUGINFOD_URLS')
    if env:
        return env.split()
    else:
        return [DEFAULT_SYMBOL_SERVER_URL]


def timeout():
    env_timeout_secs = os.getenv("DEBUGINFOD_TIMEOUT")
    return 90 if env_timeout_secs is None else int(env_timeout_secs)


def get_debuginfo(build_id):
    return _get_key(build_id, "debuginfo")


def get_executable(build_id):
    return _get_key(build_id, "executable")


def clear_cache():
    shutil.rmtree(cache_dir())


# Create our cache dir.
try:
    if not os.path.isdir(cache_dir()):
        os.makedirs(cache_dir())
except OSError:
    pass
