from django.views import generic

from joeflow.views import TaskViewMixin


class StartView(TaskViewMixin, generic.CreateView):
    """Generic view to start/create a new process."""


class TaskView(TaskViewMixin, generic.UpdateView):
    """Generic human task to update a process' state."""
