"""Tests for the deprecated Dramatiq task runner."""

from unittest import mock

import pytest

pytest.importorskip("dramatiq")

import django  # NoQA: E402
from joeflow.runner import dramatiq  # NoQA: E402

pytestmark = pytest.mark.skipif(
    django.VERSION < (6, 0),
    reason="The Dramatiq task runner is only deprecated on Django >= 6.0.",
)


def test_deprecated(monkeypatch):
    send_with_options = mock.Mock()
    monkeypatch.setattr(
        dramatiq._dramatiq_task_runner, "send_with_options", send_with_options
    )
    with pytest.warns(
        PendingDeprecationWarning, match="Dramatiq task runner is deprecated"
    ):
        dramatiq.task_runner(task_pk=1, workflow_pk=2)
    send_with_options.assert_called_once_with(args=(1, 2), delay=None, retries=0)
