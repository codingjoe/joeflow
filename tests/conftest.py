import os
import pathlib

import pytest


@pytest.fixture()
def testdir():
    return pathlib.Path(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def fixturedir(testdir):
    return testdir / "fixtures"


@pytest.fixture()
def stub_worker():
    """Execute machine tasks with the in-memory task backend."""
    from tests.testapp import backends

    yield backends.TestWorker
    backends.get_backend().clear()
