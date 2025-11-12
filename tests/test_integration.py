"""High level integration tests."""

from django.urls import reverse
from joeflow.models import Task

from tests.testapp import workflows


class TestSimpleWorkflow:
    def test_url__get(self, db, client):
        wf = workflows.SimpleWorkflow.objects.create()
        t = wf.task_set.create(name="save_the_princess")
        url = reverse("simpleworkflow:save_the_princess", args=[t.pk])
        assert list(workflows.SimpleWorkflow.urls())
        response = client.get(url)
        assert response.status_code == 200

    def test_url__get__does_not_exist(self, db, client):
        wf = workflows.SimpleWorkflow.objects.create()
        t = wf.task_set.create()
        url = reverse("simpleworkflow:save_the_princess", args=[t.pk])
        assert list(workflows.SimpleWorkflow.urls())
        response = client.get(url)
        assert response.status_code == 404

    def test_url__post(self, transactional_db, stub_worker, client):
        wf = workflows.SimpleWorkflow.objects.create()
        t = wf.task_set.create(name="save_the_princess")
        url = reverse("simpleworkflow:save_the_princess", args=[t.pk])
        assert list(workflows.SimpleWorkflow.urls())
        response = client.get(url)
        assert response.status_code == 200

        response = client.post(url)
        assert response.status_code == 302
        stub_worker.wait()
        t.refresh_from_db()
        assert t.completed
        obj = wf.task_set.get(name="end")
        assert obj.completed

    def test_start_view_get(self, db, client):
        url = reverse("simpleworkflow:start_view")
        response = client.get(url)
        assert response.status_code == 200

    def test_start_view_post(self, db, client):
        url = reverse("simpleworkflow:start_view")
        response = client.post(url)
        assert response.status_code == 302
        assert workflows.SimpleWorkflow.objects.exists()
        obj = workflows.SimpleWorkflow.objects.get()
        assert obj.task_set.count() == 2

    def test_start_method(self, db):
        wf = workflows.SimpleWorkflow.start_method()
        assert wf.task_set.filter(name="start_method").count() == 1


class TestSplitJoinWorkflow:
    def test_join(self, transactional_db, stub_worker, client):
        url = reverse("splitjoinworkflow:start")
        response = client.post(url)
        assert response.status_code == 302
        stub_worker.wait()
        obj = workflows.SplitJoinWorkflow.objects.get()
        assert obj.task_set.filter(name="join").latest().status == "succeeded"
        obj.refresh_from_db()
        assert obj.parallel_task_value == 2
        assert obj.task_set.filter(name="join").count() == 1


class TestLoopWorkflow:
    def test_loop(self, transactional_db, stub_worker, client):
        url = reverse("loopworkflow:start")
        response = client.post(url)
        assert response.status_code == 302
        stub_worker.wait()
        obj = workflows.LoopWorkflow.objects.get()
        assert obj.counter == 10
        assert obj.task_set.filter(name="increment_counter").count() == 10


class TestTaskAdmin:
    def test_changelist(self, db, admin_client):
        workflows.SimpleWorkflow.start_method()
        url = reverse("admin:joeflow_task_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_change(self, db, admin_client):
        wf = workflows.SimpleWorkflow.start_method()
        task = wf.task_set.last()
        url = reverse("admin:joeflow_task_change", args=[task.pk])
        response = admin_client.get(url)
        assert response.status_code == 200


class TestFailingWorkflow:
    def test_fail(self, transactional_db, stub_worker):
        wf = workflows.FailingWorkflow.start()
        stub_worker.wait()
        failed_task = wf.task_set.latest()
        assert failed_task.status == Task.FAILED
        assert failed_task.exception == "ValueError: Boom!"
        assert "Traceback (most recent call last):" in failed_task.stacktrace
