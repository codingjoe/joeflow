from django.views import generic

from galahad.views import TaskViewMixin


class StartView(TaskViewMixin, generic.CreateView):
    pass


class TaskView(TaskViewMixin, generic.UpdateView):
    """Update view."""
    pass
