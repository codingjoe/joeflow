from datetime import timedelta

from django.conf import settings
from django.db import models

from joeflow import tasks
from joeflow.models import Process
from tests.testapp import views


class WelcomeProcessState(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True, null=True,
    )

    class Meta:
        abstract = True


class WelcomeProcess(WelcomeProcessState, Process):
    start = tasks.StartView(fields=['user'])

    def has_user(self):
        if self.user:
            return [self.send_welcome_email]
        else:
            return [self.end]

    def send_welcome_email(self):
        self.user.email_user(
            subject='Welcome',
            message='Hello %s!' % self.user.get_short_name(),
        )

    def end(self):
        pass

    edges = (
        (start, has_user),
        (has_user, end),
        (has_user, send_welcome_email),
        (send_welcome_email, end),
    )


class SimpleProcess(Process):
    start_view = views.StartView(fields='__all__')
    start_method = tasks.Start()
    save_the_princess = views.TaskView(fields='__all__')

    def end(self):
        pass

    edges = (
        (start_view, save_the_princess),
        (start_method, save_the_princess),
        (save_the_princess, end),
    )


class GatewayProcess(Process):
    start = views.StartView(fields='__all__')

    save_the_princess = views.TaskView()

    def is_princess_safe(self):
        return [self.happy_end]

    happy_end = lambda s, task: s.finish()
    bad_end = lambda s, task: s.finish()

    edges = (
        (start, is_princess_safe),
        (is_princess_safe, happy_end),
        (is_princess_safe, bad_end),
    )


class SplitJoinProcess(Process):
    parallel_task_value = models.PositiveIntegerField(default=0)

    start = views.StartView(fields=[])

    def split(self):
        return [self.batman, self.robin]

    def batman(self):
        self.parallel_task_value += 1
        self.save(update_fields=['parallel_task_value'])

    def robin(self):
        self.parallel_task_value += 1
        self.save(update_fields=['parallel_task_value'])

    join = tasks.Join('batman', 'robin')

    edges = (
        (start, split),
        (split, batman),
        (split, robin),
        (batman, join),
        (robin, join),
    )


class LoopProcess(Process):
    counter = models.PositiveIntegerField(default=0)

    start = views.StartView(fields=[])

    def increment_counter(self):
        self.counter += 1
        self.save(update_fields=['counter'])

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


class WaitProcess(Process):
    parallel_task_value = models.PositiveIntegerField(default=0)

    start = tasks.Start()

    wait = tasks.Wait(timedelta(hours=3))

    def end(self):
        pass

    edges = (
        (start, wait),
        (wait, end),
    )


class FailingProcess(Process):
    start = tasks.Start()

    def fail(self):
        raise ValueError("Boom!")

    edges = (
        (start, fail),
    )
