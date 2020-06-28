.. _tutorial-testing:

Testing your workflow
=====================

Joeflow is designed to make testing as simple as possible. Machine tasks are
the simplest to test. You just call the method on the workflow. Following our
example, your tests could looks something like this:


.. code-block:: python

    from django.contrib.auth import get_user_model
    from django.core import mail
    from django.test import SimpleTestCase, TestCase
    from django.urls import reverse

    from . import workflows


    class WelcomeWorkflowMachineTest(SimpleTestCase):
        def test_has_user__with_user(self):
            user = get_user_model()(
                email="spiderman@avengers.com",
                first_name="Peter",
                last_name="Parker",
                username="spidy",
            )
            workflow = workflows.WelcomeWorkflow(user=user)
            self.assertEqual(workflow.has_user(), [workflow.send_welcome_email])

        def test_has_user__without_user(self):
            workflow = workflows.WelcomeWorkflow()
            self.assertEqual(workflow.has_user(), [workflow.end])

        def test_send_welcome_email(self):
            user = get_user_model()(
                email="spiderman@avengers.com",
                first_name="Peter",
                last_name="Parker",
                username="spidy",
            )
            workflow = workflows.WelcomeWorkflow(user=user)

            workflow.send_welcome_email()

            email = mail.outbox[-1]
            self.assertEqual(email.subject, "Welcome")
            self.assertEqual(email.body, "Hello Peter!")
            self.assertIn("spiderman@avengers.com", email.to)


The tests above a regular unit tests covering the machine tasks. Testing the
human tasks is similarly simple. Since machine tasks are nothing but views
you can use Django's test :class:`Client<django.test.Client>`. Here an
example:

.. code-block:: python

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

            response = self.client.post(self.start_url, data=dict(user=user.pk))
            self.assertEqual(response.status_code, 302)
            workflow = workflows.WelcomeWorkflow.objects.get()
            self.assertTrue(workflow.user)
            self.assertTrue(workflow.task_set.succeeded().filter(name="start").exists())

        def test_start__post_without_user(self):
            response = self.client.post(self.start_url)
            self.assertEqual(response.status_code, 302)
            workflow = workflows.WelcomeWorkflow.objects.get()
            self.assertFalse(workflow.user)
            self.assertTrue(workflow.task_set.succeeded().filter(name="start").exists())

Note that the start task is somewhat special, since it does not need a
running workflow. You can test any other task by simply creating the
workflow and task in during test setup. In those cases you will need
pass the task primary key. You can find more information about this
in the :ref:`URLs documentation<topic-urls>`.

