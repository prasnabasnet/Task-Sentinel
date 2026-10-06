from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.department.serializers import DepartmentSerializer
from apps.department.services import (
    CreateDepartmentService,
    CreateProjectService,
    GetDepartmentProjectService,
    GetDepartmentService,
)
from apps.projects.serializers import ProjectSerializer
from apps.users.permissions import IsAdminOrOrgOwner


class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrOrgOwner()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return GetDepartmentService.execute(
            organization_id=self.kwargs["oid"], user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.instance = CreateDepartmentService.execute(
            organization_id=self.kwargs["oid"],
            user=self.request.user,
            data=serializer.validated_data,
        )

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="projects",
        url_name="project-list",
    )
    def projects(self, request, oid=None, pk=None):
        department = self.get_object()
        if request.method == "POST":
            project_data = CreateProjectService.execute(
                department=department,
                user=request.user,
                data=request.data,
                request=request,
            )
            return Response(project_data, status=status.HTTP_201_CREATED)

        projects = GetDepartmentProjectService.execute(
            department=department, user=request.user
        )
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)
