from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role in ("SUPERADMIN", "ORG_ADMIN") or request.user.is_superuser)
        )


class IsSelfOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return request.user.role in ("SUPERADMIN", "ORG_ADMIN") or obj == request.user


class IsAdminOrOrgOwner(BasePermission):
    """
    Permission to check if the user is a SUPERADMIN OR an ORG_ADMIN
    belonging to the same organization as the object / request.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role not in ("SUPERADMIN", "ORG_ADMIN") and not request.user.is_superuser:
            return False

        oid = view.kwargs.get("oid")
        if oid:
            from apps.organization.models import Organization

            try:
                org = Organization.objects.get(pk=oid)
                return org.owner == request.user or org.memberships.filter(user=request.user).exists()
            except Organization.DoesNotExist:
                return False
        return True


    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == "SUPERADMIN" or request.user.is_superuser:
            return True

        # Check object organization ownership / membership
        org = getattr(obj, "organization", None)
        if not org and hasattr(obj, "department"):
            org = getattr(obj.department, "organization", None)
        if not org and hasattr(obj, "project"):
            org = getattr(obj.project.department, "organization", None)

        if org and request.user.role == "ORG_ADMIN":
            return org.owner == request.user or org.memberships.filter(user=request.user).exists()

        return False

