"""High level integration tests."""
import sys
import time

import pytest
from django.urls import reverse

from tests.testapp import models


class TestSimpleProcess:

    def test_url__get(self, db, client):
        p = models.SimpleProcess.objects.create()
        t = p.task_set.create(node_name='save_the_princess')
        url = reverse('simpleprocess:save_the_princess', args=[t.pk])
        assert list(models.SimpleProcess.urls())
        response = client.get(url)
        assert response.status_code == 200

    def test_url__get__does_not_exist(self, db, client):
        p = models.SimpleProcess.objects.create()
        t = p.task_set.create()
        url = reverse('simpleprocess:save_the_princess', args=[t.pk])
        assert list(models.SimpleProcess.urls())
        response = client.get(url)
        assert response.status_code == 404

    def test_url__post(self, db, client):
        p = models.SimpleProcess.objects.create()
        t = p.task_set.create(node_name='save_the_princess')
        url = reverse('simpleprocess:save_the_princess', args=[t.pk])
        assert list(models.SimpleProcess.urls())
        response = client.get(url)
        assert response.status_code == 200

        response = client.post(url)
        assert response.status_code == 302
        t.refresh_from_db()
        assert t.completed
        obj = p.task_set.get(node_name='end')
        assert obj.completed

    def test_start_view_get(self, db, client):
        url = reverse('simpleprocess:start_view')
        response = client.get(url)
        assert response.status_code == 200

    def test_start_view_post(self, db, client):
        url = reverse('simpleprocess:start_view')
        response = client.post(url)
        assert response.status_code == 302
        assert models.SimpleProcess.objects.exists()
        obj = models.SimpleProcess.objects.get()
        assert obj.task_set.count() == 2

    def test_start_method(self, db):
        obj = models.SimpleProcess.start_method()
        assert obj.task_set.filter(node_name='start_method').count() == 1


class TestSplitJoinProcess:

    def test_join(self, db, client):
        url = reverse('splitjoinprocess:start')
        response = client.post(url)
        assert response.status_code == 302
        obj = models.SplitJoinProcess.objects.get()
        assert obj.parallel_task_value == 2
        assert obj.task_set.filter(node_name='join').count() == 1


class TestLoopProcess:

    def test_loop(self, db, client):
        url = reverse('loopprocess:start')
        response = client.post(url)
        assert response.status_code == 302

        obj = models.LoopProcess.objects.get()
        assert obj.counter == 10
        assert obj.task_set.filter(node_name='increment_counter').count() == 10


class TestTaskAdmin:
    def test_changelist(self, db, admin_client):
        models.SimpleProcess.start_method()
        url = reverse('admin:galahad_task_changelist')
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_change(self, db, admin_client):
        process = models.SimpleProcess.start_method()
        task = process.task_set.last()
        url = reverse('admin:galahad_task_change', args=[task.pk])
        response = admin_client.get(url)
        assert response.status_code == 200
