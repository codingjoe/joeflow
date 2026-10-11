"""
Execute machine tasks with Django's task framework.

A task backend must be configured with the ``TASKS`` setting.
"""

import logging
from contextlib import contextmanager
from datetime import timedelta

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError, transaction
from django.tasks import exceptions, task
from django.utils import timezone

from ..conf import settings
from .base import execute, finish

logger = logging.getLogger(__name__)

__all__ = ["task_runner"]

_RETRY_DELAY = 60
"""Time in seconds to wait before a machine task is re-enqueued."""


class RetryError(Exception):
    """Raised to re-enqueue a machine task that is not ready to continue."""


def _get_run_after(countdown=None, eta=None):
    """
    Return the point in time a machine task should start.

    An ``eta`` takes precedence over a ``countdown``.
    """
    if eta is not None:
        return eta
    if countdown:
        return timezone.now() + timedelta(seconds=countdown)
    return None


@contextmanager
def _retry_on_failure(task, *args, **kwargs):
    """
    Re-enqueue a task if the wrapped code block fails.

    Machine tasks are locked to prevent race conditions. Django's task
    framework has no retry mechanism of its own, so a task that is locked or
    not ready to continue gets re-enqueued once the current transaction
    commits.

    A task backend without support for deferred execution cannot re-enqueue
    it, so the failure propagates instead.
    """
    try:
        yield
    except (OperationalError, RetryError) as e:
        backend = task.get_backend()
        if not backend.supports_defer:
            logger.exception(
                "%r must be executed again, but the %r task backend does not "
                "support deferred execution. The task is not re-enqueued.",
                task.name,
                backend.alias,
            )
            raise
        run_after = _get_run_after(countdown=_RETRY_DELAY)
        logger.warning("Re-enqueueing task %s%r: %s", task.name, args, str(e))
        transaction.on_commit(
            lambda: task.using(run_after=run_after).enqueue(*args, **kwargs)
        )


def _machine_task(task_pk, workflow_pk):
    """Run the scheduled node and continue the workflow."""
    Task = apps.get_model("joeflow", "Task")
    with (
        _retry_on_failure(_machine_task, task_pk=task_pk, workflow_pk=workflow_pk),
        transaction.atomic(),
    ):
        try:
            task = Task.objects.select_for_update().get(pk=task_pk, completed=None)
        except Task.DoesNotExist:
            logger.info(
                "Task %s does not exist or has already been completed.", task_pk
            )
            return

        workflow = (
            task.content_type.model_class()
            .objects.select_for_update(nowait=True)
            .get(pk=workflow_pk)
        )

        executed, result = execute(workflow, task)
        if not executed:
            return
        if result is False:
            msg = f"{task} is not ready to continue yet."
            raise RetryError(msg)
        finish(task, result)


def _create_machine_task():
    """Bind the runner to the queue named in the settings."""
    try:
        return task(queue_name=settings.JOEFLOW_TASK_QUEUE_NAME)(_machine_task)
    except exceptions.InvalidTask as e:
        msg = (
            f"The {settings.JOEFLOW_TASK_QUEUE_NAME!r} queue is not configured in "
            "the 'TASKS' setting. Add it to the 'QUEUES' of the used task backend."
        )
        raise ImproperlyConfigured(msg) from e


_machine_task = _create_machine_task()


def task_runner(*, task_pk, workflow_pk, countdown=None, eta=None):
    """
    Schedule an asynchronous machine task.

    Args:
        task_pk (int): Primary key of the task that should be executed.
        workflow_pk (int): Primary key of the workflow the task belongs to.
        countdown (int):
            Time in seconds until the task should be started.
        eta (datetime.datetime):
            Time at which the task should be started.

    Returns:
        django.tasks.TaskResult: The enqueued task result.

    """
    return _machine_task.using(
        run_after=_get_run_after(countdown=countdown, eta=eta)
    ).enqueue(task_pk=task_pk, workflow_pk=workflow_pk)
