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

Here is a little sample of what a process written with joeflow may look like::

    class WelcomeProcess(Process):
        user = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            blank=True, null=True,
        )

        start = tasks.StartView(fields=['user'])

        def has_user(self, task):
            if self.user_id is None:
                return []
            else:
                return [self.send_welcome_email]

        def send_welcome_email(self, task):
            self.user.email_user(
                subject='Welcome',
                message='Hello %s!' % self.user.get_short_name(),
            )

        edges = (
            (start, has_user),
            (has_user, send_welcome_email),
        )

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
embraces that fact. It allows uses to interrupt a process at any given point
and modify it's current state. All while tracking all changes. This allows
developers to automate the main cases and users handle manually exceptions.
This allows you businesses to ship prototypes and MVPs of workflows.
Improvements can be shipped in multiple iterations without disrupting the
business.

People
------

Joeflow is build with all users in mind. Managers should be able to develop
better processes. Users should able to interact with the tasks every single
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
