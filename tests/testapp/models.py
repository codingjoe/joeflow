from django.conf import settings
from django.db import models

from joeflow import tasks
from joeflow.models import Workflow


class Shipment(Workflow):
    email = models.EmailField(blank=True)
    shipping_address = models.TextField()
    tracking_code = models.TextField()


class WelcomeWorkflow(Workflow):
    # state
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    # behavior
    start = tasks.StartView(fields=["user"])

    def has_user(self):
        if self.user:
            return [self.send_welcome_email]
        else:
            return [self.end]

    def send_welcome_email(self):
        self.user.email_user(
            subject="Welcome",
            message="Hello %s!" % self.user.get_short_name(),
        )

    def end(self):
        pass

    edges = [
        (start, has_user),
        (has_user, end),
        (has_user, send_welcome_email),
        (send_welcome_email, end),
    ]


class SimpleWorkflowState(Workflow):
    pass


class GatewayWorkflowState(Workflow):
    pass


class SplitJoinWorkflowState(Workflow):
    parallel_task_value = models.PositiveIntegerField(default=0)


class LoopWorkflowState(Workflow):
    counter = models.PositiveIntegerField(default=0)


class WaitWorkflowState(Workflow):
    parallel_task_value = models.PositiveIntegerField(default=0)


class FailingWorkflowState(Workflow):
    pass


class TestWorkflowState(Workflow):
    pass
