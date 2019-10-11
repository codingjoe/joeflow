"""Set of reusable machine tasks."""
from typing import Iterable

from django.utils import timezone

__all__ = (
    'Start',
    'Join',
    'Wait',
)


class Start:
    """
    Start a new function via a callable.

    Creates a new process instance and executes a start task.
    The start task does not do anything beyond creating the process.

    Sample:

    .. code-block:: python

        from django.db import models
        from joeflow.models import Process
        from joeflow import tasks


        class StartProcess(Process):
            a_text_field = models.TextField()

            start = tasks.Start()

            def end(self):
                pass

            edges = (
                (start, end),
            )

        process = StartProcess.start(a_text_field="initial data")

    """

    def __call__(self, **kwargs):
        obj = self.process_cls.objects.create(**kwargs)
        task = obj.task_set.create(name=self.name)
        task.start_next_tasks()
        return obj


class Join:
    """
    Wait for all parent tasks to complete before continuing the process.

    Args:
        *parents (str): List of parent task names to wait for.

    Sample:

    .. code-block:: python

        from django.db import models
        from joeflow.models import Process
        from joeflow import tasks


        class SplitJoinProcess(Process):
            parallel_task_value = models.PositiveIntegerField(default=0)

            start = tasks.Start()

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

    """

    with_task = True

    def __init__(self, *parents: Iterable[str]):
        self.parents = set(parents)

    def __call__(self, process, task):
        return set(task.parent_task_set.values_list('name', flat=True)) == self.parents

    def create_task(self, process):
        return process.task_set.get_or_create(
            name=self.name,
            type=self.type,
            completed=None,
        )[0]


class Wait:
    """
    Wait for a certain amount of time and then continue with the next tasks.

    Args:
        duration (datetime.timedelta): Time to wait in time delta from creation of task.

    Sample:

    .. code-block:: python

        import datetime

        from django.db import models
        from joeflow.models import Process
        from joeflow import tasks


        class WaitProcess(Process):
            parallel_task_value = models.PositiveIntegerField(default=0)

            start = tasks.Start()

            wait = tasks.Wait(datetime.timedelta(hours=3))

            def end(self):
                pass

            edges = (
                (start, wait),
                (wait, end),
            )

    """

    with_task = True

    def __init__(self, duration: timezone.timedelta):
        self.duration = duration

    def __call__(self, process, task):
        return timezone.now() - task.created >= self.duration
