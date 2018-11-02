from django.contrib import admin, messages
from django.contrib.auth import get_permission_codename
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as t

from . import models


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    @staticmethod
    def rerun(modeladmin, request, queryset):
        succeeded = queryset.succeeded().count()
        if succeeded:
            messages.warning(request, "Only failed tasks can be retried. %s tasks have been skipped" % succeeded)
        counter = 0
        for obj in queryset.filter(~queryset.is_completed).iterator():
            obj.enqueue()
            counter += 1
        messages.success(request, "%s tasks have been successfully queued" % counter)
    rerun.short_description = t('Rerun tasks')
    rerun.allowed_permissions = ('rerun',)

    def has_rerun_permission(self, request):
        opts = self.opts
        codename = get_permission_codename('rerun', opts)
        return request.user.has_perm('%s.%s' % (opts.app_label, codename))

    def pretty_stacktrace(self, obj):
        return format_html('<pre class="readonly collapse">{}<pre>', obj.stacktrace)
    pretty_stacktrace.short_description = t('Traceback')

    def child_tasks(self, obj):
        return ", ".join(str(task) for task in obj.child_task_set.all().iterator())
    child_tasks.short_description = t('Child tasks')

    actions = ('rerun',)

    list_display = (
        'content_type',
        'node_name',
        'completed',
        'failed',
    )

    readonly_fields = (
        'process',
        'node_name',
        'parent_task_set',
        'child_tasks',
        'completed',
        'failed',
        'exception',
        'pretty_stacktrace',
    )

    list_filter = (
        'completed',
        'failed',
        'content_type',
    )

    fieldsets = (
        (None, {
            'fields': ('process', 'node_name', 'parent_task_set', 'child_tasks', 'completed', 'failed', 'exception')
        }),
        (t('Traceback'), {
            'classes': ('collapse',),
            'fields': ('pretty_stacktrace',),
        }),
    )
