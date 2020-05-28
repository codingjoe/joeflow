import logging

import dramatiq
from django.apps import apps
from django.db import OperationalError, transaction

from .. import locking, utils
from ..conf import settings
from ..contrib.reversion import with_reversion

logger = logging.getLogger(__name__)


def task_runner(*, task_pk, process_pk, countdown=None, eta=None, retries=0):
    """Schedule asynchronous machine task using celery."""
    _dramatiq_task_runner.send_with_options(
        args=(task_pk, process_pk), delay=countdown, retries=retries,
    )


@dramatiq.actor(
    queue_name=settings.JOEFLOW_CELERY_QUEUE_NAME,
    retry_when=lambda a, b: isinstance(b, OperationalError),
)
def _dramatiq_task_runner(task_pk, process_pk, retries=0):
    with locking.lock(process_pk) as lock_result:
        countdown = utils.backoff(retries)
        if not lock_result:
            logger.info("Process is locked, retrying in %s seconds", countdown)
            task_runner(
                task_pk=task_pk,
                process_pk=process_pk,
                countdown=countdown,
                retries=retries + 1,
            )
            return
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
                transaction.on_commit(
                    lambda: task_runner(
                        task_pk=task_pk,
                        process_pk=process_pk,
                        countdown=countdown,
                        retries=retries + 1,
                    )
                )
                return
            elif result is True:
                result = None
            logger.info("Task completed successful, starting next tasks: %s", result)
            task.start_next_tasks(next_nodes=result)
            task.finish()
