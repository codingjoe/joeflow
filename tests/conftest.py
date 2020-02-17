import os
import pathlib
from contextlib import contextmanager
from unittest import mock

import pytest
import redis


@pytest.fixture()
def testdir():
    return pathlib.Path(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def fixturedir(testdir):
    return testdir / 'fixtures'


@pytest.fixture(params=["joeflow.runner.dramatiq.task_runner", "joeflow.runner.celery.task_runner"])
def _runner(request, monkeypatch, settings):
    settings.JOEFLOW_TASK_RUNNER = request.param
    if request.param == "joeflow.runner.dramatiq.task_runner":
        try:
            import dramatiq  # NoQA
        except ImportError:
            pytest.skip("Dramatiq is not installed")
    if request.param == "joeflow.runner.celery.task_runner":
        try:

            from celery import shared_task  # NoQA
        except ImportError:
            pytest.skip("Celery is not installed")


@pytest.fixture()
def stub_worker(monkeypatch, settings, _runner):
    if settings.JOEFLOW_TASK_RUNNER == "joeflow.runner.celery.task_runner":
        settings.CELERY_TASK_ALWAYS_EAGER = True

        @contextmanager
        def _fake_lock(key):
            yield True
        monkeypatch.setattr('joeflow.locking.lock', _fake_lock)
        yield mock.Mock()
    else:
        with redis.Redis.from_url(settings.JOEFLOW_REDIS_LOCK_URL) as connection:
            connection.flushdb()
        import dramatiq

        broker = dramatiq.get_broker()
        broker.emit_after("process_boot")
        broker.flush_all()
        worker = dramatiq.Worker(broker, worker_timeout=100)
        worker.start()

        class Meta:
            @staticmethod
            def wait():
                broker.join(settings.JOEFLOW_CELERY_QUEUE_NAME, timeout=10000)
                worker.join()

        yield Meta
        worker.stop()
