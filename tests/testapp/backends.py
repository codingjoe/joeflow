"""An in-memory task backend for the test suite."""

from django.tasks import TaskResult, TaskResultStatus, task_backends
from django.tasks.backends.base import BaseTaskBackend
from django.tasks.exceptions import TaskResultDoesNotExist
from django.utils import timezone
from django.utils.crypto import get_random_string


def get_backend():
    """Return the test task backend."""
    return task_backends["default"]


class InMemoryBackend(BaseTaskBackend):
    """Store tasks in memory and execute them on demand."""

    supports_defer = True
    supports_get_result = True
    supports_priority = True

    def __init__(self, alias, params):
        super().__init__(alias, params)
        self.results = []

    def enqueue(self, task, args, kwargs):
        self.validate_task(task)
        result = TaskResult(
            task=task,
            id=get_random_string(32),
            status=TaskResultStatus.READY,
            enqueued_at=timezone.now(),
            started_at=None,
            last_attempted_at=None,
            finished_at=None,
            args=args,
            kwargs=kwargs,
            backend=self.alias,
            errors=[],
            worker_ids=[],
        )
        self.results.append(result)
        return result

    def get_result(self, result_id):
        for result in self.results:
            if result.id == result_id:
                return result
        raise TaskResultDoesNotExist(result_id)

    def clear(self):
        """Forget all task results."""
        self.results.clear()

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
        result.worker_ids.append("pytest")
        try:
            return_value = result.task.call(*result.args, **result.kwargs)
        except BaseException:
            object.__setattr__(result, "status", TaskResultStatus.FAILED)
            raise
        else:
            object.__setattr__(result, "_return_value", return_value)
            object.__setattr__(result, "status", TaskResultStatus.SUCCESSFUL)
        finally:
            object.__setattr__(result, "finished_at", timezone.now())


class TestWorker:
    """Execute pending machine tasks."""

    @staticmethod
    def wait():
        """Execute all pending tasks, including tasks that have been retried."""
        get_backend().drain()
