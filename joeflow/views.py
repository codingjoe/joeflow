from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404
from django.views import generic

from . import forms, models
from .contrib.reversion import RevisionMixin


class WorkflowTemplateNameViewMixin:
    name = None

    def get_template_names(self):
        names = [
            "%s/%s_%s.html"
            % (
                self.model._meta.app_label,
                self.model._meta.model_name,
                self.name,
            )
        ]
        names.extend(super().get_template_names())
        names.append(
            "%s/workflow%s.html"
            % (self.model._meta.app_label, self.template_name_suffix)
        )
        return names


class TaskViewMixin(WorkflowTemplateNameViewMixin, RevisionMixin):
    name = None
    path = ""
    """
    URL pattern postfix for task view.

    Should a task require custom arguments via URL, path
    can be set to provide a pattern postfix. e.G.::

        start = tasks.StartView(path="path/to/<other_pk>")

    """

    def __init__(self, **kwargs):
        self._instance_kwargs = kwargs
        super().__init__(**kwargs)

    def get_task(self):
        try:
            return get_object_or_404(
                models.Task,
                pk=self.kwargs["pk"],
                name=self.name,
                completed=None,
            )
        except KeyError:
            return models.Task(name=self.name, type=models.Task.HUMAN)

    def next_task(self):
        task = self.get_task()
        task.workflow = self.model._base_manager.get(
            pk=self.model._base_manager.get(pk=self.object.pk)
        )
        task.finish(self.request.user)
        task.start_next_tasks()

    def get_object(self, queryset=None):
        task = self.get_task()
        return task.workflow

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        self.next_task()
        return response

    def create_task(self, workflow, prev_task):
        """
        Return a new database instance of this task.

        The factory method should be overridden, to create custom database instances
        based on the task node's class, the workflow or the previous task.

        Note:
            This is not a view method, a request via ``self.request`` is not available.

        Args:
            workflow (joeflow.models.Workflow): Current workflow instance.
            prev_task (joeflow.models.Task): Instance of the previous Task.

        Returns:
            joeflow.models.Task: New task instance.

        """
        return workflow.task_set.create(
            name=self.name, type=self.type, workflow=workflow
        )


class WorkflowDetailView(WorkflowTemplateNameViewMixin, generic.DetailView):
    pass


class OverrideView(
    PermissionRequiredMixin,
    RevisionMixin,
    WorkflowTemplateNameViewMixin,
    generic.UpdateView,
):
    permission_required = "override"
    name = "override"
    form_class = forms.OverrideForm
    fields = "__all__"

    def get_form_class(self):
        return modelform_factory(self.model, form=self.form_class, fields=self.fields)

    @transaction.atomic()
    def form_valid(self, form):
        response = super().form_valid(form)
        form.start_next_tasks(self.request.user)
        return response
