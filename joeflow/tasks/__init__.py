"""
A task defines the behavior or a process.

A task can be considered as a simple transaction that changes state of a process.
There are two types of tasks, human and machine tasks.
"""
from .human import *  # NoQA
from .machine import *  # NoQA

HUMAN = "human"
MACHINE = "machine"
