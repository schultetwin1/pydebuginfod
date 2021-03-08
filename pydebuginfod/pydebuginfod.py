import bison
import logging
import os
from pathlib import Path
import requests
import shutil
import sys
import tempfile
from urllib.parse import urljoin, quote
import toml
from appdirs import AppDirs
import boto3

symbols_dirs = AppDirs("symbols")
debuginfod_dirs = AppDirs("debuginfod")

DEFAULT_SYMBOL_SERVER_URL = "https://debuginfod.elfutils.org/"
scheme = bison.Scheme(
    bison.Option("cache-path", field_type=str, default=debuginfod_dirs.user_cache_dir),
    bison.Option('verbose', field_type=bool, default=False),
    bison.Option('timeout', field_type=int, default=90),
    bison.Option('progress', field_type=bool, default=True),
    bison.ListOption('urls', default=[DEFAULT_SYMBOL_SERVER_URL])
)


class Client:
    def __init__(self) -> None:
        config = read_config()
        symbols_config = read_symbols_config()

        self.verbose = config.get('veborse')
        self.timeout = config.get('timeout')
        if self.timeout == 0:
            self.timeout = None
        self.progress = config.get('progress')
        self.cache = config.get('cache-path')
        self.servers = symbols_config["servers"]
        urls = config.get('urls')
        for url in urls:
            self.servers.append({
                'access': 'read',
                'type': 'http',
                'url': url
            })

        try:
            if not os.path.isdir(self.cache):
                os.makedirs(self.cache)
        except OSError:
            pass

    def clear_cache(self):
        """ Removes all files in the cache """
        shutil.rmtree(self.cache)

    def _download_file(self, server, key, destination):
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if server['type'] == 'http':
            url = urljoin(server['url'], key)
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

            shutil.copy(temp.name, str(destination))

            return str(destination)

        elif server['type'] == 's3':
            s3 = boto3.client('s3')
            s3.download_file(server['bucket'], key, str(destination))
            return str(destination)
        else:
            return None

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

        for server in self.servers:
            dest_file = self._download_file(server, url_key, cached_file)
            if dest_file is not None:
                return dest_file
        return None

    def get_debuginfo(self, build_id):
        return self._get_key(build_id, "debuginfo")

    def get_executable(self, build_id):
        return self._get_key(build_id, "executable")


def read_symbols_config():
    config_file = Path(symbols_dirs.user_config_dir).joinpath("symbols.toml")
    symbols_config = toml.load(config_file)
    return symbols_config


def read_config():

    # Reads DEBUGINFOD config
    config = bison.Bison(scheme)
    config.config_name = 'pydebuginfod'
    config.add_config_paths(
        '.',
        debuginfod_dirs.user_config_dir
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
