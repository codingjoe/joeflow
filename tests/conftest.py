import os
import pathlib
from unittest import mock

import pytest


@pytest.fixture()
def testdir():
    return pathlib.Path(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def fixturedir(testdir):
    return testdir / "fixtures"


@pytest.fixture(
    params=[
        "joeflow.runner.django_tasks.task_runner",
        "joeflow.runner.dramatiq.task_runner",
        "joeflow.runner.celery.task_runner",
    ]
)
def _runner(request, settings):
    runner = request.param
    if runner == "joeflow.runner.django_tasks.task_runner":
        try:
            import django.tasks  # NoQA
        except ImportError:
            pytest.skip("Django < 6.0 does not ship the Tasks framework.")
    if runner == "joeflow.runner.dramatiq.task_runner":
        pytest.importorskip("dramatiq")
    if runner == "joeflow.runner.celery.task_runner":
        pytest.importorskip("celery")
    settings.JOEFLOW_TASK_RUNNER = runner


@pytest.fixture()
def stub_worker(settings, _runner):
    if settings.JOEFLOW_TASK_RUNNER == "joeflow.runner.django_tasks.task_runner":
        from tests.testapp import backends

        yield backends.TestWorker
        backends.get_backend().clear()
    elif settings.JOEFLOW_TASK_RUNNER == "joeflow.runner.celery.task_runner":
        yield mock.Mock()
    else:
        import dramatiq

        broker = dramatiq.get_broker()
        broker.emit_after("process_boot")
        broker.flush_all()
        worker = dramatiq.Worker(broker, worker_timeout=100, worker_threads=1)
        worker.start()

        class Meta:
            @staticmethod
            def wait():
                broker.join(
                    settings.JOEFLOW_TASK_QUEUE_NAME, timeout=60000, fail_fast=False
                )
                worker.join()

        yield Meta
        worker.stop()


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    """Serve all Redis traffic from an in-process fake server."""
    import fakeredis
    import redis

    server = fakeredis.FakeServer()

    class FakeRedis(fakeredis.FakeStrictRedis):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("server", server)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(redis, "Redis", FakeRedis)
    monkeypatch.setattr(redis, "StrictRedis", FakeRedis)


collect_ignore = []
try:
    import django.tasks  # NoQA
except ImportError:
    # Django < 6.0 does not ship the Tasks framework.
    collect_ignore.append("test_runner.py")
