from django import forms
from django.utils.translation import gettext_lazy as t

from . import models


class OverrideForm(forms.ModelForm):
    next_tasks = forms.MultipleChoiceField(
        label=t("Next tasks"),
        choices=[],
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["next_tasks"].choices = [
            (name, name) for name in dict(self._meta.model.get_nodes()).keys()
        ]

    def get_next_task_nodes(self):
        names = self.cleaned_data["next_tasks"]
        for name in names:
            yield self._meta.model.get_node(name)

    def start_next_tasks(self, user=None):
        active_tasks = list(self.instance.task_set.filter(completed=None))
        for task in active_tasks:
            task.cancel(user)
        if active_tasks:
            parent_tasks = active_tasks
        else:
            try:
                parent_tasks = [self.instance.task_set.latest()]
            except models.Task.DoesNotExist:
                parent_tasks = []
        override_task = self.instance.task_set.create(
            name="override",
            type=models.Task.HUMAN,
        )
        override_task.parent_task_set.set(parent_tasks)
        override_task.finish(user=user)
        override_task.start_next_tasks(next_nodes=self.get_next_task_nodes())
