from joeflow import tasks


class UpdateWithPrevUserView(tasks.UpdateView):
    def create_task(self, workflow, prev_task):
        """Assign a new task to the user who completed the previous task."""
        new_task = workflow.task_set.create(
            workflow=workflow,
            name=self.name,
            type=self.type,
        )
        if prev_task.completed_by_user:
            # If the previous tasks was a machine task, no user is set.
            new_task.assignees.add(prev_task.completed_by_user)
        return new_task
