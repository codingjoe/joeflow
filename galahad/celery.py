import logging
import random

from celery import shared_task
from django.apps import apps
from django.db import transaction

from . import locking

logger = logging.getLogger('galahad')


def jitter():
    """Return a random number between 0 and 1."""
    return random.randrange(1)


def backoff(retries):
    """Return an exponentially growing number limited to 600 plus a random jitter."""
    return min(600, 2 ** retries) + jitter()


@shared_task(bind=True, ignore_results=True)
def task_wrapper(self, task_pk, process_pk, retries=0):
    with locking.lock(process_pk) as lock_result:
        if not lock_result:
            countdown = backoff(self.request.retries)
            logger.info("Process is locked, retrying in %s seconds", countdown)
            self.retry(countdown=countdown)
        Task = apps.get_model('galahad', 'Task')
        task = Task.objects.get(pk=task_pk, completed=None)
        process = task.process

        try:
            logger.info("Executing %r", task)
            node = getattr(type(process), task.node_name)
            if getattr(node, 'with_task', False):
                result = node(process, task)
            else:
                result = node(process)
        except:  # NoQA
            task.fail()
            logger.exception("Execution of %r failed", task)
        else:
            if result is False:
                countdown = backoff(retries)
                logger.info("Task returned False, retrying in %s seconds", countdown)
                transaction.on_commit(lambda: task.enqueue(countdown=countdown, retires=retries+1))
                return
            elif result is True:
                result = None
            logger.info("Task completed successful, starting next tasks: %s", result)
            task.start_next_tasks(next_nodes=result)
            task.finish()
