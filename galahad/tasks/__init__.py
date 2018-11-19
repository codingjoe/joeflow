"""
A task defines the behavior or a process.

A task can be considered as a simple transaction that changes state of a process.
There are two types of tasks, human and machine tasks.
"""
from .machine import *  # NoQA
from .human import *  # NoQA

HUMAN = 'human'
MACHINE = 'machine'
