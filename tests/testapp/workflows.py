from datetime import timedelta

from django.core.mail import send_mail

from joeflow import tasks

from . import models
from .views import UpdateWithPrevUserView


class ShippingWorkflow(models.Shipment):
    checkout = tasks.StartView(fields=["shipping_address", "email"])

    ship = tasks.UpdateView(fields=["tracking_code"])

    def has_email(self, task):
        if self.email:
            return [self.send_tracking_code]

    def send_tracking_code(self, task):
        send_mail(
            subject="Your tracking code",
            message=self.tracking_code,
            from_email=None,
            recipient_list=[self.email],
        )

    def end(self, task):
        pass

    edges = [
        (checkout, ship),
        (ship, has_email),
        (has_email, send_tracking_code),
        (has_email, end),
        (send_tracking_code, end),
    ]

    class Meta:
        proxy = True


class SimpleWorkflow(models.SimpleWorkflowState):
    start_view = tasks.StartView(fields="__all__", path="custom/postfix/")
    start_method = tasks.Start()
    save_the_princess = tasks.UpdateView(fields="__all__")

    def end(self):
        pass

    edges = (
        (start_view, save_the_princess),
        (start_method, save_the_princess),
        (save_the_princess, end),
    )

    class Meta:
        proxy = True


class AssigneeWorkflow(models.SimpleWorkflowState):
    start_view = tasks.StartView(fields="__all__", path="custom/postfix/")
    start_method = tasks.Start()
    save_the_princess = UpdateWithPrevUserView(fields="__all__")

    def end(self):
        pass

    edges = (
        (start_view, save_the_princess),
        (start_method, save_the_princess),
        (save_the_princess, end),
    )

    class Meta:
        proxy = True


class GatewayWorkflow(models.GatewayWorkflowState):
    start = tasks.StartView(fields="__all__")

    save_the_princess = tasks.UpdateView()

    def is_princess_safe(self):
        return [self.happy_end]

    happy_end = lambda s, task: s.finish()
    bad_end = lambda s, task: s.finish()

    edges = (
        (start, is_princess_safe),
        (is_princess_safe, happy_end),
        (is_princess_safe, bad_end),
    )

    class Meta:
        proxy = True


class SplitJoinWorkflow(models.SplitJoinWorkflowState):
    start = tasks.StartView(fields=[])

    def split(self):
        return [self.batman, self.robin]

    def batman(self):
        self.parallel_task_value += 1
        self.save(update_fields=["parallel_task_value"])

    def robin(self):
        self.parallel_task_value += 1
        self.save(update_fields=["parallel_task_value"])

    join = tasks.Join("batman", "robin")

    edges = (
        (start, split),
        (split, batman),
        (split, robin),
        (batman, join),
        (robin, join),
    )

    class Meta:
        proxy = True


class LoopWorkflow(models.LoopWorkflowState):
    start = tasks.StartView(fields=[])

    def increment_counter(self):
        self.counter += 1
        self.save(update_fields=["counter"])

    def is_counter_10(self):
        if self.counter == 10:
            return [self.end]
        return [self.increment_counter]

    def end(self):
        pass

    edges = (
        (start, increment_counter),
        (increment_counter, is_counter_10),
        (is_counter_10, increment_counter),
        (is_counter_10, end),
    )

    class Meta:
        proxy = True


class WaitWorkflow(models.WaitWorkflowState):
    start = tasks.Start()

    wait = tasks.Wait(timedelta(hours=3))

    def end(self):
        pass

    edges = (
        (start, wait),
        (wait, end),
    )

    class Meta:
        proxy = True


class FailingWorkflow(models.FailingWorkflowState):
    start = tasks.Start()

    def fail(self):
        raise ValueError("Boom!")

    edges = ((start, fail),)

    class Meta:
        proxy = True


class TestWorkflow(models.TestWorkflowState):
    a = tasks.Start()
    b = tasks.UpdateView()
    c = lambda s, t: s

    not_a_node = lambda s, t: s

    edges = [
        (a, b),
        (b, c),
    ]

    class Meta:
        proxy = True
