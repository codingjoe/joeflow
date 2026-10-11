import logging
import warnings

import django
from celery import shared_task
from django.apps import apps
from django.db import OperationalError, transaction

from joeflow.conf import settings
from joeflow.runner.base import execute, finish

logger = logging.getLogger(__name__)


__all__ = ["task_runner"]


@shared_task(
    bind=True,
    ignore_results=True,
    max_retries=None,
    autoretry_for=(OperationalError,),
    retry_backoff=True,
)
def _celery_task_runner(self, task_pk, workflow_pk):
    Task = apps.get_model("joeflow", "Task")
    with transaction.atomic():
        task = Task.objects.select_for_update().get(pk=task_pk, completed=None)
        workflow = (
            task.content_type.model_class()
            .objects.select_for_update(nowait=True)
            .get(pk=workflow_pk)
        )

        executed, result = execute(workflow, task)
        if not executed:
            return
        if result is False:
            logger.info("Task returned False, retrying …")
            transaction.on_commit(lambda: self.retry())
            return
        finish(task, result)


def task_runner(*, task_pk, workflow_pk, countdown=None, eta=None):
    """Schedule an asynchronous machine task with Celery.

    Deprecated in favor of Django's task framework.
    """
    if django.VERSION >= (6, 0):
        warnings.warn(
            "The Celery task runner is deprecated in favor of Django's task "
            "framework. Deletion is scheduled with the expiration of Django "
            "5.2 LTS version support.",
            PendingDeprecationWarning,
            stacklevel=2,
        )
    _celery_task_runner.apply_async(
        args=(task_pk, workflow_pk),
        countdown=countdown,
        eta=eta,
        queue=settings.JOEFLOW_TASK_QUEUE_NAME,
    )
