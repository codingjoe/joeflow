from django.contrib import admin, messages
from django.contrib.auth import get_permission_codename
from django.db import transaction
from django.forms.widgets import Media, MediaAsset, Script
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as t

from . import forms, models
from .contrib.reversion import VersionAdmin

__all__ = ("WorkflowAdmin",)


@admin.action(
    description=t("Rerun selected tasks"),
    permissions=("rerun",),
)
def rerun(modeladmin, request, queryset):
    succeeded = queryset.succeeded().count()
    if succeeded:
        messages.warning(
            request,
            f"Only failed tasks can be retried. {succeeded} tasks have been skipped",
        )
    counter = 0
    for obj in queryset.not_succeeded().iterator():
        obj.enqueue()
        counter += 1
    messages.success(request, f"{counter} tasks have been successfully queued")


@admin.action(
    description=t("Cancel selected tasks"),
    permissions=("cancel",),
)
def cancel(modeladmin, request, queryset):
    not_scheduled = queryset.not_scheduled().count()
    if not_scheduled:
        messages.warning(
            request,
            f"Only scheduled tasks can be canceled. {not_scheduled} tasks have been skipped",
        )
    queryset.scheduled().cancel(request.user)
    messages.success(request, "Tasks have been successfully canceled")


@admin.register(models.Task)
class TaskAdmin(VersionAdmin):
    def has_rerun_permission(self, request):
        opts = self.opts
        codename = get_permission_codename("rerun", opts)
        return request.user.has_perm(f"{opts.app_label}.{codename}")

    def has_cancel_permission(self, request):
        opts = self.opts
        codename = get_permission_codename("cancel", opts)
        return request.user.has_perm(f"{opts.app_label}.{codename}")

    @admin.display(description=t("Traceback"))
    def pretty_stacktrace(self, obj):
        return format_html('<pre class="readonly collapse">{}<pre>', obj.stacktrace)

    @admin.display(description=t("Child tasks"))
    def child_tasks(self, obj):
        return ", ".join(str(task) for task in obj.child_task_set.all().iterator())

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


class CSS(MediaAsset):
    element_template = "<style{attributes}>{path}</style>"

    @property
    def path(self):
        return mark_safe(self._path)  # noqa: S308


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
            "display_workflow_diagram",
            *super().get_readonly_fields(*args, **kwargs),
            "modified",
            "created",
        ]

    @admin.display(description="Workflow Diagram")
    def display_workflow_diagram(self, obj):
        """Display workflow diagram using MermaidJS for client-side rendering."""
        if obj.pk:
            return mark_safe(  # noqa: S308
                f"""<pre class="mermaid" style="width: 100%; display: block">{obj.get_instance_graph_mermaid()}</pre>"""
            )
        return ""

    @transaction.atomic()
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        form.start_next_tasks(request.user)

    @property
    def media(self):
        return super().media + Media(
            js=[
                Script(
                    "https://cdn.jsdelivr.net/npm/mermaid@latest/dist/mermaid.esm.min.mjs",
                    type="module",
                )
            ],
            css={
                "all": [
                    CSS(
                        ".field-display_workflow_diagram .flex-container > .readonly { flex: 1 }"
                    )
                ]
            },
        )
