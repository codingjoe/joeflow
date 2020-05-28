import logging
import sys
import traceback

import graphviz as gv
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models, transaction
from django.db.models.functions import Now
from django.urls import NoReverseMatch, path, reverse
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.safestring import SafeString
from django.utils.translation import ugettext_lazy as t
from django.views.generic.edit import BaseCreateView

from . import tasks, utils, views
from .conf import settings

logger = logging.getLogger(__name__)

__all__ = (
    "Process",
    "Task",
)


class NoDashDiGraph(gv.Digraph):
    """Like `.graphviz.Digraph` but removes underscores from labels."""

    def __init__(self, *args, **kwargs):
        self._edges = []
        super().__init__(*args, **kwargs)

    def edge(self, tail_name, head_name, label=None, _attributes=None, **attrs):
        if not (tail_name, head_name) in self._edges:
            self._edges.append((tail_name, head_name))
            super().edge(
                tail_name, head_name, label=label, _attributes=_attributes, **attrs
            )

    @staticmethod
    def _quote(identifier, *args, **kwargs):
        """Remove underscores from labels."""
        identifier = identifier.replace("_", " ")
        return gv.lang.quote(identifier, *args, **kwargs)

    @staticmethod
    def _quote_edge(identifier):
        """Remove underscores from labels."""
        identifier = identifier.replace("_", " ")
        return gv.lang.quote_edge(identifier)


class BaseProcess(models.base.ModelBase):
    """Set node names on the nodes."""

    def __new__(cls, name, bases, attrs, **kwargs):
        edges = attrs.get("edges") or tuple()
        klass = super().__new__(cls, name, bases, attrs, **kwargs)
        nodes = set()
        for edge in edges:
            nodes |= set(edge)

        for name, func in attrs.items():
            try:
                if func in nodes:
                    node = getattr(klass, name)
                    node.name = name
                    node.type = (
                        tasks.HUMAN
                        if isinstance(node, views.TaskViewMixin)
                        else tasks.MACHINE
                    )
                    node.process_cls = klass
            except TypeError:
                pass
        return klass


class Process(models.Model, metaclass=BaseProcess):
    """
    The `Process` object holds the state of a workflow instances.

    It is represented by a Django Model. This way all process states
    are persisted in your database.

    Processes are also the vehicle for the other two components tasks and
    :attr:`.edges`.
    """

    id = models.BigAutoField(primary_key=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    task_set = GenericRelation("joeflow.Task", object_id_field="_process_id")

    class Meta:
        permissions = (("override", t("Can override a process.")),)

    edges = None
    """
    Edges define the transitions between tasks.

    They are the glue that binds tasks together. Edges have no
    behavior but define the structure of a workflow.

    Returns:
        (list[tuple]):
            List of edges. An edge is represented by a tuple
            including start end end not of an edge.
    """

    override_view = views.OverrideView
    detail_view = views.ProcessDetailView

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
        """
        Return all URLs to process related task and other special views.

        Example::

            from django.urls import path, include

            from . import models

            urlpatterns = [
                # …
                path('myprocess/', include(models.MyProcess.urls())),
            ]

        Returns:
            tuple(list, str): Tuple containing aw list of URLs and the process namespace.

        """
        urls = []
        for name, node in cls.get_nodes():
            if isinstance(node, views.TaskViewMixin):
                if isinstance(node, BaseCreateView):
                    route = "{name}/".format(name=name)
                else:
                    route = "{name}/<pk>/".format(name=name)
                urls.append(path(route, cls._wrap_view_instance(name, node), name=name))
        if cls.detail_view:
            urls.append(
                path("<pk>/", cls.detail_view.as_view(model=cls), name="detail")
            )
        if cls.override_view:
            urls.append(
                path(
                    "<pk>/override",
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
        """Return URL to process detail view."""
        return reverse(
            "{}:detail".format(self.get_url_namespace()), kwargs=dict(pk=self.pk)
        )

    def get_override_url(self):
        """Return URL to process override view."""
        return reverse(
            "{}:override".format(self.get_url_namespace()), kwargs=dict(pk=self.pk)
        )

    @classmethod
    def get_graph(cls, color="black"):
        """
        Return process graph.

        Returns:
            (graphviz.Digraph): Directed graph of the process.

        """
        graph = NoDashDiGraph()
        graph.attr("graph", rankdir="LR")
        graph.attr(
            "node",
            dict(
                fontname="sans-serif", shape="rect", style="filled", fillcolor="white"
            ),
        )
        for name, node in cls.get_nodes():
            node_style = "filled"
            if node.type == tasks.HUMAN:
                node_style += ", rounded"
            graph.node(name, style=node_style, color=color, fontcolor=color)

        for start, end in cls.edges:
            graph.edge(start.name, end.name)
        return graph

    @classmethod
    def get_graph_svg(cls):
        """
        Return graph representation of a model process as SVG.

        The SVG is HTML safe and can be included in a template, e.g.:

        .. code-block:: html

            <html>
            <body>
            <!--// other content //-->
            {{ process_class.get_graph_svg }}
            <!--// other content //-->
            </body>
            </html>

        Returns:
            (django.utils.safestring.SafeString): SVG representation of a running process.

        """
        graph = cls.get_graph()
        graph.format = "svg"
        return SafeString(graph.pipe().decode("utf-8"))  # nosec

    def get_instance_graph(self):
        """Return process instance graph."""
        graph = self.get_graph(color="#888888")

        names = dict(self.get_nodes()).keys()

        for task in self.task_set.filter(name__in=names):
            href = task.get_absolute_url()
            style = "filled"

            if task.type == tasks.HUMAN:
                style += ", rounded"
            if not task.completed:
                style += ", bold"
            graph.node(
                task.name, href=href, style=style, color="black", fontcolor="black"
            )

        for task in self.task_set.filter(name="override").prefetch_related(
            "parent_task_set", "child_task_set"
        ):
            label = "override_%s" % task.pk
            graph.node(label, style="filled, rounded, dashed")
            for parent in task.parent_task_set.all():
                graph.edge(parent.name, "override_%s" % task.pk, style="dashed")
            for child in task.child_task_set.all():
                graph.edge("override_%s" % task.pk, child.name, style="dashed")

        for task in self.task_set.exclude(name__in=names).exclude(name="override"):
            style = "filled, dashed"
            if task.type == tasks.HUMAN:
                style += ", rounded"
            if not task.completed:
                style += ", bold"
            graph.node(task.name, style=style, color="black", fontcolor="black")
            for parent in task.parent_task_set.all():
                graph.edge(parent.name, task.name, style="dashed")
            for child in task.child_task_set.all():
                graph.edge(task.name, child.name, style="dashed")

        return graph

    def get_instance_graph_svg(self, output_format="svg"):
        """
        Return graph representation of a running process as SVG.

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
            (django.utils.safestring.SafeString): SVG representation of a running process.

        """
        graph = self.get_instance_graph()
        graph.format = output_format
        return SafeString(graph.pipe().decode("utf-8"))  # nosec

    def save(self, **kwargs):
        if self.pk:
            try:
                update_fields = kwargs["update_fields"]
            except KeyError:
                pass
            else:
                update_fields.append("modified")
        super().save(**kwargs)

    def cancel(self, user=None):
        self.task_set.cancel(user)


def process_subclasses():
    from django.apps import apps

    apps.check_models_ready()
    query = models.Q()
    for model in utils.get_processes():
        opts = model._meta
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
            status=self.model.CANCELED, completed_by_user=user, completed=Now(),
        )


class Task(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    _process = models.ForeignKey(
        "joeflow.Process",
        on_delete=models.CASCADE,
        db_column="process_id",
        editable=False,
    )
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        on_delete=models.CASCADE,
        editable=False,
        limit_choices_to=process_subclasses,
        related_name="joeflow_task_set",
    )
    process = GenericForeignKey("content_type", "_process_id")

    name = models.TextField(db_index=True, editable=False)

    HUMAN = "human"
    MACHINE = "machine"
    _type_choices = (
        (HUMAN, t(HUMAN)),
        (MACHINE, t(MACHINE)),
    )
    type = models.TextField(choices=_type_choices, editable=False, db_index=True,)

    parent_task_set = models.ManyToManyField(
        "self", related_name="child_task_set", editable=False, symmetrical=False,
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
    status = models.TextField(
        choices=_status_choices, default=SCHEDULED, editable=False, db_index=True,
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
        return "%s (%s)" % (self.name, self.pk)

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
            return
        url_name = "{}:{}".format(self.process.get_url_namespace(), self.name)
        try:
            return reverse(url_name, kwargs=dict(pk=self.pk))
        except NoReverseMatch:
            pass

    @property
    def node(self):
        return getattr(self.process, self.name)

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
        """
        Schedule the tasks for execution.

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
                process_pk=self._process_id,
                countdown=countdown,
                eta=eta,
            )
        )

    @transaction.atomic()
    def start_next_tasks(self, next_nodes: list = None):
        """
        Start new tasks following another tasks.

        Args:
            self (Task): The task that precedes the next tasks.
            next_nodes (list):
                List of nodes that should be executed next. This argument is
                optional. If no nodes are provided it will default to all
                possible edges.

        """
        if next_nodes is None:
            next_nodes = self.process.get_next_nodes(self.node)
        tasks = []
        for node in next_nodes:
            try:
                # Some nodes – like Join – implement their own method to create new tasks.
                task = node.create_task(self.process)
            except AttributeError:
                task = self.process.task_set.create(name=node.name, type=node.type,)
            task.parent_task_set.add(self)
            if callable(node):
                transaction.on_commit(task.enqueue)
            tasks.append(task)
        return tasks
