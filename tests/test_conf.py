"""Tests for the joeflow application settings."""

from django.conf import settings


class TestTaskRunner:
    def test_default(self):
        assert settings.JOEFLOW_TASK_RUNNER == "joeflow.runner.django_tasks.task_runner"


class TestTaskQueueName:
    def test_override(self):
        """The test project configures a queue other than the default."""
        assert settings.JOEFLOW_TASK_QUEUE_NAME == "yoloflow"
