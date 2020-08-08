from appconf import AppConf
from django.conf import settings

__all__ = ("settings",)


class JoeflowAppConfig(AppConf):
    """
    List of available settings.

    To change the default values just set the setting in your settings file.
    """

    JOEFLOW_TASK_RUNNER = "joeflow.runner.dramatiq.task_runner"
    """
    Task runner is used to execute machine tasks.

    JoeFlow supports two different asynchronous task runners – Dramatiq_ and Celery_.

    To use either of the task runners change this setting to:

    * ``joeflow.runner.dramatiq.task_runner``
    * ``joeflow.runner.celery.task_runner``

    .. _Dramatiq: https://dramatiq.io/
    .. _Celery: http://www.celeryproject.org/
    """

    JOEFLOW_CELERY_QUEUE_NAME = "joeflow"
    """
    Queue name in which all machine tasks will be queued.
    """
