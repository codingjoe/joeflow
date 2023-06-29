from django.urls import reverse

from .testapp import models, workflows


class TestTaskViewMixin:
    def test_next_task__form_errors(self, db, admin_client, admin_user):
        url = reverse("shippingworkflow:checkout")
        response = admin_client.post(
            url, data={"shipping_address": 123, "email": "not a email"}
        )
        assert response.status_code == 200
        assert response.context_data["form"].errors == {
            "email": ["Enter a valid email address."]
        }

        assert models.Shipment.objects.count() == 0

    def test_create_task(self, db, admin_client, admin_user):
        url = reverse("simpleworkflow:start_view")
        response = admin_client.post(url)
        assert response.status_code == 302

        wf = workflows.SimpleWorkflow.objects.get()
        assert wf.task_set.count() == 2

        start_task = wf.task_set.get(name="start_view")
        assert start_task.type == "human"
        assert start_task.status == "succeeded"

        new_task = wf.task_set.get(name="save_the_princess")
        assert new_task.type == "human"
        assert new_task.status == "scheduled"
        assert not new_task.assignees.all()

    def test_custom_create_task(self, db, admin_client, admin_user):
        url = reverse("assigneeworkflow:start_view")
        response = admin_client.post(url)
        assert response.status_code == 302

        wf = workflows.AssigneeWorkflow.objects.get()
        assert wf.task_set.count() == 2

        new_task = wf.task_set.get(name="save_the_princess")
        assert admin_user in new_task.assignees.all()
