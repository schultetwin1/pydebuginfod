import bison
import logging
import os
from pathlib import Path
import requests
import shutil
import sys
import tempfile
from urllib.parse import urljoin, quote
import xdg

DEFAULT_SYMBOL_SERVER_URL = "https://debuginfod.elfutils.org/"
scheme = bison.Scheme(
    bison.Option("cache-path", field_type=str, default=os.path.join(str(xdg.xdg_cache_home()), 'debuginfod')),
    bison.Option('verbose', field_type=bool, default=False),
    bison.Option('timeout', field_type=int, default=90),
    bison.Option('progress', field_type=bool, default=True),
    bison.ListOption('urls', default=[DEFAULT_SYMBOL_SERVER_URL])
)


class Client:
    def __init__(self) -> None:
        config = read_config()

        self.verbose = config.get('veborse')
        self.timeout = config.get('timeout')
        if self.timeout == 0:
            self.timeout = None
        self.progress = config.get('progress')
        self.cache = config.get('cache-path')
        self.urls = config.get('urls')

        try:
            if not os.path.isdir(self.cache):
                os.makedirs(self.cache)
        except OSError:
            pass

    def clear_cache(self):
        """ Removes all files in the cache """
        shutil.rmtree(self.cache)

    def _download_file(self, url, destination):
        logging.info("Downloading {0} to {1}".format(url, destination))

        # Download to a temporary file first
        temp = tempfile.NamedTemporaryFile()

        response = requests.get(url, stream=True, timeout=self.timeout)
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
            if self.progress:
                sys.stdout.write(
                    '\r[debuginfod] Downloading... {} bytes'
                    .format(_sizeof_fmt(bytes_downloaded))
                )
                sys.stdout.flush()
        if self.progress:
            sys.stdout.write("\n")
        temp.flush()

        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy(temp.name, str(destination))

        return str(destination)

    def _get_key(self, build_id, type):
        build_id = build_id.lower()
        # Check cache
        cache_key = os.path.join("buildid", build_id, type)
        cached_file = os.path.join(self.cache, cache_key)
        if os.path.exists(cached_file):
            logging.info("Found {0} in cache".format(cache_key))
            return cached_file

        # File not cached, attempt to download for server
        url_key = f"buildid/{build_id}/{type}"

        for server in self.urls:
            url = urljoin(server, quote(url_key))
            dest_file = self._download_file(url, cached_file)
            if dest_file is not None:
                return dest_file
        return None

    def get_debuginfo(self, build_id):
        return self._get_key(build_id, "debuginfo")

    def get_executable(self, build_id):
        return self._get_key(build_id, "executable")


def read_config():
    config = bison.Bison(scheme)
    config.config_name = 'pydebuginfod'
    config.add_config_paths(
        '.',
        str(xdg.xdg_config_home())
    )
    config.env_prefix = "DEBUGINFOD"
    config.auto_env = True
    config.parse(False)
    return config


def _sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
