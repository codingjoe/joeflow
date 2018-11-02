"""
A task defines the behavior or a process.

A task can be considered as a simple transaction that changes state of a process.
There are two types of tasks, human and machine tasks.

Human tasks are represented by a Django :class:`View<django.views.generic.base.View>`.
A user can change the processes state via a Django form or a JSON API.

Machine tasks are represented by simple methods on the `Process` class. They
can change the state and perform any action you can think of. They can decide
which task to execute next (exclusive gateway) but also start or wait for multiple
other tasks (split/join gateways).

Furthermore tasks can implement things like sending emails or fetching data
from an 3rd party API. All tasks are executed asynchronously to avoid blocking
IO and locked to prevent raise conditions.
"""
from .machine import *  # NoQA
from .human import *  # NoQA

HUMAN = 'human'
MACHINE = 'machine'
