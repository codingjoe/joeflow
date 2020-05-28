from contextlib import contextmanager

import redis

from .conf import settings

__all__ = ("lock",)


@contextmanager
def _lock(process_pk):
    """
    Non blocking lock to prevent raise conditions on processes.

    Task especially machine tasks can be executed in parallel. To avoid
    raise conditions all tasks need to acquire a lock before they modify
    the process state. This avoids tasks to be executed with the wrong
    process state and multiple tasks changing a value of the same process
    field.

    The lock is not blocking to free CPU time for other tasks on celery
    workers.
    """
    connection = redis.Redis.from_url(settings.JOEFLOW_REDIS_LOCK_URL)
    __lock = connection.lock(
        "joeflow_process_{}".format(process_pk),
        timeout=settings.JOEFLOW_REDIS_LOCK_TIMEOUT,
    )
    successful = __lock.acquire(blocking=False)
    try:
        yield successful
    except BaseException:
        pass
    finally:
        if successful:
            __lock.release()
        connection.close()


# little hack for testing purposes
lock = _lock
