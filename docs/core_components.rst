Core Components
===============

Workflow
--------

The :class:`.Workflow` is where all your components come together.
It defines the flow overall flow and the different states of your workflow.
Workflow are also the vehicle for the other two components :class:`Tasks<Task>` and
`edges`.

It combines both behavior and state using familiar components.
The state is persisted via a Django :class:`.Model` for each
instance of your workflow.

Task
----

A task defines the behavior of a workflow. It can be considered as a simple
transaction that changes state of a workflow. There are two types of tasks,
human and machine tasks.

Human tasks are represented by a Django :class:`.View`. A user can change the workflows
state via a Django form or a JSON API.

Machine tasks are represented by simple methods on the :class:`.Workflow` class. They
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

Advanced Workflow API
---------------------

.. autoclass:: joeflow.models.Workflow
    :show-inheritance:
    :members:
        urls,
        get_graph_svg,
        get_instance_graph_svg,
        get_absolute_url,
        get_override_url

.. autoclass:: joeflow.models.Task
    :show-inheritance:
    :members:
        start_next_tasks,
        enqueue
