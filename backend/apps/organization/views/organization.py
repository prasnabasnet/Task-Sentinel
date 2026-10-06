from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.organization.models import Organization
from apps.organization.permissions import CanCreateOrganization, IsAdminOrOwner
from apps.organization.serializers import OrganizationSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()
    http_method_names = ["get", "patch", "put", "delete", "head", "options"]

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdminOrOwner()]
        return [IsAuthenticated()]



    def get_queryset(self):
        user = self.request.user
        if getattr(user, "role", "") == "SUPERADMIN" or getattr(user, "is_superuser", False):
            return Organization.objects.all()
        return (
            Organization.objects.filter(memberships__user=user)
            | Organization.objects.filter(owner=user)
            | Organization.objects.filter(departments__projects__members=user)
            | Organization.objects.filter(departments__projects__tasks__assignees=user)
        ).distinct()

