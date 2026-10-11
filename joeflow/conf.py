import warnings

import django
from appconf import AppConf
from django.conf import settings

__all__ = ("settings",)


def _default_task_runner() -> str:
    """Select the import path that executes machine tasks.

    The Tasks framework ships with Django 6.0 and later, older releases need a
    third-party task runner.
    """
    if django.VERSION >= (6, 0):
        return "joeflow.runner.django_tasks.task_runner"
    return "joeflow.runner.dramatiq.task_runner"


def _default_task_queue_name() -> str:
    """Resolve the configured queue, honoring the deprecated setting.

    A ``JOEFLOW_CELERY_QUEUE_NAME`` override applies while
    ``JOEFLOW_TASK_QUEUE_NAME`` is unset and warns about the deprecation.
    """
    if settings.is_overridden("JOEFLOW_CELERY_QUEUE_NAME"):
        warnings.warn(
            "The JOEFLOW_CELERY_QUEUE_NAME setting is deprecated, "
            "use JOEFLOW_TASK_QUEUE_NAME instead.",
            DeprecationWarning,
            stacklevel=4,
        )
        if not settings.is_overridden("JOEFLOW_TASK_QUEUE_NAME"):
            return settings.JOEFLOW_CELERY_QUEUE_NAME
    return "joeflow"


class JoeflowAppConfig(AppConf):
    """List of available settings.

    To change the default values just set the setting in your settings file.
    """

    JOEFLOW_TASK_RUNNER = _default_task_runner()
    """
    Execute machine tasks with this task runner.

    On Django 6.0 and later the default uses `Django Tasks`_ and requires a
    task backend in the ``TASKS`` setting. On older releases the default uses
    the deprecated Dramatiq_ task runner.

    Set this setting to the dotted path of a custom task runner, for example
    ``joeflow.runner.celery.task_runner``.

    .. warning::
        The Celery_ and Dramatiq_ task runners are deprecated and will be
        removed with the expiration of Django 5.2 LTS version support.

    .. _Django Tasks: https://docs.djangoproject.com/en/stable/topics/tasks/
    .. _Dramatiq: https://dramatiq.io/
    .. _Celery: http://www.celeryproject.org/
    """

    JOEFLOW_TASK_QUEUE_NAME = _default_task_queue_name()
    """
    Send machine tasks to the named queue.

    The queue must be listed in the ``QUEUES`` of the task backend used by the
    ``TASKS`` setting. A ``JOEFLOW_CELERY_QUEUE_NAME`` override applies as a
    deprecated fallback while this setting is unset.
    """
