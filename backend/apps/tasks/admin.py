from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin
from unfold.decorators import display, action
from unfold.contrib.filters.admin import (
    ChoicesDropdownFilter,
    RelatedDropdownFilter,
    RangeDateFilter,
)

from apps.tasks.models import Task


@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = (
        "display_title",
        "project",
        "display_status",
        "display_priority",
        "display_assignees",
        "display_due_date",
        "created_at",
    )
    list_display_links = ("display_title",)

    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("priority", ChoicesDropdownFilter),
        ("project", RelatedDropdownFilter),
        ("created_by", RelatedDropdownFilter),
        ("due_date", RangeDateFilter),
    )

    search_fields = (
        "title",
        "description",
        "assignees__email",
        "assignees__username",
        "created_by__email",
        "created_by__username",
        "project__name",
    )

    autocomplete_fields = ("project", "created_by", "assignees")

    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Task Overview",
            {
                "fields": ("title", "project", "description"),
            },
        ),
        (
            "Status & Priority",
            {
                "fields": ("status", "priority", "due_date"),
            },
        ),
        (
            "Assignments & Authorship",
            {
                "fields": ("assignees", "created_by"),
            },
        ),
        (
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    actions = ["mark_as_done", "mark_as_in_progress", "mark_as_todo"]

    @display(description="Task Title", header=True)
    def display_title(self, obj):
        return [
            obj.title,
            f"Project: {obj.project.name if obj.project else 'N/A'}",
            None,
        ]

    @display(
        description="Status",
        ordering="status",
        label={
            Task.Status.TODO: "danger",
            Task.Status.IN_PROGRESS: "warning",
            Task.Status.DONE: "success",
        },
    )
    def display_status(self, obj):
        return obj.get_status_display()

    @display(
        description="Priority",
        ordering="priority",
        label={
            Task.Priority.LOW: "info",
            Task.Priority.MEDIUM: "primary",
            Task.Priority.HIGH: "warning",
            Task.Priority.CRITICAL: "danger",
        },
    )
    def display_priority(self, obj):
        return obj.get_priority_display()

    @display(description="Assignees")
    def display_assignees(self, obj):
        assignees = obj.assignees.all()
        if not assignees:
            return "Unassigned"
        return ", ".join([user.username or user.email for user in assignees])

    @display(description="Due Date", ordering="due_date")
    def display_due_date(self, obj):
        if not obj.due_date:
            return "-"
        if obj.due_date < timezone.now().date() and obj.status != Task.Status.DONE:
            return f"⚠️ {obj.due_date} (Overdue)"
        return str(obj.due_date)

    @action(description="Mark selected tasks as Done", icon="check_circle")
    def mark_as_done(self, request, queryset):
        updated = queryset.update(status=Task.Status.DONE)
        self.message_user(request, f"{updated} task(s) marked as Done.")

    @action(description="Mark selected tasks as In Progress", icon="pending")
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status=Task.Status.IN_PROGRESS)
        self.message_user(request, f"{updated} task(s) marked as In Progress.")

    @action(description="Mark selected tasks as To Do", icon="schedule")
    def mark_as_todo(self, request, queryset):
        updated = queryset.update(status=Task.Status.TODO)
        self.message_user(request, f"{updated} task(s) marked as To Do.")
