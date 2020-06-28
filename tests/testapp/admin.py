from django.contrib import admin

from joeflow.admin import WorkflowAdmin

from . import workflows

admin.site.register(workflows.SimpleWorkflow, WorkflowAdmin)
admin.site.register(workflows.SplitJoinWorkflow, WorkflowAdmin)
admin.site.register(workflows.LoopWorkflow, WorkflowAdmin)
