from unittest.mock import Mock

import pytest
from django.contrib.admin import site
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
from joeflow import admin
from joeflow.admin import WorkflowAdmin
from joeflow.models import Task

from tests.testapp import models, workflows


class TestTaskAdmin:
    @pytest.fixture
    def post_request(self, rf):
        request = rf.post("/")

        # adding session
        middleware = SessionMiddleware(lambda x: "Response")
        middleware.process_request(request)
        request.session.save()

        # adding messages
        messages = FallbackStorage(request)
        request._messages = messages
        request.user = AnonymousUser()
        return request

    def test_rerun(self, db, post_request, stub_worker):
        workflow = models.SimpleWorkflowState.objects.create()
        task = workflow.task_set.create(status=Task.FAILED, name="save_the_princess")
        admin.rerun(None, post_request, workflow.task_set.all())
        assert "1 tasks have been successfully queued" == str(
            post_request._messages._queued_messages[0]
        )
        task.refresh_from_db()
        assert task.status == Task.SCHEDULED

    def test_rerun__succeeded(self, db, post_request):
        workflow = models.SimpleWorkflowState.objects.create()
        task = workflow.task_set.create(status=Task.SUCCEEDED, name="save_the_princess")
        admin.rerun(None, post_request, workflow.task_set.all())
        assert "Only failed tasks can be retried. 1 tasks have been skipped" == str(
            post_request._messages._queued_messages[0]
        )
        assert "0 tasks have been successfully queued" == str(
            post_request._messages._queued_messages[1]
        )
        task.refresh_from_db()
        assert task.status == Task.SUCCEEDED

    def test_cancel(self, db, post_request):
        workflow = models.SimpleWorkflowState.objects.create()
        task = workflow.task_set.create(name="save_the_princess")
        admin.cancel(None, post_request, workflow.task_set.all())
        assert "Tasks have been successfully canceled" == str(
            post_request._messages._queued_messages[0]
        )
        task.refresh_from_db()
        assert task.status == Task.CANCELED

    def test_cancel__not_scheduled(self, db, post_request):
        workflow = models.SimpleWorkflowState.objects.create()
        task = workflow.task_set.create(status=Task.SUCCEEDED, name="save_the_princess")
        admin.cancel(None, post_request, workflow.task_set.all())
        assert "Only scheduled tasks can be canceled. 1 tasks have been skipped" == str(
            post_request._messages._queued_messages[0]
        )
        assert "Tasks have been successfully canceled" == str(
            post_request._messages._queued_messages[1]
        )
        task.refresh_from_db()
        assert task.status == Task.SUCCEEDED


class TestWorkflowAdmin:
    def test_changelist(self, db, admin_client):
        workflows.SimpleWorkflow.start_method()
        response = admin_client.get(reverse("admin:testapp_simpleworkflow_changelist"))
        assert response.status_code == 200

    def test_change(self, db, admin_client):
        wf = workflows.SimpleWorkflow.start_method()
        response = admin_client.get(
            reverse("admin:testapp_simpleworkflow_change", args=[wf.pk])
        )
        assert response.status_code == 200

    def test_save_model(self, db, rf):
        wf = workflows.SimpleWorkflow.start_method()
        request = rf.get(
            reverse("admin:testapp_simpleworkflow_change", args=[wf.pk]),
            data={"next_tasks": ["end"]},
        )
        request.user = "user"
        form = Mock()
        WorkflowAdmin(workflows.SimpleWorkflow, site).save_model(
            request, wf, form, True
        )
        form.start_next_tasks.assert_called_once_with("user")
