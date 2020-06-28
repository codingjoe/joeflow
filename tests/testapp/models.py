from django.conf import settings
from django.db import models

from joeflow.models import Workflow


class Shipment(Workflow):
    email = models.EmailField(blank=True)
    shipping_address = models.TextField()
    tracking_code = models.TextField()


class WelcomeWorkflowState(Workflow):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True,
    )


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
