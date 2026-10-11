"""Tests for the shared machine task execution."""

from unittest import mock

import pytest
from django.db import OperationalError
from joeflow.runner import base


def test_execute__operational_error(monkeypatch):
    """An OperationalError is re-raised so the runner can retry the task."""
    monkeypatch.setattr(base, "with_reversion", mock.MagicMock())
    task = mock.Mock()
    task.node.side_effect = OperationalError("database is locked")
    with pytest.raises(OperationalError):
        base.execute(mock.Mock(), task)
    task.fail.assert_not_called()
