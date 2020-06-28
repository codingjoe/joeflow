"""Set of reusable human tasks."""
from django.views import generic

from joeflow.views import TaskViewMixin

__all__ = (
    "StartView",
    "UpdateView",
)


class StartView(TaskViewMixin, generic.CreateView):
    """
    Start a new workflow by a human with a view.

    Starting a workflow with a view allows users to provide initial data.

    Similar to Django's :class:`CreateView<django.views.generic.edit.CreateView>`
    but does not only create the workflow but also completes a tasks.
    """

    pass


class UpdateView(TaskViewMixin, generic.UpdateView):
    """
    Modify the workflow state and complete a human task.

    Similar to Django's :class:`UpdateView<django.views.generic.edit.UpdateView>`
    but does not only update the workflow but also completes a tasks.
    """

    pass
