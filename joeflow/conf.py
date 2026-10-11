from appconf import AppConf
from django.conf import settings

__all__ = ("settings",)


class JoeflowAppConfig(AppConf):
    """
    List of available settings.

    To change the default values just set the setting in your settings file.
    """

    JOEFLOW_TASK_RUNNER = "joeflow.runner.django_tasks.task_runner"
    """
    Execute machine tasks with this task runner.

    Requires a task backend in the ``TASKS`` setting. Set this setting to the
    dotted path of a custom task runner.

    .. _Django Tasks: https://docs.djangoproject.com/en/stable/topics/tasks/
    """

    JOEFLOW_TASK_QUEUE_NAME = "joeflow"
    """
    Send machine tasks to the named queue.

    The queue must be listed in the ``QUEUES`` of the task backend used by the
    ``TASKS`` setting.
    """
