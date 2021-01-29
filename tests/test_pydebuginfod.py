import os
import pydebuginfod


def test_version():
    assert pydebuginfod.__version__ == '0.0.1'


def test_download_ls():
    client = pydebuginfod.Client()
    buildid = "c0e8c127f1f36dd10e77331f46b6e2dbbbdb219b"
    client.clear_cache()
    cached_path = client.get_debuginfo(buildid)
    expected_path = os.path.join(
        client.cache,
        'buildid',
        buildid,
        'debuginfo')
    assert cached_path == expected_path
