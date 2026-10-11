"""Shared machine task execution."""

import logging

from django.db import OperationalError

from ..contrib.reversion import with_reversion

logger = logging.getLogger(__name__)

__all__ = [
    "execute",
    "finish",
]


def execute(workflow, task):
    """
    Run the node of a machine task.

    Returns:
        tuple: Whether the node executed successfully and its result.

    """
    logger.info("Executing %r", task)
    node = task.node
    kwargs = {}
    if getattr(node, "with_task", False):
        kwargs["task"] = task
    try:
        with with_reversion(task):
            return True, node(workflow, **kwargs)
    except OperationalError:
        raise
    except:  # NoQA
        task.fail()
        logger.exception("Execution of %r failed", task)
        return False, None


def finish(task, result):
    """Start the next tasks after the current one completes successfully."""
    if result is True:
        result = None
    logger.info("Task completed successful, starting next tasks: %s", result)
    task.start_next_tasks(next_nodes=result)
    task.finish()
