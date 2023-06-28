from datetime import timedelta

from django.utils import timezone

from joeflow import tasks
from joeflow.models import Task
from tests.testapp import workflows


class TestStart:
    def test_call(self, db):
        wf = workflows.SimpleWorkflow.start_method(pk=3)
        assert wf.pk == 3

        start_task = wf.task_set.get(name="start_method")
        assert start_task.type == "machine"
        assert start_task.status == "succeeded"


class TestJoin:
    def test_init(self):
        node = tasks.Join("1", "2", "3")
        assert node.parents == {"1", "2", "3"}

    def test_call(self, db):
        wf = workflows.SimpleWorkflow.start_method()
        assert isinstance(wf, workflows.SimpleWorkflow)
        task = wf.task_set.latest()
        assert not tasks.Join("does_not_have_the_parent")(None, task)
        assert tasks.Join("start_method")(None, task)

    def test_create_task(self, db):
        wf = workflows.SimpleWorkflow.start_method()
        node = tasks.Join()
        node.name = "test"
        node.type = "machine"
        obj = node.create_task(wf, None)
        obj2 = node.create_task(wf, None)
        assert obj == obj2
        obj.finish()
        obj3 = node.create_task(wf, None)
        assert obj != obj3


class TestWait:
    def test_call(self):
        created = timezone.now()
        task = Task(created=created)
        task_func = tasks.Wait(timedelta(seconds=3))
        assert task_func(None, task) is False

        task.created -= timedelta(seconds=3)
        task_func = tasks.Wait(timedelta(seconds=3))
        assert task_func(None, task)
