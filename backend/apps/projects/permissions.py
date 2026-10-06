from rest_framework.permissions import BasePermission


class IsAdminPMOrTM(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("SUPERADMIN", "ORG_ADMIN", "PM", "TM")
        )



class IsProjectOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role in ("SUPERADMIN", "ORG_ADMIN") or request.user.is_superuser:
            return True
        return obj.owner == request.user


class IsProjectMemberOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if (
            getattr(request.user, "is_admin", False)
            or getattr(request.user, "role", "") in ("SUPERADMIN", "ORG_ADMIN")
        ):
            return True
        return (
            obj.owner == request.user
            or obj.members.filter(id=request.user.id).exists()
            or obj.tasks.filter(assignees=request.user).exists()
        )

