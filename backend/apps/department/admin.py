from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.contrib.filters.admin import RelatedDropdownFilter

from apps.department.models import Department


@admin.register(Department)
class DepartmentAdmin(ModelAdmin):
    list_display = (
        "display_name",
        "organization",
        "head",
        "display_members_count",
        "display_projects_count",
        "created_at",
    )
    list_display_links = ("display_name",)

    search_fields = (
        "name",
        "description",
        "organization__name",
        "head__email",
        "head__username",
    )
    list_filter = (
        ("organization", RelatedDropdownFilter),
        ("head", RelatedDropdownFilter),
    )
    autocomplete_fields = ("organization", "head", "members")
    ordering = ("organization", "name")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Department Information",
            {
                "fields": ("name", "organization", "description"),
            },
        ),
        (
            "Leadership & Membership",
            {
                "fields": ("head", "members"),
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

    @display(description="Department", header=True)
    def display_name(self, obj):
        return [
            obj.name,
            f"Org: {obj.organization.name if obj.organization else 'N/A'}",
            None,
        ]

    @display(description="Members", label="info")
    def display_members_count(self, obj):
        return f"{obj.members.count()} Member(s)"

    @display(description="Projects", label="primary")
    def display_projects_count(self, obj):
        return f"{obj.projects.count()} Project(s)"
