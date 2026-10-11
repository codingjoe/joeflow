"""Tests for the joeflow application settings."""

import pytest
from joeflow import conf


class TestDefaultTaskQueueName:
    def test_default(self, monkeypatch):
        monkeypatch.setattr(conf.settings, "is_overridden", lambda name: False)
        assert conf._default_task_queue_name() == "joeflow"

    def test_deprecated_setting(self, monkeypatch):
        monkeypatch.setattr(
            conf.settings,
            "is_overridden",
            lambda name: name == "JOEFLOW_CELERY_QUEUE_NAME",
        )
        monkeypatch.setattr(
            conf.settings, "JOEFLOW_CELERY_QUEUE_NAME", "legacy", raising=False
        )
        with pytest.warns(DeprecationWarning, match="JOEFLOW_CELERY_QUEUE_NAME"):
            assert conf._default_task_queue_name() == "legacy"

    def test_deprecated_setting__new_setting_takes_precedence(self, monkeypatch):
        monkeypatch.setattr(conf.settings, "is_overridden", lambda name: True)
        monkeypatch.setattr(
            conf.settings, "JOEFLOW_CELERY_QUEUE_NAME", "legacy", raising=False
        )
        with pytest.warns(DeprecationWarning, match="JOEFLOW_CELERY_QUEUE_NAME"):
            assert conf._default_task_queue_name() == "joeflow"
