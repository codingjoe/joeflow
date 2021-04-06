import logging

from celery import shared_task
from django.apps import apps
from django.db import OperationalError, transaction

from joeflow.conf import settings
from joeflow.contrib.reversion import with_reversion

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
                transaction.on_commit(lambda: self.retry())
                return
            elif result is True:
                result = None
            logger.info("Task completed successful, starting next tasks: %s", result)
            task.start_next_tasks(next_nodes=result)
            task.finish()


def task_runner(*, task_pk, workflow_pk, countdown, eta):
    """Schedule asynchronous machine task using celery."""
    _celery_task_runner.apply_async(
        args=(task_pk, workflow_pk),
        countdown=countdown,
        eta=eta,
        queue=settings.JOEFLOW_CELERY_QUEUE_NAME,
    )
