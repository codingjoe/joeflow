from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404
from django.views import generic

from . import forms, models
from .contrib.reversion import RevisionMixin
from .typing import HUMAN


class WorkflowTemplateNameViewMixin:
    name = None

    def get_template_names(self):
        names = [
            f"{self.model._meta.app_label}/{self.model._meta.model_name}_{self.name}.html"
        ]
        names.extend(super().get_template_names())
        names.append(
            f"{self.model._meta.app_label}/workflow{self.template_name_suffix}.html"
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
    type = HUMAN

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
            return models.Task(name=self.name, type=HUMAN)

    def next_task(self):
        task = self.get_task()
        task.workflow = self.model._base_manager.get(pk=self.object.pk)
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
        """Return a new database instance of this task.

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


class StartViewMixin(TaskViewMixin):
    """View-mixin to create a start workflow.

    Example:
        class MyStartWorkflowView(StartViewMixin, View):
            def post(self, request, *args, **kwargs):
                try:
                    data = json.loads(request.body)
                    workflow_id = self.start_workflow(data)
                except Exception as e:
                    return HttpResponseBadRequest("Failed to start workflow")

                return JsonResponse({'message': 'Workflow started successfully.', 'id': workflow_id}, status=201)
    """

    model = None


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
