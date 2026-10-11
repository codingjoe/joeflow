"""An in-memory task backend for the test suite."""

from django.tasks import TaskResultStatus, task_backends
from django.tasks.backends.dummy import DummyBackend
from django.utils import timezone


def get_backend():
    """Return the test task backend."""
    return task_backends["default"]


class InMemoryBackend(DummyBackend):
    """Store tasks in memory and execute them on demand."""

    def drain(self):
        """Execute all tasks that are due."""
        for _ in range(100):
            now = timezone.now()
            due = [
                result
                for result in self.results
                if result.status == TaskResultStatus.READY
                and (result.task.run_after is None or result.task.run_after <= now)
            ]
            if not due:
                return
            for result in due:
                self._execute(result)
        raise RuntimeError("Too many tasks, is a task re-enqueueing itself forever?")

    def _execute(self, result):
        now = timezone.now()
        object.__setattr__(result, "status", TaskResultStatus.RUNNING)
        object.__setattr__(result, "started_at", now)
        object.__setattr__(result, "last_attempted_at", now)
        object.__setattr__(
            result, "_return_value", result.task.call(*result.args, **result.kwargs)
        )
        object.__setattr__(result, "status", TaskResultStatus.SUCCESSFUL)
        object.__setattr__(result, "finished_at", timezone.now())


class TestWorker:
    """Execute pending machine tasks."""

    @staticmethod
    def wait():
        """Execute all pending tasks, including tasks that have been retried."""
        get_backend().drain()
