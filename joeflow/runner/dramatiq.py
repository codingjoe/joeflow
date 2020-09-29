import logging

import dramatiq
from django.apps import apps
from django.db import OperationalError, transaction

from ..conf import settings
from ..contrib.reversion import with_reversion

logger = logging.getLogger(__name__)


def task_runner(*, task_pk, workflow_pk, countdown=None, eta=None, retries=0):
    """Schedule asynchronous machine task using celery."""
    _dramatiq_task_runner.send_with_options(
        args=(task_pk, workflow_pk),
        delay=countdown,
        retries=retries,
    )


class RetryError(Exception):
    """Raised to retry a task if the task result is ``False``."""

    pass


@dramatiq.actor(
    queue_name=settings.JOEFLOW_CELERY_QUEUE_NAME,
    retry_when=lambda a, b: isinstance(b, (OperationalError, RetryError)),
)
def _dramatiq_task_runner(task_pk, workflow_pk, retries=0):
    Task = apps.get_model("joeflow", "Task")
    with transaction.atomic():
        task = Task.objects.select_for_update().get(pk=task_pk, completed=None)

        workflow = (
            task.content_type.model_class()
            .objects.select_for_update(nowait=True)
            .get(pk=workflow_pk)
        )

        try:
            logger.info("Executing %r", task)
            node = task.node
            with_task = getattr(node, "with_task", False)
            kwargs = {}
            if with_task:
                kwargs["task"] = task
            with with_reversion(task):
                result = node(workflow, **kwargs)
        except OperationalError:
            raise
        except:  # NoQA
            task.fail()
            logger.exception("Execution of %r failed", task)
        else:
            if result is False:
                logger.info("Task returned False, retrying …")
                raise RetryError("Task returned False, retrying …")
            elif result is True:
                result = None
            logger.info("Task completed successful, starting next tasks: %s", result)
            task.start_next_tasks(next_nodes=result)
            task.finish()
