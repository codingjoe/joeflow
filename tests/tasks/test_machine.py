from datetime import timedelta

from django.utils import timezone

from joeflow import tasks
from joeflow.models import Task
from tests.testapp import models


class TestStart:

    def test_call(self, db):
        proc = models.SimpleProcess.start_method(pk=3)
        assert proc.pk == 3


class TestJoin:

    def test_init(self):
        node = tasks.Join('1', '2', '3')
        assert node.parents == {'1', '2', '3'}

    def test_call(self, db):
        proc = models.SimpleProcess.start_method()
        task = proc.task_set.latest()
        assert not tasks.Join('does_not_have_the_parent')(None, task)
        assert tasks.Join('start_method')(None, task)

    def test_create_task(self, db):
        proc = models.SimpleProcess.start_method()
        node = tasks.Join()
        node.name = 'test'
        node.type = 'machine'
        obj = node.create_task(proc)
        obj2 = node.create_task(proc)
        assert obj == obj2
        obj.finish()
        obj3 = node.create_task(proc)
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
