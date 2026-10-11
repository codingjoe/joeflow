"""Run machine tasks with Django's Tasks framework.

Machine tasks are executed asynchronously using `Django Tasks`_. A task
backend must be configured with the ``TASKS`` setting, see the Django
documentation for details.

.. _Django Tasks: https://docs.djangoproject.com/en/stable/topics/tasks/
"""

import logging
from contextlib import contextmanager
from datetime import timedelta

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError, transaction
from django.utils import timezone

try:  # Django >= 6.0
    from django.tasks import exceptions, task
except ImportError as e:  # Django < 6.0
    raise ImproperlyConfigured(
        "The 'joeflow.runner.django_tasks' task runner requires Django 6.0 or "
        "later. Use the deprecated Celery or Dramatiq task runner instead."
    ) from e

from ..conf import settings
from .base import execute, finish

logger = logging.getLogger(__name__)

__all__ = ["task_runner"]

_RETRY_DELAY = 60
"""Time in seconds to wait before a machine task is re-enqueued."""


class RetryError(Exception):
    """Signal that a machine task is not ready and has to be executed again."""


def _get_run_after(countdown=None, eta=None):
    """Return the earliest point in time a task should be executed at."""
    if eta is not None:
        return eta
    if countdown:
        return timezone.now() + timedelta(seconds=countdown)
    return None


@contextmanager
def _retry_on_failure(task, *args, **kwargs):
    """Re-enqueue a task if the wrapped code block fails.

    Machine tasks are locked to prevent race conditions. If the lock cannot
    be acquired or a task is not ready to continue yet, the task has to be
    executed again at a later point. Django's Tasks framework has no built-in
    retry mechanism, so the task is re-enqueued once the current transaction
    has been committed.

    A task backend with support for deferred execution is required. The
    failure is raised otherwise, so the task is not re-enqueued.

    Args:
        task (django.tasks.Task): The task that is re-enqueued on failure.
        *args: Positional arguments the task is called with.
        **kwargs: Keyword arguments the task is called with.

    """
    try:
        yield
    except (OperationalError, RetryError) as e:
        backend = task.get_backend()
        if not backend.supports_defer:
            logger.error(
                "%r must be executed again, but the %r task backend does not "
                "support deferred execution. The task is not re-enqueued: %s",
                task.name,
                backend.alias,
                e,
            )
            raise
        run_after = _get_run_after(countdown=_RETRY_DELAY)
        logger.warning("Re-enqueueing task %s%r: %s", task.name, args, e)
        transaction.on_commit(
            lambda: task.using(run_after=run_after).enqueue(*args, **kwargs)
        )


def _machine_task(task_pk, workflow_pk):
    """Execute a single machine task."""
    Task = apps.get_model("joeflow", "Task")
    with _retry_on_failure(_machine_task, task_pk=task_pk, workflow_pk=workflow_pk):
        with transaction.atomic():
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
                raise RetryError(f"{task} is not ready to continue yet.")
            finish(task, result)


def _create_machine_task():
    """Create the machine task for the configured task queue."""
    try:
        return task(queue_name=settings.JOEFLOW_TASK_QUEUE_NAME)(_machine_task)
    except exceptions.InvalidTask as e:
        raise ImproperlyConfigured(
            f"The {settings.JOEFLOW_TASK_QUEUE_NAME!r} queue is not configured in "
            "the 'TASKS' setting. Add it to the 'QUEUES' of the used task backend "
            "or set JOEFLOW_TASK_RUNNER to use a deprecated task runner."
        ) from e


_machine_task = _create_machine_task()


def task_runner(*, task_pk, workflow_pk, countdown=None, eta=None):
    """Schedule an asynchronous machine task.

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
