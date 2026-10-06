from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.contrib.filters.admin import RelatedDropdownFilter

from apps.projects.models import Project, ProjectMember


class ProjectMemberInline(TabularInline):
    model = ProjectMember
    extra = 1
    autocomplete_fields = ("user",)
    verbose_name_plural = "Project Members"
    tab = True


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    inlines = [ProjectMemberInline]

    list_display = (
        "display_name",
        "owner",
        "department",
        "display_members_count",
        "display_tasks_count",
        "created_at",
    )
    list_display_links = ("display_name",)

    search_fields = ("name", "description", "owner__email", "owner__username")
    list_filter = (
        ("department", RelatedDropdownFilter),
        ("owner", RelatedDropdownFilter),
    )
    autocomplete_fields = ("owner", "department")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Project Details",
            {
                "fields": ("name", "description"),
            },
        ),
        (
            "Ownership & Department",
            {
                "fields": ("owner", "department"),
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

    @display(description="Project", header=True)
    def display_name(self, obj):
        return [
            obj.name,
            f"Department: {obj.department.name if obj.department else 'N/A'}",
            None,
        ]

    @display(description="Members", label="info")
    def display_members_count(self, obj):
        return f"{obj.members.count()} Member(s)"

    @display(description="Total Tasks", label="primary")
    def display_tasks_count(self, obj):
        return f"{obj.tasks.count()} Task(s)"


@admin.register(ProjectMember)
class ProjectMemberAdmin(ModelAdmin):
    list_display = ("project", "user", "joined_at")
    search_fields = ("project__name", "user__email", "user__username")
    list_filter = (
        ("project", RelatedDropdownFilter),
        ("user", RelatedDropdownFilter),
    )
    autocomplete_fields = ("project", "user")
    ordering = ("-joined_at",)
