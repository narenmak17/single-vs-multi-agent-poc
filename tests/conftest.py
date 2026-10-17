import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from app import create_app  # noqa: E402  (app/ is not a package)


@pytest.fixture
def client(tmp_path):
    return create_app(str(tmp_path / "test.db")).test_client()
