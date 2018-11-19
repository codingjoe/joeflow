# Galahad

**The lean workflow automation framework for machines with heart.**

Galahad is a free workflow automation framework designed to bring simplicity
to complex workflows.


## Design

### Principles 

#### Common sense is better than convention

Galahad does not follow any academic modeling notation developed by a poor Phd
student who actually never worked a day in their life. Businesses are already
complex which is why Galahad is rather simple. There are only two types of
tasks – human & machine – as well as edges to connect them. It's so simple a
toddler (or your CEO) could design a workflow.

#### Lean Automation (breaking the rules)

Things don't always go according to plan especially when humans are involved.
Even the best workflow can't cover all possible edge cases. Galahad
embraces that fact. It allows uses to interrupt a process at any given point
and modify it's current state. All while tracking all changes. This allows
developers to automate the main cases and users handle manually exceptions.
This allows you businesses to ship prototypes and MVPs of workflows.
Improvements can be shipped in multiple iterations without disrupting the
business.

#### People

Galahad is build with all users in mind. Managers should be able to develop
better processes. Users should able to interact with the tasks every single
day. And developers should be able to rapidly develop and test new features.

## Core Components

### Process

The `Process` object holds the state of a workflow instances. It is represented
by a Django Model. This way all process states are persisted in your database.

Processes are also the vehicle for the other two components `Tasks` and
`edges`.

### Task

A task defines the behavior or a process. It can be considered as a simple
transaction that changes state of a process. There are two types of tasks,
human and machine tasks.

Human tasks are represented by Django `View`s. A user can change the processes
state via a Django form or a JSON API. 

Machine tasks are represented by simple methods on the `Process` class. They
can change the state and perform any action you can think of. They can decide
which task to execute next (exclusive gateway) but also start or wait for multiple
other tasks (split/join gateways).

Furthermore tasks can implement things like sending emails or fetching data
from an 3rd party API. All tasks are executed asynchronously to avoid blocking
IO and locked to prevent raise conditions.

### Edges

Edges are the glue that binds tasks together. They define the transitions
between tasks. They are represented by a simple list of tuples. Edges have no
behavior but define the structure of a workflow.
