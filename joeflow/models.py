import logging
import sys
import traceback
import types
import typing

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models, transaction
from django.db.models.base import ModelBase
from django.db.models.functions import Now
from django.urls import NoReverseMatch, path, reverse
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as t
from django.views import View
from django.views.generic.edit import BaseCreateView

from .conf import settings
from .typing import HUMAN, MACHINE
from .utils import NoDashDiGraph
from .views import StartViewMixin

logger = logging.getLogger(__name__)

__all__ = (
    "Workflow",
    "Task",
)


class WorkflowBase(ModelBase):
    """Set node names on the nodes."""

    def __new__(mcs, name, bases, attrs):
        edges = attrs.get("edges") or []
        klass = super().__new__(mcs, name, bases, attrs)
        nodes = set()
        for edge in edges:
            nodes |= set(edge)

        for name, func in attrs.items():
            try:
                if func in nodes:
                    node = getattr(klass, name)
                    node.name = name
                    node.type = getattr(node, "type", MACHINE)
                    node.workflow_cls = klass
            except TypeError:
                pass  # not a function
        if "override_view" in attrs and isinstance(klass.override_view, str):
            klass.override_view = import_string(klass.override_view)
        if "detail_view" in attrs and isinstance(klass.detail_view, str):
            klass.detail_view = import_string(klass.detail_view)
        return klass


class Workflow(models.Model, metaclass=WorkflowBase):
    """The `WorkflowState` object holds the state of a workflow instances.

    It is represented by a Django Model. This way all workflow states
    are persisted in your database.
    """

    id = models.BigAutoField(primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    rankdir = "LR"
    """Direction of the workflow's graph visualization."""

    task_set = GenericRelation(
        "joeflow.Task", object_id_field="_workflow_id", for_concrete_model=False
    )

    class Meta:
        permissions = [("override", t("Can override a workflow."))]

    def save(self, **kwargs):
        if self.pk:
            try:
                update_fields = kwargs["update_fields"]
            except KeyError:
                pass
            else:
                update_fields.append("modified")
        super().save(**kwargs)

    edges: list[tuple[typing.Any, typing.Any]] = None
    """
    Edges define the transitions between tasks.

    They are the glue that binds tasks together. Edges have no
    behavior but define the structure of a workflow.

    Returns:
        (list[tuple]):
            List of edges. An edge is represented by a tuple
            including start end end not of an edge.
    """

    override_view = "joeflow.views.OverrideView"
    detail_view = "joeflow.views.WorkflowDetailView"

    @classmethod
    def _wrap_view_instance(cls, name, view_instance):
        return type(view_instance).as_view(
            model=cls, name=name, **view_instance._instance_kwargs
        )

    @classmethod
    def get_nodes(cls):
        nodes = set()
        for edge in cls.edges:
            nodes |= set(edge)
        for node in nodes:
            yield node.name, node

    @classmethod
    def urls(cls):
        """Return all URLs to workflow related task and other special views.

        Example::

            from django.urls import path, include

            from . import models

            urlpatterns = [
                # …
                path('myworkflow/', include(models.MyWorkflow.urls())),
            ]

        Returns:
            tuple(list, str): Tuple containing aw list of URLs and the workflow namespace.

        """
        urls = []
        for name, node in cls.get_nodes():
            if isinstance(node, View):
                if isinstance(node, (BaseCreateView, StartViewMixin)):
                    route = f"{name}/"
                else:
                    route = f"{name}/<int:pk>/"
                urls.append(
                    path(
                        route + node.path,
                        cls._wrap_view_instance(name, node),
                        name=name,
                    )
                )
        if cls.detail_view:
            urls.append(
                path("<int:pk>/", cls.detail_view.as_view(model=cls), name="detail")
            )
        if cls.override_view:
            urls.append(
                path(
                    "<int:pk>/override",
                    cls.override_view.as_view(model=cls),
                    name="override",
                )
            )
        return urls, cls.get_url_namespace()

    @classmethod
    def get_node(cls, name: str):
        """Get node by name."""
        return dict(cls.get_nodes())[name]

    @classmethod
    def get_next_nodes(cls, prev_node):
        for start, end in cls.edges:
            if start.name == prev_node.name:
                yield end

    @classmethod
    def get_url_namespace(cls):
        return cls.__name__.lower()

    def get_absolute_url(self):
        """Return URL to workflow detail view."""
        return reverse(f"{self.get_url_namespace()}:detail", kwargs={"pk": self.pk})

    def get_override_url(self):
        """Return URL to workflow override view."""
        return reverse(f"{self.get_url_namespace()}:override", kwargs={"pk": self.pk})

    @classmethod
    def get_graph(cls, color="black"):
        """Return workflow graph.

        Returns:
            (graphviz.Digraph): Directed graph of the workflow.

        """
        graph = NoDashDiGraph()
        graph.attr("graph", rankdir=cls.rankdir)
        graph.attr(
            "node",
            _attributes={
                "fontname": "sans-serif",
                "shape": "rect",
                "style": "filled",
                "fillcolor": "white",
            },
        )
        for name, node in cls.get_nodes():
            node_style = "filled"
            if node.type == HUMAN:
                node_style += ", rounded"
            graph.node(name, style=node_style, color=color, fontcolor=color)

        for start, end in cls.edges:
            graph.edge(start.name, end.name, color=color)
        return graph

    @classmethod
    def get_graph_svg(cls):
        """Return graph representation of a model workflow as SVG.

        The SVG is HTML safe and can be included in a template, e.g.:

        .. code-block:: html

            <html>
            <body>
            <!--// other content //-->
            {{ workflow_class.get_graph_svg }}
            <!--// other content //-->
            </body>
            </html>

        Returns:
            (django.utils.safestring.SafeString): SVG representation of a running workflow.

        """
        graph = cls.get_graph()
        graph.format = "svg"
        return SafeString(graph.pipe(encoding="utf-8"))  # nosec

    get_graph_svg.short_description = t("graph")

    def get_instance_graph(self):
        """Return workflow instance graph."""
        graph = self.get_graph(color="#888888")

        names = dict(self.get_nodes()).keys()

        for task in self.task_set.filter(name__in=names):
            href = task.get_absolute_url()
            style = "filled"
            peripheries = "1"

            if task.type == HUMAN:
                style += ", rounded"
            if not task.completed:
                style += ", bold"
            if not task.child_task_set.all() and task.completed:
                peripheries = "2"
            graph.node(
                task.name,
                href=href,
                style=style,
                color="black",
                fontcolor="black",
                peripheries=peripheries,
            )
            for child in task.child_task_set.exclude(name="override"):
                graph.edge(task.name, child.name, color="black")

        for task in self.task_set.filter(name="override").prefetch_related(
            "parent_task_set", "child_task_set"
        ):
            label = f"override_{task.pk}"
            peripheries = "1"
            for parent in task.parent_task_set.all():
                graph.edge(parent.name, f"override_{task.pk}", style="dashed")
            for child in task.child_task_set.all():
                graph.edge(f"override_{task.pk}", child.name, style="dashed")
            if not task.child_task_set.all() and task.completed:
                peripheries = "2"
            graph.node(label, style="filled, rounded, dashed", peripheries=peripheries)

        for task in self.task_set.exclude(name__in=names).exclude(name="override"):
            style = "filled, dashed"
            peripheries = "1"
            if task.type == HUMAN:
                style += ", rounded"
            if not task.completed:
                style += ", bold"
            for parent in task.parent_task_set.all():
                graph.edge(parent.name, task.name, style="dashed")
            for child in task.child_task_set.all():
                graph.edge(task.name, child.name, style="dashed")
            if not task.child_task_set.all() and task.completed:
                peripheries = "2"
            graph.node(
                task.name,
                style=style,
                color="black",
                fontcolor="black",
                peripheries=peripheries,
            )

        return graph

    def get_instance_graph_svg(self, output_format="svg"):
        """Return graph representation of a running workflow as SVG.

        The SVG is HTML safe and can be included in a template, e.g.:

        .. code-block:: html

            <html>
            <body>
            <!--// other content //-->
            {{ object.get_instance_graph_svg }}
            <!--// other content //-->
            </body>
            </html>

        Returns:
            (django.utils.safestring.SafeString): SVG representation of a running workflow.

        """
        graph = self.get_instance_graph()
        graph.format = output_format
        return SafeString(graph.pipe(encoding="utf-8"))  # nosec

    get_instance_graph_svg.short_description = t("instance graph")

    def get_instance_graph_mermaid(self):
        """Return instance graph as Mermaid diagram syntax.

        This can be used with MermaidJS for client-side rendering in admin.

        Returns:
            (str): Mermaid diagram syntax for the instance graph.
        """
        lines = [f"graph {self.rankdir}"]
        node_styles = []
        edge_styles = {}  # Map of (start, end) -> style
        edge_list = []  # List to maintain order of edges

        names = dict(self.get_nodes()).keys()

        # Add all nodes from workflow definition (inactive/gray style)
        for name, node in self.get_nodes():
            node_id = name.replace(" ", "_")
            # Keep original name with spaces for label
            label = name.replace("_", " ")

            # Determine shape based on node type, quote IDs to handle reserved words
            if node.type == HUMAN:
                lines.append(f"    '{node_id}'({label})")
            else:
                lines.append(f"    '{node_id}'[{label}]")

            # Default gray styling for nodes not yet processed
            node_styles.append(
                f"    style '{node_id}' fill:#f9f9f9,stroke:#999,color:#999"
            )

        # Add edges from workflow definition with default gray style
        for start, end in self.edges:
            start_id = start.name.replace(" ", "_")
            end_id = end.name.replace(" ", "_")
            edge_key = (start_id, end_id)
            if edge_key not in edge_styles:
                edge_list.append(edge_key)
                edge_styles[edge_key] = "stroke:#999"

        # Process actual tasks to highlight active/completed states
        for task in self.task_set.filter(name__in=names):
            node_id = task.name.replace(" ", "_")

            # Active tasks (not completed) get bold black styling
            if not task.completed:
                node_styles.append(
                    f"    style '{node_id}' fill:#fff,stroke:#000,stroke-width:3px,color:#000"
                )
            else:
                # Completed tasks get normal black styling
                node_styles.append(
                    f"    style '{node_id}' fill:#fff,stroke:#000,stroke-width:2px,color:#000"
                )

            # Update edge styling for actual task connections (black style)
            for child in task.child_task_set.exclude(name="override"):
                child_id = child.name.replace(" ", "_")
                edge_key = (node_id, child_id)
                if edge_key not in edge_styles:
                    edge_list.append(edge_key)
                # Update styling to black (overrides gray)
                edge_styles[edge_key] = "stroke:#000,stroke-width:2px"

        # Handle override tasks
        for task in self.task_set.filter(name="override").prefetch_related(
            "parent_task_set", "child_task_set"
        ):
            override_id = f"override_{task.pk}"
            override_label = f"override {task.pk}"

            # Add override node with dashed style, quote ID
            lines.append(f"    '{override_id}'({override_label})")
            node_styles.append(
                f"    style '{override_id}' fill:#fff,stroke:#000,stroke-width:2px,stroke-dasharray:5 5,color:#000"
            )

            # Add dashed edges for override connections
            for parent in task.parent_task_set.all():
                parent_id = parent.name.replace(" ", "_")
                edge_key = (parent_id, override_id)
                if edge_key not in edge_styles:
                    edge_list.append(edge_key)
                edge_styles[edge_key] = "stroke:#000,stroke-dasharray:5 5"

            for child in task.child_task_set.all():
                child_id = child.name.replace(" ", "_")
                edge_key = (override_id, child_id)
                if edge_key not in edge_styles:
                    edge_list.append(edge_key)
                edge_styles[edge_key] = "stroke:#000,stroke-dasharray:5 5"

        # Handle obsolete/custom tasks (not in workflow definition)
        for task in self.task_set.exclude(name__in=names).exclude(name="override"):
            node_id = task.name.replace(" ", "_")
            # Keep original name with spaces for label
            label = task.name.replace("_", " ")

            # Determine shape based on node type, quote IDs
            if task.type == HUMAN:
                lines.append(f"    '{node_id}'({label})")
            else:
                lines.append(f"    '{node_id}'[{label}]")

            # Dashed styling for obsolete tasks
            if not task.completed:
                node_styles.append(
                    f"    style '{node_id}' fill:#fff,stroke:#000,stroke-width:3px,stroke-dasharray:5 5,color:#000"
                )
            else:
                node_styles.append(
                    f"    style '{node_id}' fill:#fff,stroke:#000,stroke-width:2px,stroke-dasharray:5 5,color:#000"
                )

            # Add dashed edges for obsolete task connections
            for parent in task.parent_task_set.all():
                parent_id = parent.name.replace(" ", "_")
                edge_key = (parent_id, node_id)
                if edge_key not in edge_styles:
                    edge_list.append(edge_key)
                edge_styles[edge_key] = "stroke:#000,stroke-dasharray:5 5"

            for child in task.child_task_set.all():
                child_id = child.name.replace(" ", "_")
                edge_key = (node_id, child_id)
                if edge_key not in edge_styles:
                    edge_list.append(edge_key)
                edge_styles[edge_key] = "stroke:#000,stroke-dasharray:5 5"

        # Add edges to output (using dotted arrow for dashed edges)
        for start_id, end_id in edge_list:
            style = edge_styles[(start_id, end_id)]
            if "dasharray" in style:
                # Use dotted arrow for dashed edges
                lines.append(f"    '{start_id}' -.-> '{end_id}'")
            else:
                # Use solid arrow for normal edges
                lines.append(f"    '{start_id}' --> '{end_id}'")

        # Add all styling at the end
        lines.extend(node_styles)

        # Add edge styling
        for idx, (start_id, end_id) in enumerate(edge_list):
            style = edge_styles[(start_id, end_id)]
            lines.append(f"    linkStyle {idx} {style}")

        return "\n".join(lines)

    def cancel(self, user=None):
        self.task_set.cancel(user)


def workflow_state_subclasses():
    from django.apps import apps

    apps.check_models_ready()
    query = models.Q()
    for workflow in get_workflows():
        opts = workflow._meta
        query |= models.Q(app_label=opts.app_label, model=opts.model_name)
    return query


class TasksQuerySet(models.query.QuerySet):
    def scheduled(self):
        return self.filter(status=self.model.SCHEDULED)

    def not_scheduled(self):
        return self.exclude(status=self.model.SCHEDULED)

    def succeeded(self):
        return self.filter(status=self.model.SUCCEEDED)

    def not_succeeded(self):
        return self.exclude(status=self.model.SUCCEEDED)

    def failed(self):
        return self.filter(status=self.model.FAILED)

    def canceled(self):
        return self.filter(status=self.model.CANCELED)

    def cancel(self, user=None):
        if user and not user.is_authenticated:
            user = None
        return self.update(
            status=self.model.CANCELED,
            completed_by_user=user,
            completed=Now(),
        )


class Task(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    _workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        db_column="workflow_id",
        editable=False,
    )
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        on_delete=models.CASCADE,
        editable=False,
        limit_choices_to=workflow_state_subclasses,
        related_name="joeflow_task_set",
    )
    workflow = GenericForeignKey(
        "content_type", "_workflow_id", for_concrete_model=False
    )

    name = models.CharField(max_length=255, db_index=True, editable=False)

    _type_choices = (
        (HUMAN, t(HUMAN)),
        (MACHINE, t(MACHINE)),
    )
    type = models.CharField(
        max_length=50,
        choices=_type_choices,
        editable=False,
        db_index=True,
    )

    parent_task_set = models.ManyToManyField(
        "self",
        related_name="child_task_set",
        editable=False,
        symmetrical=False,
    )

    FAILED = "failed"
    SUCCEEDED = "succeeded"
    SCHEDULED = "scheduled"
    CANCELED = "canceled"
    _status_choices = (
        (FAILED, t(FAILED)),
        (SUCCEEDED, t(SUCCEEDED)),
        (SCHEDULED, t(SCHEDULED)),
        (CANCELED, t(CANCELED)),
    )
    status = models.CharField(
        max_length=50,
        choices=_status_choices,
        default=SCHEDULED,
        editable=False,
        db_index=True,
    )

    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=t("assignees"),
        related_name="joeflow_assignee_task_set",
    )

    completed_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=t("completed by"),
        related_name="joeflow_completed_by_task_set",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)
    completed = models.DateTimeField(
        blank=True, null=True, editable=False, db_index=True
    )

    exception = models.TextField(blank=True)
    stacktrace = models.TextField(blank=True)

    objects = TasksQuerySet.as_manager()

    class Meta:
        ordering = ("-completed", "-created")
        get_latest_by = ("created",)
        permissions = (
            ("rerun", t("Can rerun failed tasks.")),
            ("cancel", t("Can cancel failed tasks.")),
        )
        default_manager_name = "objects"

    def __str__(self):
        return f"{self.name} ({self.pk})"

    def save(self, **kwargs):
        if self.pk:
            try:
                update_fields = kwargs["update_fields"]
            except KeyError as e:
                raise ValueError(
                    "You need to provide explicit 'update_fields' to avoid race conditions."
                ) from e
            else:
                update_fields.append("modified")
        super().save(**kwargs)

    def get_absolute_url(self):
        if self.completed:
            return  # completed tasks have no detail view
        url_name = f"{self.workflow.get_url_namespace()}:{self.name}"
        try:
            return reverse(url_name, kwargs={"pk": self.pk})
        except NoReverseMatch:
            return  # no URL was defined for this task

    @property
    def node(self):
        return getattr(type(self.workflow), self.name)

    def finish(self, user=None):
        self.completed = timezone.now()
        self.status = self.SUCCEEDED
        if user and not user.is_authenticated:
            user = None
        self.completed_by_user = user
        if self.pk:
            self.save(update_fields=["status", "completed", "completed_by_user"])
        else:
            self.save()

    def cancel(self, user=None):
        self.completed = timezone.now()
        self.status = self.CANCELED
        if user and not user.is_authenticated:
            user = None
        self.completed_by_user = user
        self.save(update_fields=["status", "completed", "completed_by_user"])

    def fail(self):
        self.completed = timezone.now()
        self.status = self.FAILED
        tb = traceback.format_exception(*sys.exc_info())
        self.exception = tb[-1].strip()
        self.stacktrace = "".join(tb)
        self.save(update_fields=["status", "exception", "stacktrace"])

    def enqueue(self, countdown=None, eta=None):
        """Schedule the tasks for execution.

        Args:
            countdown (int):
                Time in seconds until the time should be started.

            eta (datetime.datetime):
                Time at which the task should be started.

        Returns:
            celery.result.AsyncResult: Celery task result.

        """
        self.status = self.SCHEDULED
        self.completed = None
        self.exception = ""
        self.stacktrace = ""
        self.save(update_fields=["status", "completed", "exception", "stacktrace"])
        task_runner = import_string(settings.JOEFLOW_TASK_RUNNER)
        transaction.on_commit(
            lambda: task_runner(
                task_pk=self.pk,
                workflow_pk=self._workflow_id,
                countdown=countdown,
                eta=eta,
            )
        )

    def start_next_tasks(self, next_nodes: list = None):
        """Start new tasks following another tasks.

        Args:
            self (Task): The task that precedes the next tasks.
            next_nodes (list):
                List of nodes that should be executed next. This argument is
                optional. If no nodes are provided it will default to all
                possible edges.

        """
        if next_nodes is None:
            next_nodes = self.workflow.get_next_nodes(self.node)
        tasks = []
        for node in next_nodes:
            try:
                # Some nodes – like Join – implement their own method to create new tasks.
                task = node.create_task(self.workflow, self)
            except AttributeError:
                task = self.workflow.task_set.create(
                    name=node.name, type=node.type, workflow=self.workflow
                )
            task.parent_task_set.add(self)
            if callable(node):
                transaction.on_commit(task.enqueue)
            tasks.append(task)
        return tasks


def get_workflows() -> types.GeneratorType:
    """Return all registered workflows."""
    from django.apps import apps

    apps.check_models_ready()
    for model in apps.get_models():
        if issubclass(model, Workflow) and model is not Workflow and model.edges:
            yield model
    return  # empty generator


def get_workflow(name) -> Workflow | None:
    for workflow_cls in get_workflows():
        if (
            name.lower()
            == f"{workflow_cls._meta.app_label}.{workflow_cls.__name__}".lower()
        ):
            return workflow_cls
