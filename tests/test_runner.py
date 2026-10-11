"""Tests for the Django Tasks task runner."""

import logging
from datetime import timedelta
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError
from django.utils import timezone
from joeflow.models import Task
from joeflow.runner import django_tasks
from joeflow.typing import MACHINE

from tests.testapp import backends, workflows


class TestGetRunAfter:
    def test_no_delay(self):
        assert django_tasks._get_run_after() is None

    def test_countdown(self):
        now = timezone.now()
        run_after = django_tasks._get_run_after(countdown=60)
        assert now + timedelta(seconds=59) < run_after < now + timedelta(seconds=61)


class TestTaskRunner:
    def test_enqueue(self, monkeypatch):
        task = mock.Mock()
        monkeypatch.setattr(django_tasks, "_machine_task", task)
        result = django_tasks.task_runner(task_pk=1, workflow_pk=2)
        task.using.assert_called_once_with(run_after=None)
        assert result is task.using.return_value.enqueue.return_value

    def test_deferred(self, monkeypatch):
        task = mock.Mock()
        monkeypatch.setattr(django_tasks, "_machine_task", task)
        django_tasks.task_runner(task_pk=1, workflow_pk=2, countdown=60)
        run_after = task.using.call_args.kwargs["run_after"]
        assert run_after > timezone.now()
        task.using.return_value.enqueue.assert_called_once_with(
            task_pk=1, workflow_pk=2
        )

    def test_eta(self, monkeypatch):
        task = mock.Mock()
        monkeypatch.setattr(django_tasks, "_machine_task", task)
        eta = timezone.now() + timedelta(hours=1)
        django_tasks.task_runner(task_pk=1, workflow_pk=2, eta=eta)
        assert task.using.call_args.kwargs["run_after"] == eta


class TestRetryOnFailure:
    @pytest.fixture()
    def task(self):
        task = mock.Mock()
        task.get_backend.return_value.supports_defer = True
        return task

    def test_no_failure(self, task):
        with django_tasks._retry_on_failure(task, 1, 2):
            pass
        task.using.assert_not_called()

    def test_retry(self, task, monkeypatch, db, django_capture_on_commit_callbacks):
        monkeypatch.setattr(django_tasks, "_RETRY_DELAY", 42)
        now = timezone.now()
        with django_capture_on_commit_callbacks(execute=True) as callbacks:
            with django_tasks._retry_on_failure(task, 1, 2):
                raise OperationalError("database is locked")
        assert len(callbacks) == 1
        run_after = task.using.call_args.kwargs["run_after"]
        assert now + timedelta(seconds=41) < run_after < now + timedelta(seconds=43)
        task.using.return_value.enqueue.assert_called_once_with(1, 2)

    def test_retry__retry_error(self, task, db, django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True):
            with django_tasks._retry_on_failure(task, task_pk=1):
                raise django_tasks.RetryError("not ready")
        task.using.return_value.enqueue.assert_called_once_with(task_pk=1)

    def test_retry__immediately(
        self, task, monkeypatch, db, django_capture_on_commit_callbacks
    ):
        monkeypatch.setattr(django_tasks, "_RETRY_DELAY", 0)
        with django_capture_on_commit_callbacks(execute=True):
            with django_tasks._retry_on_failure(task, 1, 2):
                raise OperationalError("database is locked")
        task.using.assert_called_once_with(run_after=None)

    def test_retry__without_defer_support(self, task, caplog):
        task.get_backend.return_value.supports_defer = False
        with caplog.at_level(logging.ERROR), pytest.raises(OperationalError):
            with django_tasks._retry_on_failure(task, 1, 2):
                raise OperationalError("database is locked")
        task.using.assert_not_called()
        assert "does not support deferred execution" in caplog.text


class TestMachineTask:
    @pytest.fixture()
    def worker(self, stub_worker, transactional_db):
        """Execute machine tasks with the in-memory task backend."""
        yield stub_worker

    def test_locked(self, monkeypatch, worker):
        """A machine task is re-enqueued if the task cannot be locked."""
        monkeypatch.setattr(django_tasks, "_RETRY_DELAY", 0)
        monkeypatch.setattr(
            Task.objects,
            "select_for_update",
            mock.Mock(side_effect=OperationalError("database is locked")),
        )
        assert django_tasks._machine_task.func(task_pk=1, workflow_pk=2) is None
        results = backends.get_backend().results
        assert len(results) == 1
        assert results[0].status == backends.TaskResultStatus.READY
        assert results[0].kwargs == {"task_pk": 1, "workflow_pk": 2}

    def test_task_does_not_exist(self, worker):
        assert django_tasks._machine_task.func(task_pk=1, workflow_pk=2) is None
        assert backends.get_backend().results == []

    def test_retry__machine_task(self, monkeypatch, worker):
        """A machine task that returns False is re-enqueued until it succeeds."""
        monkeypatch.setattr(django_tasks, "_RETRY_DELAY", 0)
        attempts = 0

        def waiting(self, task):
            nonlocal attempts
            attempts += 1
            return attempts > 1

        waiting.name = "wait"
        waiting.type = MACHINE
        waiting.with_task = True
        monkeypatch.setattr(workflows.WaitWorkflow, "wait", waiting)
        workflow = workflows.WaitWorkflow.start()
        worker.wait()
        assert attempts == 2
        assert workflow.task_set.get(name="wait").status == Task.SUCCEEDED

    def test_retry__deferred(self, monkeypatch, worker):
        """A machine task that keeps returning False is re-enqueued later."""
        monkeypatch.setattr(django_tasks, "_RETRY_DELAY", 3600)
        workflow = workflows.WaitWorkflow.start()
        worker.wait()
        assert workflow.task_set.get(name="wait").status == Task.SCHEDULED
        retries = [
            result
            for result in backends.get_backend().results
            if result.status == backends.TaskResultStatus.READY
        ]
        assert len(retries) == 1
        assert retries[0].task.run_after > timezone.now() + timedelta(minutes=59)


class TestImproperlyConfigured:
    def test_queue_not_configured(self, settings):
        settings.JOEFLOW_TASK_QUEUE_NAME = "not-the-joeflow-queue"
        with pytest.raises(ImproperlyConfigured, match="is not configured"):
            django_tasks._create_machine_task()
