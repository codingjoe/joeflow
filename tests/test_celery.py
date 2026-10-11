"""Tests for the deprecated Celery task runner."""

from unittest import mock

import pytest

pytest.importorskip("celery")

import django  # NoQA: E402
from joeflow.runner import celery  # NoQA: E402

pytestmark = pytest.mark.skipif(
    django.VERSION < (6, 0),
    reason="The Celery task runner is only deprecated on Django >= 6.0.",
)


def test_deprecated(monkeypatch):
    apply_async = mock.Mock()
    monkeypatch.setattr(celery._celery_task_runner, "apply_async", apply_async)
    with pytest.warns(
        PendingDeprecationWarning, match="Celery task runner is deprecated"
    ):
        celery.task_runner(task_pk=1, workflow_pk=2)
    apply_async.assert_called_once_with(
        args=(1, 2), countdown=None, eta=None, queue="yoloflow"
    )
