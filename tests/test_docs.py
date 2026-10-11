from django.contrib.auth import get_user_model
from django.core import mail
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .testapp import models


class WelcomeWorkflowMachineTest(SimpleTestCase):
    def test_has_user__with_user(self):
        user = get_user_model()(
            email="spiderman@avengers.com",
            first_name="Peter",
            last_name="Parker",
            username="spidy",
        )
        workflow = models.WelcomeWorkflow(user=user)
        assert workflow.has_user() == [workflow.send_welcome_email]

    def test_has_user__without_user(self):
        workflow = models.WelcomeWorkflow()
        assert workflow.has_user() == [workflow.end]

    def test_send_welcome_email(self):
        user = get_user_model()(
            email="spiderman@avengers.com",
            first_name="Peter",
            last_name="Parker",
            username="spidy",
        )
        workflow = models.WelcomeWorkflow(user=user)

        workflow.send_welcome_email()

        email = mail.outbox[-1]
        assert email.subject == "Welcome"
        assert email.body == "Hello Peter!"
        assert "spiderman@avengers.com" in email.to


class WelcomeWorkflowHumanTest(TestCase):
    start_url = reverse("welcomeworkflow:start")

    def test_start__get(self):
        response = self.client.get(self.start_url)
        assert response.status_code == 200

    def test_start__post_with_user(self):
        user = get_user_model().objects.create(
            email="spiderman@avengers.com",
            first_name="Peter",
            last_name="Parker",
            username="spidy",
        )

        response = self.client.post(self.start_url, data={"user": user.pk})
        assert response.status_code == 302
        workflow = models.WelcomeWorkflow.objects.get()
        assert workflow.user
        assert workflow.task_set.succeeded().filter(name="start").exists()

    def test_start__post_without_user(self):
        response = self.client.post(self.start_url)
        assert response.status_code == 302
        workflow = models.WelcomeWorkflow.objects.get()
        assert not workflow.user
        assert workflow.task_set.succeeded().filter(name="start").exists()
