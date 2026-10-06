from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.tasks.filters import TaskFilter
from apps.tasks.models.task import Task
from apps.tasks.permissions import CanDeleteTask, CanModifyTask, IsProjectMemberForTask
from apps.tasks.serializers.task import TaskSerializer
from apps.tasks.services import(
    CreateTaskService,
    DeleteTaskService,
    UpdateTaskService,
)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend,OrderingFilter, SearchFilter]
    filterset_class = TaskFilter

    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "priority", "created_at"]
    ordering = ["due_date"]

    def get_permissions(self):
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), CanDeleteTask()]
        if self.action in ("update", "partial_update"):
            return [permissions.IsAuthenticated(), CanModifyTask()]
        return [permissions.IsAuthenticated(), IsProjectMemberForTask()]

    def get_queryset(self):
        user = self.request.user
        base_qs = Task.objects.select_related("project", "created_by").prefetch_related("assignees")
        if getattr(user, "role", "") == "SUPERADMIN" or getattr(user, "is_superuser", False):
            return base_qs.all()
        if getattr(user, "role", "") in ("ORG_ADMIN", "PM"):
            return base_qs.filter(
                models.Q(project__department__organization__owner=user)
                | models.Q(project__department__organization__memberships__user=user)
                | models.Q(project__department__head=user)
                | models.Q(project__department__members=user)
                | models.Q(project__owner=user)
                | models.Q(project__members=user)
                | models.Q(assignees=user)
            ).distinct()
        # TM role: tasks in projects they belong to or are assigned to
        return base_qs.filter(
            models.Q(assignees=user)
            | models.Q(project__members=user)
        ).distinct()



    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = CreateTaskService.execute(
            request=request,
            validated_data=serializer.validated_data,
        )
        return Response(self.get_serializer(task).data,
                        status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        task = UpdateTaskService.execute(
            request=request,
            validated_data=serializer.validated_data,
            task=instance
        )
        return Response(self.get_serializer(task).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        DeleteTaskService.execute(request=request, task=instance)
        return Response(status=status.HTTP_204_NO_CONTENT)