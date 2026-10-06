from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.contrib.filters.admin import BooleanRadioFilter, RelatedDropdownFilter

from apps.organization.models import Organization, OrganizationMember


class OrganizationMemberInline(TabularInline):
    model = OrganizationMember
    extra = 1
    autocomplete_fields = ("user",)
    verbose_name_plural = "Organization Members"
    tab = True


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    inlines = [OrganizationMemberInline]

    list_display = (
        "display_name",
        "owner",
        "display_is_active",
        "display_members_count",
        "display_departments_count",
        "created_at",
    )
    list_display_links = ("display_name",)

    search_fields = ("name", "description", "slug", "owner__email", "owner__username")
    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("owner", RelatedDropdownFilter),
    )
    autocomplete_fields = ("owner",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Organization Info",
            {
                "fields": ("name", "slug", "description", "is_active"),
            },
        ),
        (
            "Ownership",
            {
                "fields": ("owner",),
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

    @display(description="Organization", header=True)
    def display_name(self, obj):
        return [
            obj.name,
            f"Slug: {obj.slug}" if obj.slug else "No slug",
            None,
        ]

    @display(
        description="Status",
        ordering="is_active",
        label={
            True: "success",
            False: "danger",
        },
    )
    def display_is_active(self, obj):
        return "Active" if obj.is_active else "Inactive"

    @display(description="Members", label="info")
    def display_members_count(self, obj):
        return f"{obj.members.count()} Member(s)"

    @display(description="Departments", label="primary")
    def display_departments_count(self, obj):
        return f"{obj.departments.count()} Dept(s)"


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(ModelAdmin):
    list_display = ("organization", "user", "joined_at")
    search_fields = ("organization__name", "user__email", "user__username")
    list_filter = (
        ("organization", RelatedDropdownFilter),
        ("user", RelatedDropdownFilter),
    )
    autocomplete_fields = ("organization", "user")
    ordering = ("-joined_at",)
