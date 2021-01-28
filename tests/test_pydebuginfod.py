import os
import pydebuginfod


def test_version():
    assert pydebuginfod.__version__ == '0.0.1'


def test_download_ls():
    pydebuginfod.clear_cache()
    buildid = "c0e8c127f1f36dd10e77331f46b6e2dbbbdb219b"
    cached_path = pydebuginfod.get_debuginfo(buildid)
    expected_path = os.path.join(
        pydebuginfod.cache_dir(),
        'buildid',
        buildid,
        'debuginfo')
    assert cached_path == expected_path
