from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from apps.projects.filters import ProjectFilter
from apps.projects.models import Project
from apps.projects.permissions import (
    IsAdminPMOrTM,
    IsProjectMemberOrAdmin,
    IsProjectOwnerOrAdmin,
)
from apps.projects.serializers import ProjectSerializer
from apps.projects.services import (
    CreateProjectService,
    DeleteProjectService,
    UpdateProjectService,
)

User = get_user_model()


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProjectFilter

    # controls which porjects can this specific user even see
    def get_queryset(self):
        user = self.request.user
        base_queryset = Project.objects.select_related("owner", "department").annotate(
            member_count=Count("members", distinct=True),
            task_count=Count("tasks", distinct=True),
        )
        if getattr(user, "role", "") == "SUPERADMIN" or getattr(user, "is_superuser", False):
            return base_queryset
        if getattr(user, "role", "") in ("ORG_ADMIN", "PM"):
            return base_queryset.filter(
                models.Q(department__organization__owner=user)
                | models.Q(department__organization__memberships__user=user)
                | models.Q(department__head=user)
                | models.Q(department__members=user)
                | models.Q(owner=user)
                | models.Q(members=user)
            ).distinct()
        # TM role
        return base_queryset.filter(
            models.Q(members=user) | models.Q(tasks__assignees=user)
        ).distinct()

    def get_permissions(self):
        if self.action == "create":
            return [IsAdminPMOrTM()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsProjectOwnerOrAdmin()]
        return [IsProjectMemberOrAdmin()]


    def perform_create(self, serializer):
        project = CreateProjectService.execute(
            user=self.request.user,
            name=self.request.data.get("name"),
            description=self.request.data.get("description", ""),
            department=self.request.data.get("department"),
            member_ids=self.request.data.get("member_ids", []),
        )
        serializer.instance = project

    def perform_update(self, serializer):
        project = UpdateProjectService.execute(
            project=serializer.instance,
            name=self.request.data.get("name"),
            description=self.request.data.get("description"),
            department=self.request.data.get("department"),
        )
        serializer.instance = project

    def perform_destroy(self, instance):
        DeleteProjectService.execute(project=instance)
