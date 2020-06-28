import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils.safestring import SafeString
from graphviz import Digraph

from joeflow.models import Task, Workflow
from joeflow.tasks import HUMAN, MACHINE, StartView
from tests.testapp import models, workflows


class TestWorkflowBase:
    def test_name(self):
        assert workflows.TestWorkflow.a.name == "a"
        assert workflows.TestWorkflow.b.name == "b"
        with pytest.raises(AttributeError):
            workflows.TestWorkflow.not_a_node.name

    def test_type(self):
        assert workflows.TestWorkflow.a.type == MACHINE
        assert workflows.TestWorkflow.b.type == HUMAN
        with pytest.raises(AttributeError):
            workflows.TestWorkflow.not_a_node.type

    def test_workflow_cls(self):
        assert workflows.TestWorkflow.a.workflow_cls == workflows.TestWorkflow
        assert workflows.TestWorkflow.b.workflow_cls == workflows.TestWorkflow
        with pytest.raises(AttributeError):
            workflows.TestWorkflow.not_a_node.workflow_cls


class TestWorkflow:
    @pytest.fixture()
    def state_model(self):
        yield models.TestWorkflowState

    def test_get_absolute_url(self, db):
        workflow = workflows.SimpleWorkflow.start_method()
        assert workflow.get_absolute_url() == f"/simple/{workflow.pk}/"

    def test_get_override_url(self, db):
        workflow = workflows.SimpleWorkflow.start_method()
        assert workflow.get_override_url() == f"/simple/{workflow.pk}/override"

    def test_get_nodes(self, state_model):
        class MyWorkflow(state_model, Workflow):
            a = lambda s, t: None
            b = lambda s, t: None
            c = lambda s, t: None
            d = lambda s, t: None
            edges = (
                (a, b),
                (b, c),
                (a, c),
            )

            class Meta:
                abstract = True

        assert dict(MyWorkflow.get_nodes()) == {
            "a": MyWorkflow.a,
            "b": MyWorkflow.b,
            "c": MyWorkflow.c,
        }

    def test_get_node(self, state_model):
        class MyWorkflow(state_model, Workflow):
            a = lambda s, t: None
            b = lambda s, t: None
            c = lambda s, t: None
            edges = ((a, b),)

            class Meta:
                abstract = True

        assert MyWorkflow.get_node("a") == MyWorkflow.a
        with pytest.raises(KeyError):
            MyWorkflow.get_node("c")

    def test_get_next_nodes(self, state_model):
        class MyWorkflow(state_model, Workflow):
            a = lambda s, t: None
            b = lambda s, t: None
            c = lambda s, t: None
            edges = (
                (a, b),
                (b, c),
                (a, c),
            )

            class Meta:
                abstract = True

        assert list(MyWorkflow.get_next_nodes(MyWorkflow.a)) == [
            MyWorkflow.b,
            MyWorkflow.c,
        ]

        assert list(MyWorkflow.get_next_nodes(MyWorkflow.b)) == [
            MyWorkflow.c,
        ]

        assert list(MyWorkflow.get_next_nodes(MyWorkflow.c)) == []

    def test_get_graph(self, fixturedir):
        graph = workflows.SimpleWorkflow.get_graph()
        assert isinstance(graph, Digraph)
        with open(str(fixturedir / "simpleworkflow.dot")) as fp:
            expected_graph = fp.read().splitlines()
        assert set(graph.body) == set(expected_graph[1:-1])

    def test_get_graph_svg(self, fixturedir):
        svg = workflows.SimpleWorkflow.get_graph_svg()
        assert isinstance(svg, SafeString)

    def test_get_instance_graph(self, db, fixturedir):
        wf = workflows.SimpleWorkflow.start_method()
        task_url = wf.task_set.get(name="save_the_princess").get_absolute_url()
        graph = wf.get_instance_graph()
        with open(str(fixturedir / "simpleworkflow_instance.dot")) as fp:
            assert set(graph.body) == set(
                fp.read().replace("{url}", task_url).splitlines()[1:-1]
            )

    def test_get_instance_graph__override(
        self, db, stub_worker, fixturedir, admin_client
    ):
        wf = workflows.SimpleWorkflow.start_method()
        url = reverse("simpleworkflow:override", args=[wf.pk])
        response = admin_client.post(url, data={"next_tasks": ["end"]})
        assert response.status_code == 302
        stub_worker.wait()
        task = wf.task_set.get(name="override")
        graph = wf.get_instance_graph()

        assert (
            f'\t"{task.name} {task.pk}" [peripheries=1 style="filled, rounded, dashed"]'
            in graph.body
        )
        assert (
            f'\t"save the princess" -> "{task.name} {task.pk}" [style=dashed]'
            in graph.body
        )
        assert f'\t"{task.name} {task.pk}" -> end [style=dashed]' in graph.body

    def test_get_instance_graph__obsolete(self, db, fixturedir, admin_client):
        workflow = workflows.SimpleWorkflow.objects.create()
        start = workflow.task_set.create(name="start_method", status=Task.SUCCEEDED)
        obsolete = workflow.task_set.create(name="obsolete", status=Task.SUCCEEDED)
        end = workflow.task_set.create(name="end", status=Task.SUCCEEDED)
        obsolete.parent_task_set.add(start)
        end.parent_task_set.add(obsolete)
        graph = workflow.get_instance_graph()

        assert (
            '\tobsolete [color=black fontcolor=black peripheries=1 style="filled, dashed, bold"]'
            in graph.body
        )
        assert '\t"start method" -> obsolete [style=dashed]' in graph.body
        assert "\tobsolete -> end [style=dashed]" in graph.body

    def test_get_instance_graph_svg(self, db, fixturedir):
        wf = workflows.SimpleWorkflow.start_method()
        svg = wf.get_instance_graph_svg()
        assert isinstance(svg, SafeString)

    def test_cancel(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        workflow.task_set.create()
        assert workflow.task_set.scheduled().exists()
        workflow.cancel()
        assert not workflow.task_set.scheduled().exists()
        assert workflow.task_set.latest().completed_by_user is None
        assert workflow.task_set.latest().completed

    def test_cancel__with_user(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        workflow.task_set.create()
        user = get_user_model().objects.create(
            email="spiderman@avengers.com",
            first_name="Peter",
            last_name="Parker",
            username="spidy",
        )
        workflow.cancel(user=user)
        assert workflow.task_set.latest().completed_by_user == user

    def test_cancel__with_anonymous_user(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        workflow.task_set.create()
        user = AnonymousUser()
        workflow.cancel(user=user)
        assert workflow.task_set.latest().completed_by_user is None

    def test_urls(self):
        patterns, namespace = workflows.SimpleWorkflow.urls()
        assert namespace == "simpleworkflow"
        names = {pattern.name for pattern in patterns}
        assert names == {
            "save_the_princess",
            "start_view",
            "override",
            "detail",
        }

    def test_urls__custom_path(self):
        patterns, namespace = workflows.SimpleWorkflow.urls()
        patterns = {pattern.pattern.describe() for pattern in patterns}
        assert "'start_view/custom/postfix/' [name='start_view']" in patterns

    def test_urls__no_override(self, state_model):
        class MyWorkflow(state_model):
            override_view = None
            start = StartView()
            end = lambda s: None

            edges = ((start, end),)

            class Meta:
                abstract = True

        patterns, namespace = MyWorkflow.urls()
        assert namespace == "myworkflow"
        names = {pattern.name for pattern in patterns}
        assert names == {
            "start",
            "detail",
        }

    def test_urls__no_detail(self, state_model):
        class MyWorkflow(state_model):
            detail_view = None
            start = StartView()
            end = lambda s: None

            edges = ((start, end),)

            class Meta:
                abstract = True

        patterns, namespace = MyWorkflow.urls()
        assert namespace == "myworkflow"
        names = {pattern.name for pattern in patterns}
        assert names == {
            "start",
            "override",
        }


class TestTaskQuerySet:
    def test_scheduled(self, db):
        workflow = models.SimpleWorkflowState.objects.create()
        task = workflow.task_set.create()
        workflow.task_set.create(status=Task.CANCELED)
        assert workflow.task_set.scheduled().get() == task

    def test_succeeded(self, db):
        workflow = models.SimpleWorkflowState.objects.create()
        task = workflow.task_set.create(status=Task.SUCCEEDED)
        workflow.task_set.create(status=Task.CANCELED)
        assert workflow.task_set.succeeded().get() == task

    def test_not_succeeded(self, db):
        workflow = models.SimpleWorkflowState.objects.create()
        task = workflow.task_set.create()
        workflow.task_set.create(status=Task.SUCCEEDED)
        assert workflow.task_set.not_succeeded().get() == task

    def test_failed(self, db):
        workflow = models.SimpleWorkflowState.objects.create()
        task = workflow.task_set.create(status=Task.FAILED)
        workflow.task_set.create(status=Task.CANCELED)
        assert workflow.task_set.failed().get() == task

    def test_canceled(self, db):
        workflow = models.SimpleWorkflowState.objects.create()
        task = workflow.task_set.create(status=Task.CANCELED)
        workflow.task_set.create()
        assert workflow.task_set.canceled().get() == task

    def test_cancel__with_user(self, db):
        workflow = models.SimpleWorkflowState.objects.create()
        workflow.task_set.create()
        user = get_user_model().objects.create(
            email="spiderman@avengers.com",
            first_name="Peter",
            last_name="Parker",
            username="spidy",
        )
        workflow.task_set.cancel(user=user)
        assert workflow.task_set.latest().completed_by_user == user

    def test_cancel__with_anonymous_user(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        workflow.task_set.create()
        user = AnonymousUser()
        workflow.task_set.cancel(user=user)
        assert workflow.task_set.latest().completed_by_user is None


class TestTask:
    def test_start_next_tasks__default(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        task = workflow.task_set.create(name="start_method", workflow=workflow)
        task.finish()
        tasks = task.start_next_tasks()
        assert len(tasks) == 1
        assert tasks[0].name == "save_the_princess"
        assert workflow.task_set.scheduled().get() == tasks[0]

    def test_start_next_tasks__specific_next_task(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        task = workflow.task_set.create(name="start_method")
        task.finish()
        tasks = task.start_next_tasks(next_nodes=[workflows.SimpleWorkflow.end])
        assert len(tasks) == 1
        assert tasks[0].name == "end"
        assert workflow.task_set.latest() == tasks[0]

    def test_start_next_tasks__multiple_next_tasks(self, db):
        workflow = workflows.SplitJoinWorkflow.objects.create()
        task = workflow.task_set.create(name="split")
        tasks = task.start_next_tasks(
            next_nodes=[
                workflows.SplitJoinWorkflow.batman,
                workflows.SplitJoinWorkflow.robin,
            ]
        )
        assert len(tasks) == 2

    def test_start_next_tasks__custom_task_creation(self, db):
        workflow = workflows.SplitJoinWorkflow.objects.create()
        task = workflow.task_set.create(name="batman")
        tasks = task.start_next_tasks(next_nodes=[workflows.SplitJoinWorkflow.join])
        join1 = tasks[0]

        task = workflow.task_set.create(name="robin")
        tasks = task.start_next_tasks(next_nodes=[workflows.SplitJoinWorkflow.join])
        assert tasks[0] == join1

    def test_fail(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        task = workflow.task_set.create()
        try:
            raise IOError("nope")
        except IOError:
            task.fail()

        assert task.status == task.FAILED
        assert task.exception == "OSError: nope"
        assert "Traceback (most recent call last):\n" in task.stacktrace
        assert '    raise IOError("nope")\n' in task.stacktrace
        assert "OSError: nope\n" in task.stacktrace

    def test_cancel(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        task = workflow.task_set.create()
        task.cancel()
        assert task.status == task.CANCELED
        assert task.completed_by_user is None
        assert task.completed

    def test_cancel__with_user(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        task = workflow.task_set.create()
        user = get_user_model().objects.create(
            email="spiderman@avengers.com",
            first_name="Peter",
            last_name="Parker",
            username="spidy",
        )
        task.cancel(user=user)
        assert task.completed_by_user == user

    def test_cancel__with_anonymous_user(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        task = workflow.task_set.create()
        user = AnonymousUser()
        task.cancel(user=user)
        assert task.completed_by_user is None

    def test_save__modified_date(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        task = workflow.task_set.create()
        modified_date = task.modified
        task.save(update_fields=[])
        task.refresh_from_db()
        assert task.modified > modified_date

    def test_save__no_update_fields(self, db):
        workflow = workflows.SimpleWorkflow.objects.create()
        task = workflow.task_set.create()
        with pytest.raises(ValueError) as e:
            task.save()
        assert (
            "You need to provide explicit 'update_fields'" " to avoid race conditions."
        ) in str(e.value)
