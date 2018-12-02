Core Components
===============

Process
-------

The :class:`.Process` object holds the state of a workflow instances. It is represented
by a Django Model. This way all process states are persisted in your database.

Processes are also the vehicle for the other two components :class:`Tasks<Task>` and
`edges`.

Task
----

A task defines the behavior or a process. It can be considered as a simple
transaction that changes state of a process. There are two types of tasks,
human and machine tasks.

Human tasks are represented by a Django :class:`.View`. A user can change the processes
state via a Django form or a JSON API.

Machine tasks are represented by simple methods on the :class:`.Process` class. They
can change the state and perform any action you can think of. They can decide
which task to execute next (exclusive gateway) but also start or wait for multiple
other tasks (split/join gateways).

Furthermore tasks can implement things like sending emails or fetching data
from an 3rd party API. All tasks are executed asynchronously to avoid blocking
IO and locked to prevent raise conditions.

Edges
-----

Edges are the glue that binds tasks together. They define the transitions
between tasks. They are represented by a simple list of tuples. Edges have no
behavior but define the structure of a workflow.

Advanced Process API
--------------------

.. autoclass:: joeflow.models.Process
    :show-inheritance:
    :members:
        urls,
        get_absolute_url,
        get_override_url,
        get_graph_svg,
        get_instance_graph_svg

.. autoclass:: joeflow.models.Task
    :show-inheritance:
    :members:
        start_next_tasks,
        enqueue
