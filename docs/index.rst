=======
joeflow
=======

**The lean workflow automation framework for machines with heart.**

.. image:: img/pexels-photo-1020325.jpeg
   :alt: a hand drawn robot

Joeflow is a free workflow automation framework designed to bring simplicity
to complex workflows. Joeflow written in Python_ based on the world famous
Django_ web framework.

.. _Python: https://python.org
.. _Django: https://www.djangoproject.com/

Here is a little sample of what a workflow or process written with joeflow
may look like:

.. graphviz::

    digraph {
        graph [rankdir=LR]
        node [fillcolor=white fontname="sans-serif" shape=rect style=filled]
        checkout [color=black fontcolor=black style="filled, rounded"]
        "has email" [color=black fontcolor=black style=filled]
        ship [color=black fontcolor=black style="filled, rounded"]
        end [color=black fontcolor=black style=filled peripheries=2]
        "send tracking code" [color=black fontcolor=black style=filled]
        checkout -> ship
        ship -> "has email"
        "has email" -> "send tracking code"
        "has email" -> end [color="#888888"]
        "send tracking code" -> end
    }

.. code-block:: python

    from django.core.mail import send_mail
    from jowflow.models import Workflow
    from joeflow import tasks


    class ShippingWorkflow(Workflow):

        # model fields to store the state
        email = models.EmailField(blank=True)
        shipping_address = models.TextField()
        tracking_code = models.TextField()

        # tasks (nodes)
        checkout = tasks.StartView(fields=["shipping_address", "email"])

        ship = tasks.UpdateView(fields=["tracking_code"])

        def has_email(self, task):
            if self.email:
                return [self.send_tracking_code]

        def send_tracking_code(self):
            send_mail(
                subject="Your tracking code",
                message=self.tracking_code,
                from_email=None,
                recipient_list=[self.email],
            )

        def end(self):
            pass

        # edges
        edges = [
            (checkout, ship),
            (ship, has_email),
            (has_email, send_tracking_code),
            (has_email, end),
            (send_tracking_code, end),
        ]

Design Principles
=================

Common sense is better than convention
--------------------------------------

Joeflow does not follow any academic modeling notation developed by a poor PhD
student who actually never worked a day in their life. Businesses are already
complex which is why Joeflow is rather simple. There are only two types of
tasks – human & machine – as well as edges to connect them. It's so simple a
toddler (or your CEO) could design a workflow.

Lean Automation (breaking the rules)
------------------------------------

Things don't always go according to plan especially when humans are involved.
Even the best workflow can't cover all possible edge cases. Joeflow
embraces that fact. It allows uses to interrupt a workflow at any given point
and modify it's current state. All while tracking all changes. This allows
developers to automate the main cases and users handle manually exceptions.
This allows you businesses to ship prototypes and MVPs of workflows.
Improvements can be shipped in multiple iterations without disrupting the
business.

People
------

Joeflow is build with all users in mind. Managers should be able to develop
better workflows. Users should able to interact with the tasks every single
day. And developers should be able to rapidly develop and test new features.

Free
----

Joeflow is open source and collaboratively developed by industry leaders in
automation and digital innovation.

All Contents
============

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :glob:

   tutorial/index
   core_components
   tasks
   settings
   *

*Photo by rawpixel.com from Pexels*
