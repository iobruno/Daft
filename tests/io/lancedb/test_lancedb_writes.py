import sys

import pyarrow as pa
import pytest

import daft
from tests.integration.io.conftest import minio_create_bucket

TABLE_NAME = "my_table"
data = {
    "vector": [[1.1, 1.2], [0.2, 1.8]],
    "lat": [45.5, 40.1],
    "long": [-122.7, -74.1],
}

PYARROW_LE_8_0_0 = tuple(int(s) for s in pa.__version__.split(".") if s.isnumeric()) < (8, 0, 0)
PY_LE_3_9_0 = sys.version_info < (3, 9)
pytestmark = pytest.mark.skipif(
    PYARROW_LE_8_0_0 or PY_LE_3_9_0, reason="lance only supported if pyarrow >= 8.0.0 and python >= 3.9.0"
)


@pytest.fixture(scope="function")
def lance_dataset_path(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("lance")
    yield str(tmp_dir)


def test_lancedb_roundtrip(lance_dataset_path):
    df = daft.from_pydict(data)
    df.write_lance(lance_dataset_path)
    df = daft.read_lance(lance_dataset_path)
    assert df.to_pydict() == data


@pytest.mark.integration()
def test_lancedb_minio(minio_io_config):
    df = daft.from_pydict(data)
    bucket_name = "lance"
    s3_path = f"s3://{bucket_name}/data"
    with minio_create_bucket(minio_io_config=minio_io_config, bucket_name=bucket_name):
        df.write_lance(s3_path, io_config=minio_io_config)
        df = daft.read_lance(s3_path, io_config=minio_io_config)
        assert df.to_pydict() == data
