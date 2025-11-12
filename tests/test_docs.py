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
        self.assertEqual(workflow.has_user(), [workflow.send_welcome_email])

    def test_has_user__without_user(self):
        workflow = models.WelcomeWorkflow()
        self.assertEqual(workflow.has_user(), [workflow.end])

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
        self.assertEqual(email.subject, "Welcome")
        self.assertEqual(email.body, "Hello Peter!")
        self.assertIn("spiderman@avengers.com", email.to)


class WelcomeWorkflowHumanTest(TestCase):
    start_url = reverse("welcomeworkflow:start")

    def test_start__get(self):
        response = self.client.get(self.start_url)
        self.assertEqual(response.status_code, 200)

    def test_start__post_with_user(self):
        user = get_user_model().objects.create(
            email="spiderman@avengers.com",
            first_name="Peter",
            last_name="Parker",
            username="spidy",
        )

        response = self.client.post(self.start_url, data={"user": user.pk})
        self.assertEqual(response.status_code, 302)
        workflow = models.WelcomeWorkflow.objects.get()
        self.assertTrue(workflow.user)
        self.assertTrue(workflow.task_set.succeeded().filter(name="start").exists())

    def test_start__post_without_user(self):
        response = self.client.post(self.start_url)
        self.assertEqual(response.status_code, 302)
        workflow = models.WelcomeWorkflow.objects.get()
        self.assertFalse(workflow.user)
        self.assertTrue(workflow.task_set.succeeded().filter(name="start").exists())
