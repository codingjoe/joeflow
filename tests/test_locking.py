import pytest

from joeflow import locking


def raise_inside_lock_context(workflow_pk):
    with locking._lock(workflow_pk) as lock:
        yield lock
        raise Exception("some unexpected error")


def test_lock__blocking():
    workflow_pk = 12345
    with locking._lock(workflow_pk) as lock:
        assert lock is True
        with locking._lock(workflow_pk) as another_lock:
            assert another_lock is False


def test_lock__release():
    workflow_pk = 12345
    with locking._lock(workflow_pk) as lock:
        assert lock is True
    # release
    with locking._lock(workflow_pk) as lock:
        assert lock is True


def test_lock__release_on_exception():
    workflow_pk = 12345
    generator = raise_inside_lock_context(workflow_pk)
    assert next(generator) is True
    with pytest.raises(Exception):
        next(generator)
        # release

    with locking._lock(workflow_pk) as lock:
        assert lock is True
