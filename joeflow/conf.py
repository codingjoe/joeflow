import warnings

from appconf import AppConf
from django.conf import settings

__all__ = ("settings",)


def _default_task_runner() -> str:
    """Return the default task runner for the installed environment."""
    try:
        import django.tasks  # NoQA
    except ImportError:
        # Django < 6.0 does not ship the Tasks framework.
        try:
            import dramatiq  # NoQA
        except ImportError:
            return "joeflow.runner.celery.task_runner"
        return "joeflow.runner.dramatiq.task_runner"
    return "joeflow.runner.django_tasks.task_runner"


def _default_task_queue_name() -> str:
    """Return the default task queue name.

    Falls back to the deprecated ``JOEFLOW_CELERY_QUEUE_NAME`` setting.
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
    Task runner is used to execute machine tasks.

    Machine tasks are executed asynchronously with `Django Tasks`_ on Django
    6.0 and later. A task backend must be configured with the ``TASKS``
    setting.

    On Django < 6.0 the task runner defaults to Dramatiq_ if installed,
    otherwise to Celery_. Both are deprecated in favor of Django Tasks.

    Set this setting to execute machine tasks with a custom task runner.

    .. warning::
        The Celery_ and Dramatiq_ task runners are deprecated and will be
        removed with the expiration of Django 5.2 LTS version support.

    .. _Django Tasks: https://docs.djangoproject.com/en/stable/topics/tasks/
    .. _Dramatiq: https://dramatiq.io/
    .. _Celery: http://www.celeryproject.org/
    """

    JOEFLOW_TASK_QUEUE_NAME = _default_task_queue_name()
    """
    Queue name in which all machine tasks will be queued.

    The queue must be listed in the ``QUEUES`` of the task backend used by
    the ``TASKS`` setting. The deprecated ``JOEFLOW_CELERY_QUEUE_NAME``
    setting is used as a fallback if it is set.
    """

    JOEFLOW_TASK_RETRY_DELAY = 60
    """
    Time in seconds to wait before a machine task is re-enqueued.

    A machine task is re-enqueued if it cannot be executed, because another
    process holds the lock or because the task is not ready to continue yet.
    This requires a task backend with support for deferred execution.
    """
