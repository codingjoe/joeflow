from joeflow import forms

from tests.testapp.workflows import SimpleWorkflow


class TestOverrideForm:
    def test_get_next_task_nodes(self):
        class SimpleWorkflowForm(forms.OverrideForm):
            class Meta:
                model = SimpleWorkflow
                fields = "__all__"

        form = SimpleWorkflowForm({"next_tasks": ["end"]})
        assert form.is_valid()
        assert list(form.get_next_task_nodes()) == [SimpleWorkflow.end]

    def test_start_next_tasks(self, db, admin_user):
        workflow = SimpleWorkflow.start_method()
        assert workflow.task_set.scheduled().exists()

        class SimpleWorkflowForm(forms.OverrideForm):
            class Meta:
                model = SimpleWorkflow
                fields = "__all__"

        form = SimpleWorkflowForm({"next_tasks": ["end"]}, instance=workflow)
        assert form.is_valid()
        form.start_next_tasks()

        assert workflow.task_set.scheduled()[0].name == "end"

    def test_start_next_tasks__user(self, db, admin_user):
        workflow = SimpleWorkflow.start_method()
        assert workflow.task_set.scheduled().exists()

        class SimpleWorkflowForm(forms.OverrideForm):
            class Meta:
                model = SimpleWorkflow
                fields = "__all__"

        form = SimpleWorkflowForm({"next_tasks": ["end"]}, instance=workflow)
        assert form.is_valid()
        form.start_next_tasks(admin_user)

        assert workflow.task_set.canceled()[0].completed_by_user == admin_user
        assert (
            workflow.task_set.filter(name="override")[0].completed_by_user == admin_user
        )
        assert workflow.task_set.filter(name="override")[0].status == "succeeded"

    def test_start_next_tasks__no_next_task(self, db, admin_user):
        workflow = SimpleWorkflow.start_method()
        assert workflow.task_set.scheduled().exists()

        class SimpleWorkflowForm(forms.OverrideForm):
            class Meta:
                model = SimpleWorkflow
                fields = "__all__"

        form = SimpleWorkflowForm({"next_tasks": []}, instance=workflow)
        assert form.is_valid()
        form.start_next_tasks()

        assert not workflow.task_set.scheduled().exists()
