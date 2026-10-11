import warnings

import django
import dramatiq
from django.apps import apps
from django.db import OperationalError, transaction

from ..conf import settings
from .base import execute, finish


def task_runner(*, task_pk, workflow_pk, countdown=None, eta=None, retries=0):
    """Schedule asynchronous machine task using dramatiq."""
    if django.VERSION >= (6, 0):
        warnings.warn(
            "The Dramatiq task runner is deprecated in favor of Django's task "
            "framework. Deletion is scheduled with the expiration of Django "
            "5.2 LTS version support.",
            PendingDeprecationWarning,
            stacklevel=2,
        )
    _dramatiq_task_runner.send_with_options(
        args=(task_pk, workflow_pk),
        delay=countdown,
        retries=retries,
    )


class RetryError(dramatiq.errors.Retry):
    """Raised to retry a task if the task result is ``False``."""

    pass


@dramatiq.actor(
    queue_name=settings.JOEFLOW_TASK_QUEUE_NAME,
    retry_when=lambda a, b: isinstance(b, (OperationalError, RetryError)),
)
def _dramatiq_task_runner(task_pk, workflow_pk, retries=0):
    Task = apps.get_model("joeflow", "Task")
    with transaction.atomic():
        task = (
            Task.objects.filter(pk=task_pk, completed=None)
            .select_for_update(nowait=True)
            .get()
        )

        workflow = (
            task.content_type.model_class()
            .objects.filter(pk=workflow_pk)
            .select_for_update(nowait=True)
            .get()
        )

        executed, result = execute(workflow, task)
        if not executed:
            return
        if result is False:
            _dramatiq_task_runner.logger.info("%r returned False, retrying …", task)
            raise RetryError("Task returned False, retrying …")
        finish(task, result)
