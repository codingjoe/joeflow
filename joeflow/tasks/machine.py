"""Set of reusable machine tasks."""
from typing import Iterable

from django.utils import timezone

__all__ = (
    "Start",
    "Join",
    "Wait",
)

try:
    # We need to import the Dramatiq task,to ensure
    # it is deteced by django-dramatiq rundramatiq command.
    from joeflow.runner.dramatiq import _dramatiq_task_runner  # NoQA
except ImportError:
    pass


class Start:
    """
    Start a new function via a callable.

    Creates a new workflow instance and executes a start task.
    The start task does not do anything beyond creating the workflow.

    Sample:

    .. code-block:: python

        from django.db import models
        from joeflow.models import Workflow
        from joeflow import tasks


        class StartWorkflow(Workflow):
            a_text_field = models.TextField()

            start = tasks.Start()

            def end(self):
                pass

            edges = (
                (start, end),
            )

        workflow = StartWorkflow.start(a_text_field="initial data")

    """

    def __call__(self, **kwargs):
        workflow = self.workflow_cls.objects.create(**kwargs)
        task = workflow.task_set.create(name=self.name, workflow=workflow)
        task.start_next_tasks()
        return workflow


class Join:
    """
    Wait for all parent tasks to complete before continuing the workflow.

    Args:
        *parents (str): List of parent task names to wait for.

    Sample:

    .. code-block:: python

        from django.db import models
        from joeflow.models import Workflow
        from joeflow import tasks


        class SplitJoinWorkflow(Workflow):
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

    def __call__(self, workflow, task):
        return set(task.parent_task_set.values_list("name", flat=True)) == self.parents

    def create_task(self, workflow, prev_task):
        return workflow.task_set.get_or_create(
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
        from joeflow.models import Workflow
        from joeflow import tasks


        class WaitWorkflow(Workflow):
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

    def __call__(self, workflow, task):
        return timezone.now() - task.created >= self.duration
