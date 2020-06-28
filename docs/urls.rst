.. _topic-urls:

URLs
====

Should you ever need to get the URL – like for a test – for a task you can use
Django's :func:`reverse<django.urls.reverse>`. All users follow a simple
pattern consisting of the workflow name (lowercase) and task name, e.g.:

.. code-block:: python

    >>> from django.urls import reverse
    >>> reverse("workflow_name:task_name", args=[task.pk])
    '/url/to/workflow/task/1'

All task URLs need the `.Task` primary key as an argument. There are some
special views that do not like the workflow detail and override view, e.g.:

.. code-block:: python

    >>> reverse('welcomeworkflow:start')
    '/welcome/start/'
    >>> reverse('welcomeworkflow:detail', args=[workflow.object.pk])
    '/welcome/1/'
    >>> reverse('welcomeworkflow:override', args=[workflow.object.pk])
    '/welcome/1/override'

The first example does not need a primary key, since it is a
:class:`.StartView` and the workflow is not created yet. The latter two
examples are workflow related views. The need the :class:`.WorkflowState` primary key
as an argument.

.. note::
    The workflow detail view is also available via
    :meth:`.Workflow.get_absolute_url`. The override view is available via
    :meth:`.Workflow.get_override_url`.
