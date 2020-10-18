=====
Inbox
=====

In a multi user workflow it can become handy to assign and reassign tasks and to have
some kind of inbox to keep track of incomplete tasks.

Automatic assignment
--------------------

To implement a default assignee you need to override implement your own
:meth:`create_task` method.


.. code-block:: python

    from joeflow import tasks


    class UpdateWithPrevUserView(tasks.UpdateView):

        def create_task(self, workflow, prev_task):
            """Assign a new task to the user who completed the previous task."""
            new_task = workflow.task_set.create(
                workflow=workflow,
                name=self.name,
                type=self.type,
            )
            if prev_task.completed_by_user:
                # If the previous tasks was a machine task, no user is set.
                new_task.assignees.add(prev_task.completed_by_user)
            return new_task


In this implementation the new task is assigned to the user who completed the previous
task. The current workflow and the previous task are always given :meth:`create_task`
method. Note, that a request is not available, since this method might not be called
within a view but in a machine task. The parent task relation must not be created as a
part of the :meth:`create_task` method.

API
===

.. automethod:: joeflow.views.TaskViewMixin.create_task
