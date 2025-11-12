"""A task defines the behavior or a workflow.

A task can be considered as a simple transaction that changes state of a workflow.
There are two types of tasks, human and machine tasks.
"""

from joeflow.typing import *  # NoQA

from .human import *  # NoQA
from .machine import *  # NoQA
