import pytest

from joeflow import locking


def raise_inside_lock_context(process_pk):
    with locking._lock(process_pk) as lock:
        yield lock
        raise Exception('some unexpected error')


def test_lock__blocking():
    process_pk = 12345
    with locking._lock(process_pk) as lock:
        assert lock is True
        with locking._lock(process_pk) as another_lock:
            assert another_lock is False


def test_lock__release():
    process_pk = 12345
    with locking._lock(process_pk) as lock:
        assert lock is True
    # release
    with locking._lock(process_pk) as lock:
        assert lock is True


def test_lock__release_on_exception():
    process_pk = 12345
    generator = raise_inside_lock_context(process_pk)
    assert next(generator) is True
    with pytest.raises(Exception):
        next(generator)
        # release

    with locking._lock(process_pk) as lock:
        assert lock is True
