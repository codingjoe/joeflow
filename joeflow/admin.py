from django.contrib import admin, messages
from django.contrib.auth import get_permission_codename
from django.db import transaction
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as t

from . import forms, models
from .contrib.reversion import VersionAdmin

__all__ = ("WorkflowAdmin",)


def rerun(modeladmin, request, queryset):
    succeeded = queryset.succeeded().count()
    if succeeded:
        messages.warning(
            request,
            "Only failed tasks can be retried. %s tasks have been skipped" % succeeded,
        )
    counter = 0
    for obj in queryset.not_succeeded().iterator():
        obj.enqueue()
        counter += 1
    messages.success(request, "%s tasks have been successfully queued" % counter)


rerun.short_description = t("Rerun selected tasks")
rerun.allowed_permissions = ("rerun",)


def cancel(modeladmin, request, queryset):
    not_scheduled = queryset.not_scheduled().count()
    if not_scheduled:
        messages.warning(
            request,
            "Only scheduled tasks can be canceled. %s tasks have been skipped"
            % not_scheduled,
        )
    queryset.scheduled().cancel(request.user)
    messages.success(request, "Tasks have been successfully canceled")


cancel.short_description = t("Cancel selected tasks")
cancel.allowed_permissions = ("cancel",)


@admin.register(models.Task)
class TaskAdmin(VersionAdmin):
    def has_rerun_permission(self, request):
        opts = self.opts
        codename = get_permission_codename("rerun", opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_cancel_permission(self, request):
        opts = self.opts
        codename = get_permission_codename("cancel", opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def pretty_stacktrace(self, obj):
        return format_html('<pre class="readonly collapse">{}<pre>', obj.stacktrace)

    pretty_stacktrace.short_description = t("Traceback")

    def child_tasks(self, obj):
        return ", ".join(str(task) for task in obj.child_task_set.all().iterator())

    child_tasks.short_description = t("Child tasks")

    actions = (rerun, cancel)

    list_display = (
        "name",
        "status",
        "type",
        "content_type",
        "completed",
        "modified",
        "created",
    )

    readonly_fields = (
        "workflow",
        "name",
        "type",
        "parent_task_set",
        "child_tasks",
        "completed",
        "created",
        "modified",
        "exception",
        "pretty_stacktrace",
    )

    list_filter = (
        "status",
        "type",
        "content_type",
        "completed",
        "created",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "workflow",
                    "name",
                    "parent_task_set",
                    "child_tasks",
                    "completed",
                    "modified",
                    "created",
                    "exception",
                ),
            },
        ),
        (t("Traceback"), {"classes": ("collapse",), "fields": ("pretty_stacktrace",)}),
    )


class TaskInlineAdmin(admin.TabularInline):
    model = models.Task
    readonly_fields = [
        "name",
        "type",
        "assignees",
        "created",
        "completed",
        "completed_by_user",
        "status",
    ]
    fields = readonly_fields
    extra = 0
    can_delete = False
    show_change_link = True
    classes = ["collapse"]


class WorkflowAdmin(VersionAdmin):
    list_filter = (
        "modified",
        "created",
    )
    form = forms.OverrideForm

    def get_inlines(self, *args, **kwargs):
        return [*super().get_inlines(*args, **kwargs), TaskInlineAdmin]

    def get_readonly_fields(self, *args, **kwargs):
        return [
            "get_instance_graph_svg",
            *super().get_readonly_fields(*args, **kwargs),
            "modified",
            "created",
        ]

    @transaction.atomic()
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        form.start_next_tasks(request.user)
