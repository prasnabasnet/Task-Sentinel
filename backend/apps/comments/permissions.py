from rest_framework import permissions

from apps.comments.models import Comment
from apps.organization.models import Organization
from apps.projects.models import Project
from apps.tasks.models import Task


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsProjectMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if getattr(request.user, "role", None) in ("SUPERADMIN", "ORG_ADMIN") or getattr(request.user, "is_superuser", False):
            return True

        from apps.department.models import Department

        if isinstance(obj, Organization):
            return (
                obj.owner == request.user
                or obj.memberships.filter(user=request.user).exists()
            )

        if isinstance(obj, Department):
            return (
                obj.organization.owner == request.user
                or obj.organization.memberships.filter(user=request.user).exists()
                or obj.head == request.user
                or obj.members.filter(id=request.user.id).exists()
            )

        if isinstance(obj, Project):
            project = obj
        elif isinstance(obj, Task):
            project = obj.project
        elif isinstance(obj, Comment):
            target = obj.commentable_object
            if isinstance(target, Organization):
                return (
                    target.owner == request.user
                    or target.memberships.filter(user=request.user).exists()
                )
            elif isinstance(target, Department):
                return (
                    target.organization.owner == request.user
                    or target.organization.memberships.filter(user=request.user).exists()
                    or target.head == request.user
                    or target.members.filter(id=request.user.id).exists()
                )
            elif isinstance(target, Project):
                project = target
            elif isinstance(target, Task):
                project = target.project
            else:
                return False
        else:
            return False

        return (
            project.owner == request.user
            or project.members.filter(id=request.user.id).exists()
        )



class IsCommentAuthorOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.role in ("SUPERADMIN", "ORG_ADMIN") or request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user

