from django.db import models
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.organization.models import Organization
from apps.organization.permissions import IsAdminOrOwner
from apps.organization.serializers import OrganizationSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    http_method_names = ["get", "patch", "put", "delete", "head", "options"]

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdminOrOwner()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        

        if getattr(user, "role", "") == "SUPERADMIN" or getattr(user, "is_superuser", False):
            qs = Organization.objects.all()
        else:

            qs = Organization.objects.filter(
                models.Q(memberships__user=user)
                | models.Q(owner=user)
                | models.Q(departments__projects__members=user)
                | models.Q(departments__projects__tasks__assignees=user)
            )


        return (
            qs.select_related("owner", "owner__profile")
            .prefetch_related("members", "members__profile")
            .distinct()
        )