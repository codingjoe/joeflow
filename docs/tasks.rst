=====
Tasks
=====

.. automodule:: joeflow.tasks
    :members:

Human
-----

Human tasks are represented by a Django :class:`View<django.views.generic.base.View>`.

A user can change the workflows state via a Django form or a JSON API.
Anything you can do in a view you can do in a human task. They only
difference to machine tasks is that they require some kind of interaction.

You can use view mixins like the
:class:`PermissionRequiredMixin<django.contrib.auth.mixins.PermissionRequiredMixin>`
or
:class:`LoginRequiredMixin<django.contrib.auth.mixins.LoginRequiredMixin>`
to create your own tasks that are only available to certain users.

Generic human tasks
~~~~~~~~~~~~~~~~~~~

.. automodule:: joeflow.tasks.human
    :members:

Machine
-------

Machine tasks are represented by simple methods on the :class:`.Workflow` class.

They can change the state and perform any action you can think of. They can
decide which task to execute next (exclusive gateway) but also start or wait
for multiple other tasks (split/join gateways).

Furthermore tasks can implement things like sending emails or fetching data
from an 3rd party API. All tasks are executed asynchronously to avoid blocking
IO and locked to prevent raise conditions.

Return values
~~~~~~~~~~~~~

Machine tasks have three different allowed return values all of which will
cause the workflow to behave differently:

:class:`None`:
    If a task returns ``None`` or anything at all the workflow will just
    proceed as planed and follow all outgoing edges and execute the next
    tasks.

:class:`Iterable`:
    A task can return also an explicit list of tasks that should be executed
    next. This can be used to create exclusive gateways::

        from django.utils import timezone
        from joeflow.workflows import Workflow
        from joeflow import tasks


        class ExclusiveWorkflow(Workflow):
            start = tasks.Start()

            def is_workday(self):
                if timezone.localtime().weekday() < 5:
                    return [self.work]
                else:
                    return [self.chill]

            def work(self):
                # pass time at the water cooler
                pass

            def chill(self):
                # enjoy life
                pass

            edges = (
                (start, is_workday),
                (is_workday, work),
                (is_workday, chill),
            )

    A task can also return am empty list. This will cause the workflow branch
    to come to a halt and no further stats will be started.

    .. warning::
        A task can not be a generator (*yield* results).

:class:`False`:
    A task can also return a boolean. Should a task return ``False`` the
    workflow will wait until the condition changes to ``True`` (or anything but
    ``False``)::

        from joeflow import tasks
        form joeflow.workflows import Workflow
        from django.utils import timezone


        class WaitingWorkflow(Workflow):
            start = tasks.Start()

            def wait_for_weekend(self):
                return timezone.now().weekday() >= 5

            def go_home(self):
                # enjoy life
                pass

            edges = (
                (start, wait_for_weekend),
                (wait_for_weekend, go_home),
            )

Exceptions
~~~~~~~~~~

Should a task raise an exception the tasks will change it status to failed.
The exception that caused the task to fail will be recorded on the task
itself and further propagated. You can find and rerun failed tasks form
Django's admin interface.

Generic machine tasks
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: joeflow.tasks.machine
    :members:
