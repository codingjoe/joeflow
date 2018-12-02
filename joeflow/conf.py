from appconf import AppConf
from django.conf import settings

__all__ = (
    'settings',
)


class JoeflowAppConfig(AppConf):
    """
    List of available settings.

    To change the default values just set the setting in your settings file.
    """

    JOEFLOW_REDIS_LOCK_URL = 'redis://'
    """
    Redis database your for Redis database that is used for process locking.
    """

    JOEFLOW_REDIS_LOCK_TIMEOUT = 60
    """
    Process lock timeout in seconds.
    
    Processes are lock and only one machine task at a time can change the
    process state.
    """

    JOEFLOW_CELERY_QUEUE_NAME = 'celery'
    """
    Queue name in which all machine tasks will be queued.
    """
