.. _topic-urls:

URLs
====

Should you ever need to get the URL – like for a test – for a task you can use
Django's :func:`reverse<django.urls.reverse>`. All users follow a simple
pattern consisting of the process name (lowercase) and task name, e.g.:

.. code-block:: python

    >>> from django.urls import reverse
    >>> reverse("process_name:task_name", args=[task.pk])
    '/url/to/process/task/1'

All task URLs need the `.Task` primary key as an argument. There are some
special views that do not like the process detail and override view, e.g.:

.. code-block:: python

    >>> reverse('welcomeprocess:start')
    '/welcome/start/'
    >>> reverse('welcomeprocess:detail', args=[process.pk])
    '/welcome/1/'
    >>> reverse('welcomeprocess:override', args=[process.pk])
    '/welcome/1/override'

The first example does not need a primary key, since it is a
:class:`.StartView` and the process is not created yet. The latter two
examples are process related views. The need the :class:`.Process` primary key
as an argument.

.. note::
    The process detail view is also available via
    :meth:`.Process.get_absolute_url`. The override view is available via
    :meth:`.Process.get_override_url`.
