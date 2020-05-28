import logging

from celery import shared_task
from django.apps import apps
from django.db import transaction

from joeflow.conf import settings
from joeflow.contrib.reversion import with_reversion

from .. import locking, utils

logger = logging.getLogger(__name__)


__all__ = ["task_runner"]


@shared_task(bind=True, ignore_results=True, max_retries=None)
def _celery_task_runner(self, task_pk, process_pk):
    with locking.lock(process_pk) as lock_result:
        countdown = utils.backoff(self.request.retries)
        if not lock_result:
            logger.info("Process is locked, retrying in %s seconds", countdown)
            self.retry(countdown=countdown)
        Task = apps.get_model("joeflow", "Task")
        task = Task.objects.get(pk=task_pk, completed=None)
        process = task.process

        try:
            logger.info("Executing %r", task)
            node = getattr(type(process), task.name)
            with_task = getattr(node, "with_task", False)
            kwargs = {}
            if with_task:
                kwargs["task"] = task
            with with_reversion(task):
                result = node(process, **kwargs)
        except:  # NoQA
            task.fail()
            logger.exception("Execution of %r failed", task)
        else:
            if result is False:
                logger.info("Task returned False, retrying in %s seconds", countdown)
                transaction.on_commit(lambda: self.retry(countdown=countdown))
                return
            elif result is True:
                result = None
            logger.info("Task completed successful, starting next tasks: %s", result)
            task.start_next_tasks(next_nodes=result)
            task.finish()


def task_runner(*, task_pk, process_pk, countdown, eta):
    """Schedule asynchronous machine task using celery."""
    _celery_task_runner.apply_async(
        args=(task_pk, process_pk),
        countdown=countdown,
        eta=eta,
        queue=settings.JOEFLOW_CELERY_QUEUE_NAME,
    )
