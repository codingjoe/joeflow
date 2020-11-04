.. _tutorial-workflow:

Writing your first Workflow
===========================

As an example we will create a simple workflow that sends a welcome email to a
user. A human selects the user (or leaves the field blank). If the user is set
a welcome emails is being sent. If the user is blank no email will be send and
the workflow will end right way.

.. graphviz::

    digraph {
        graph [rankdir=LR]
        node [fillcolor=white fontname="Georgia, serif" shape=rect style=filled]
        start [color=black fontcolor=black style="filled, rounded"]
        "send welcome email" [color=black fontcolor=black style=filled]
        end [color=black fontcolor=black style=filled]
        "has user" [color=black fontcolor=black style=filled]
        start -> "has user"
        "has user" -> end
        "has user" -> "send welcome email"
        "send welcome email" -> end
    }

Let's start with the data structure or workflow state. We need a model that can
store a user. Like so:

.. code-block:: python

    from django.conf import settings
    from joeflow.models import Workflow


    class WelcomeWorkflow(Workflow):
        # state
        user = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            blank=True, null=True,
        )

Next we add the behavior:

.. code-block:: python

    from django.conf import settings
    from joeflow import tasks
    from joeflow.models import Workflow


    class WelcomeWorkflow(Workflow):
        # state
        user = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            blank=True, null=True,
        )

        # behavior
        start = tasks.StartView(fields=["user"])

        def has_user(self):
            if self.user:
                return [self.send_welcome_email]
            else:
                return [self.end]

        def send_welcome_email(self):
            self.user.email_user(
                subject="Welcome", message="Hello %s!" % self.user.get_short_name(),
            )

        def end(self):
            pass

        edges = [
            (start, has_user),
            (has_user, end),
            (has_user, send_welcome_email),
            (send_welcome_email, end),
        ]


We have the tasks ``start``, ``has_user`` ``send_welcome_email`` and ``end``
on the top and define all the edges on the bottom. Edges are defined by a
set of tuples. Edges are directed, meaning the first item in the tuple is
the start tasks and the second item the end tasks.

Note that the ``has_user`` task has two different return values. A task
can return a list of following or child tasks. This is how your workflow
can take different paths. If there is no return value, it will simply
follow all possible edges defined in ``edges``.

The ``end`` task, does not really do anything. It is also not really needed.
It is just added for readability and could be omitted. Any tasks that does
not have a child task defined in ``edges`` or returns an empty list is
considered a workflow end.

To make your workflow available to users you will need to add the workflow URLs
to your ``urls.py``:

.. code-block:: python

    from django.urls import path, include

    from . import models

    urlpatterns = [
        # …
        path('welcome/', include(models.WelcomeWorkflow.urls())),
    ]

This will add URLs for all human tasks as well as a detail view and manual
override view. We will get to the last one later.

That it all the heavy lifting is done. In the next part of tutorial you will
learn
:ref:`how to integrate the tasks into your templates<tutorial-templates>`.
