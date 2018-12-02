import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

from joeflow import admin
from joeflow.models import Task
from tests.testapp import models


class TestTaskAdmin:

    @pytest.fixture
    def post_request(self, rf):
        request = rf.post('/')

        # adding session
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        # adding messages
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        setattr(request, 'user', AnonymousUser())
        return request

    def test_rerun(self, db, no_on_commit, post_request):
        process = models.SimpleProcess.objects.create()
        task = process.task_set.create(status=Task.FAILED, name='save_the_princess')
        admin.rerun(None, post_request, process.task_set.all())
        assert '1 tasks have been successfully queued' == str(post_request._messages._queued_messages[0])
        task.refresh_from_db()
        assert task.status == Task.SCHEDULED

    def test_rerun__succeeded(self, db, no_on_commit, post_request):
        process = models.SimpleProcess.objects.create()
        task = process.task_set.create(status=Task.SUCCEEDED, name='save_the_princess')
        admin.rerun(None, post_request, process.task_set.all())
        assert 'Only failed tasks can be retried. 1 tasks have been skipped' == \
               str(post_request._messages._queued_messages[0])
        assert '0 tasks have been successfully queued' == \
               str(post_request._messages._queued_messages[1])
        task.refresh_from_db()
        assert task.status == Task.SUCCEEDED

    def test_cancel(self, db, post_request):
        process = models.SimpleProcess.objects.create()
        task = process.task_set.create(name='save_the_princess')
        admin.cancel(None, post_request, process.task_set.all())
        assert "Tasks have been successfully canceled" == \
               str(post_request._messages._queued_messages[0])
        task.refresh_from_db()
        assert task.status == Task.CANCELED

    def test_cancel__not_scheduled(self, db, post_request):
        process = models.SimpleProcess.objects.create()
        task = process.task_set.create(status=Task.SUCCEEDED, name='save_the_princess')
        admin.cancel(None, post_request, process.task_set.all())
        assert 'Only scheduled tasks can be canceled. 1 tasks have been skipped' == \
               str(post_request._messages._queued_messages[0])
        assert "Tasks have been successfully canceled" == \
               str(post_request._messages._queued_messages[1])
        task.refresh_from_db()
        assert task.status == Task.SUCCEEDED
