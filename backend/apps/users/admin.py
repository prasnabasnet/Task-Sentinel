from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin, StackedInline
from unfold.contrib.filters.admin import BooleanRadioFilter, ChoicesDropdownFilter
from unfold.decorators import action, display

from apps.users.models import Profile, RoleChoices, User

# Unregister default Group and register with Unfold ModelAdmin + BaseGroupAdmin
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


class ProfileInline(StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "User Profile"
    fk_name = "user"
    fields = ("display_name", "avatar_url", "bio")
    tab = True


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    inlines = (ProfileInline,)

    list_display = (
        "display_header",
        "email",
        "display_role",
        "display_is_active",
        "date_joined",
    )
    list_display_links = ("display_header", "email")
    list_filter = (
        ("role", ChoicesDropdownFilter),
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions & Roles",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "role", "password1", "password2"),
            },
        ),
    )

    actions = ["make_active", "make_inactive"]

    @display(description="User", header=True)
    def display_header(self, obj):
        full_name = obj.get_full_name()
        display_str = full_name if full_name else obj.username
        return [
            display_str,
            obj.email,
            None,
        ]

    @display(
        description="Role",
        ordering="role",
        label={
            RoleChoices.SUPERADMIN: "danger",
            RoleChoices.ORG_ADMIN: "warning",
            RoleChoices.PM: "info",
            RoleChoices.TM: "success",
        },
    )
    def display_role(self, obj):
        return obj.get_role_display()

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

    @action(description="Mark selected users as Active")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) successfully activated.")

    @action(description="Mark selected users as Inactive")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) successfully deactivated.")

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)
