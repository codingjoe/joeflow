import logging
import random
import sys
import traceback

import graphviz as gv
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models, transaction
from django.urls import path, reverse, NoReverseMatch
from django.utils import timezone
from django.utils.safestring import SafeString
from django.utils.translation import ugettext_lazy as t
from django.views.generic.edit import BaseCreateView

from galahad import views, celery, tasks
from .conf import settings

logger = logging.getLogger(__name__)

__all__ = (
    'Process',
    'Task',
)


class NoDashDiGraph(gv.Digraph):
    """Like `.graphviz.Digraph` but removes underscores from labels."""

    @staticmethod
    def _quote(identifier, *args, **kwargs):
        identifier = identifier.replace('_', ' ')
        return gv.lang.quote(identifier, *args, **kwargs)

    @staticmethod
    def _quote_edge(identifier):
        identifier = identifier.replace('_', ' ')
        return gv.lang.quote_edge(identifier)


class BaseProcess(models.base.ModelBase):
    """Set node names on the nodes."""

    def __new__(cls, name, bases, attrs, **kwargs):
        edges = attrs.get('edges') or tuple()
        klass = super().__new__(cls, name, bases, attrs, **kwargs)
        nodes = set()
        for edge in edges:
            nodes |= set(edge)

        for name, func in attrs.items():
            try:
                if func in nodes:
                    node = getattr(klass, name)
                    node.node_name = name
                    node.node_type = tasks.HUMAN if isinstance(node, views.TaskViewMixin) else tasks.MACHINE
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
    started = models.DateTimeField(auto_now_add=True, db_index=True)
    completed = models.DateTimeField(blank=True, null=True, editable=False, db_index=True)

    task_set = GenericRelation('galahad.Task', object_id_field='_process_id')

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

    manual_override = views.ManualOverrideView

    @classmethod
    def _wrap_view_instance(cls, name, view_instance):
        return type(view_instance).as_view(
            model=cls, node_name=name,
            **view_instance._instance_kwargs
        )

    @classmethod
    def get_nodes(cls):
        nodes = set()
        for edge in cls.edges:
            nodes |= set(edge)
        for node in nodes:
            yield node.node_name, node

    @classmethod
    def urls(cls):
        """
        Return all URLs to process related task and other special views.

        Examples:

        .. code-block:: python

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
                    route = '{name}/'.format(name=name)
                else:
                    route = '{name}/<pk>/'.format(name=name)
                urls.append(path(route, cls._wrap_view_instance(name, node), name=name))
        urls.extend((
            path('<pk>/', views.ProcessDetailView.as_view(model=cls),
                 name='detail'),
            path('<pk>/override', views.ManualOverrideView.as_view(model=cls), name='override'),
        ))
        return urls, cls.get_url_namespace()

    @classmethod
    def get_node(cls, name: str):
        """Get node by name."""
        return dict(cls.get_nodes())[name]

    @classmethod
    def get_next_nodes(cls, prev_node):
        for start, end in cls.edges:
            if start.node_name == prev_node.node_name:
                yield end

    def finish(self):
        self.completed = timezone.now()
        self.save(update_fields=['completed'])

    @classmethod
    def get_url_namespace(cls):
        return cls.__name__.lower()

    def get_absolute_url(self):
        """Return URL to process detail view."""
        return reverse('{}:detail'.format(self.get_url_namespace()), kwargs=dict(pk=self.pk))

    def get_override_url(self):
        """Return URL to process override view."""
        return reverse('{}:override'.format(self.get_url_namespace()), kwargs=dict(pk=self.pk))

    @classmethod
    def get_graph(cls, color='black'):
        """
        Return process graph.

        Returns:
            (graphviz.Digraph): Directed graph of the process.

        """
        graph = NoDashDiGraph()
        graph.attr('graph', rankdir='LR')
        graph.attr('node', dict(fontname='sans-serif', shape='rect', style='filled', fillcolor='white'))
        for name, node in cls.get_nodes():
            node_style = 'filled'
            if node.node_type == tasks.HUMAN:
                node_style += ', rounded'
            graph.node(name, style=node_style, color=color, fontcolor=color)

        for start, end in cls.edges:
            graph.edge(start.node_name, end.node_name)
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
        graph.format = 'svg'
        return SafeString(graph.pipe().decode('utf-8'))

    def get_instance_graph(self):
        """Return process instance graph."""
        graph = self.get_graph(color='#666666')

        for task in self.task_set.exclude(node_name='manual_override'):
            node = task.node
            href = task.get_absolute_url()
            style = 'filled'

            if node.node_type == tasks.HUMAN:
                style += ', rounded'
            if not task.completed:
                style += ', bold'
            graph.node(node.node_name, href=href, style=style, color='black', fontcolor='black')

        for task in self.task_set.filter(node_name='manual_override').prefetch_related(
            'parent_task_set', 'child_task_set'
        ):
            label = 'manual_override_%s' % task.pk
            graph.node(label, style='filled, rounded, dashed')
            for parent in task.parent_task_set.all():
                graph.edge(parent.node_name, 'manual_override_%s' % task.pk, style='dashed')
            for child in task.child_task_set.all():
                graph.edge('manual_override_%s' % task.pk, child.node_name, style='dashed')

        return graph

    def get_instance_graph_svg(self, output_format='svg'):
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
        return SafeString(graph.pipe().decode('utf-8'))


def process_subclasses():
    from django.apps import apps

    apps.check_models_ready()
    query = models.Q()
    for app_models in apps.all_models.values():
        for model in app_models.values():
            if issubclass(model, Process) and model is not Process:
                opts = model._meta
                query |= models.Q(app_label=opts.app_label, model=opts.model_name)
    return query


class TasksQuerySet(models.query.QuerySet):
    is_completed = models.Q(completed__isnull=False)
    is_failed = models.Q(failed__isnull=False)

    def scheduled(self):
        return self.filter(~(self.is_failed | self.is_completed))

    def succeeded(self):
        return self.filter(self.is_completed)

    def failed(self):
        return self.filter(self.is_failed)


class Task(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    _process = models.ForeignKey('galahad.Process', on_delete=models.CASCADE, db_column='process_id', editable=False)
    content_type = models.ForeignKey(
        'contenttypes.ContentType', on_delete=models.CASCADE,
        editable=False, limit_choices_to=process_subclasses,
        related_name='galahad_task_set',
    )
    process = GenericForeignKey('content_type', '_process_id')
    node_name = models.TextField(db_index=True, editable=False)
    parent_task_set = models.ManyToManyField('self', related_name='child_task_set', editable=False, symmetrical=False)

    assignees = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=t('assignees'), related_name='galahad_task_set')

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    completed = models.DateTimeField(blank=True, null=True, editable=False, db_index=True)
    failed = models.DateTimeField(blank=True, null=True, editable=False, db_index=True)

    exception = models.TextField(blank=True)
    stacktrace = models.TextField(blank=True)

    objects = TasksQuerySet.as_manager()

    def __str__(self):
        return '%s (%s)' % (self.node_name, self.pk)

    class Meta:
        ordering = ('-completed', '-created')
        get_latest_by = ('created',)
        permissions = (
            ('rerun', t('Can rerun failed tasks.')),
            ('override', t('Can override a process.')),
        )
        default_manager_name = 'objects'

    def get_absolute_url(self):
        if self.completed:
            return
        url_name = '{}:{}'.format(self.process.get_url_namespace(), self.node_name)
        try:
            return reverse(url_name, kwargs=dict(pk=self.pk))
        except NoReverseMatch:
            pass

    @property
    def node(self):
        return getattr(self.process, self.node_name)

    def finish(self):
        self.completed = timezone.now()
        if self.pk:
            self.save(update_fields=['completed'])
        else:
            self.save()

    def fail(self):
        self.failed = timezone.now()
        tb = traceback.format_exception(*sys.exc_info())
        self.exception = tb[-1].strip()
        self.stacktrace = "".join(tb)
        self.save(update_fields=['failed', 'exception', 'stacktrace'])

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
        return celery.task_wrapper.apply_async(
            args=(self.pk, self._process_id),
            countdown=countdown,
            eta=eta,
            queue=settings.GALAHAD_CELERY_QUEUE_NAME,
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
                task = self.process.task_set.create(node_name=node.node_name, completed=None, failed=None)
            task.parent_task_set.add(self)
            if callable(node):
                transaction.on_commit(task.enqueue)
            tasks.append(task)
        else:
            self.process.finish()
        return tasks
