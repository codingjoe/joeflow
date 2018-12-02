import os
import pathlib
from contextlib import contextmanager

import pytest


@pytest.fixture()
def testdir():
    return pathlib.Path(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def fixturedir(testdir):
    return testdir / 'fixtures'


@pytest.fixture(autouse=True)
def instant_commit(monkeypatch):
    def on_commit(f):
        f()

    monkeypatch.setattr('django.db.transaction.on_commit', on_commit)


@pytest.fixture()
def no_on_commit(instant_commit, monkeypatch):
    def on_commit(f):
        pass

    monkeypatch.setattr('django.db.transaction.on_commit', on_commit)


@pytest.yield_fixture(autouse=True)
def fake_lock(monkeypatch):
    @contextmanager
    def _fake_lock(key):
        yield True

    monkeypatch.setattr('joeflow.locking.lock', _fake_lock)


@pytest.fixture(autouse=True)
def always_eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
