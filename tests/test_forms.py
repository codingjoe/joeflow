from joeflow import forms
from tests.testapp.models import SimpleProcess


class TestOverrideForm:
    def test_get_next_task_nodes(self):
        class SimpleProcessForm(forms.OverrideForm):
            class Meta:
                model = SimpleProcess
                fields = "__all__"

        form = SimpleProcessForm({"next_tasks": ["end"]})
        assert form.is_valid()
        assert list(form.get_next_task_nodes()) == [SimpleProcess.end]

    def test_start_next_tasks(self, db, admin_user):
        process = SimpleProcess.start_method()
        assert process.task_set.scheduled().exists()

        class SimpleProcessForm(forms.OverrideForm):
            class Meta:
                model = SimpleProcess
                fields = "__all__"

        form = SimpleProcessForm({"next_tasks": ["end"]}, instance=process)
        assert form.is_valid()
        form.start_next_tasks()

        assert process.task_set.scheduled()[0].name == "end"

    def test_start_next_tasks__user(self, db, admin_user):
        process = SimpleProcess.start_method()
        assert process.task_set.scheduled().exists()

        class SimpleProcessForm(forms.OverrideForm):
            class Meta:
                model = SimpleProcess
                fields = "__all__"

        form = SimpleProcessForm({"next_tasks": ["end"]}, instance=process)
        assert form.is_valid()
        form.start_next_tasks(admin_user)

        assert process.task_set.canceled()[0].completed_by_user == admin_user
        assert (
            process.task_set.filter(name="override")[0].completed_by_user == admin_user
        )
        assert process.task_set.filter(name="override")[0].status == "succeeded"

    def test_start_next_tasks__no_next_task(self, db, admin_user):
        process = SimpleProcess.start_method()
        assert process.task_set.scheduled().exists()

        class SimpleProcessForm(forms.OverrideForm):
            class Meta:
                model = SimpleProcess
                fields = "__all__"

        form = SimpleProcessForm({"next_tasks": []}, instance=process)
        assert form.is_valid()
        form.start_next_tasks()

        assert not process.task_set.scheduled().exists()
