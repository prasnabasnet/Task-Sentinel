from django.contrib.auth import get_user_model
from django.db import models
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.department.models import Department
from apps.department.serializers import DepartmentSerializer
from apps.organization.models import Organization
from apps.projects.serializers import ProjectSerializer
from apps.shared.services import BaseService


class BaseDepartmentService(BaseService):
    def get_organization(self, pk, user):
        try:
            org = Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            raise NotFound("Organization not found")

        if not (getattr(user, "role", "") == "SUPERADMIN" or getattr(user, "is_superuser", False)):
            is_owner = org.owner == user
            is_member = (
                org.memberships.filter(user=user).exists()
                or org.departments.filter(projects__members=user).exists()
                or org.departments.filter(projects__tasks__assignees=user).exists()
            )
            if not (is_owner or is_member):
                raise PermissionDenied("You are not a member of this organization")

        return org


class GetDepartmentService(BaseDepartmentService):
    def process(self):
        org = self.get_organization(self.organization_id, self.user)
        user = self.user
        if getattr(user, "role", "") in ("SUPERADMIN", "ORG_ADMIN") or getattr(user, "is_superuser", False):
            return org.departments.all()
        if getattr(user, "role", "") == "PM":
            return org.departments.filter(
                models.Q(head=user)
                | models.Q(members=user)
                | models.Q(projects__owner=user)
                | models.Q(projects__members=user)
                | models.Q(projects__tasks__assignees=user)
            ).distinct()
        # TM role: only departments where they are a member or assigned to projects/tasks
        return org.departments.filter(
            models.Q(members=user)
            | models.Q(projects__members=user)
            | models.Q(projects__tasks__assignees=user)
        ).distinct()




User = get_user_model()


class CreateDepartmentService(BaseDepartmentService):
    def validate(self):
        user_role = getattr(self.user, "role", "")
        if user_role not in ("SUPERADMIN", "ORG_ADMIN") and not getattr(self.user, "is_superuser", False):
            raise PermissionDenied("Only Organization Admins can create departments.")

    def process(self):
        org = self.get_organization(self.organization_id, self.user)
        if isinstance(self.data, dict) and any(
            isinstance(v, User) for v in self.data.values()
        ):
            return Department.objects.create(organization=org, **self.data)
        serializer = DepartmentSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        return serializer.save(organization=org)



class GetDepartmentProjectService(BaseService):
    def process(self):
        user = self.user
        if getattr(user, "role", "") in ("SUPERADMIN", "ORG_ADMIN") or getattr(user, "is_superuser", False):
            return self.department.projects.all()
        return (
            self.department.projects.filter(owner=user)
            | self.department.projects.filter(members=user)
            | self.department.projects.filter(tasks__assignees=user)
        ).distinct()



class CreateProjectService(BaseService):
    def process(self):
        user = self.user
        department = self.department

        if not (getattr(user, "is_admin", False) or getattr(user, "role", "") == "PM"):
            raise PermissionDenied("You are not authorized to create project")

        data = self.data.copy()
        data["department"] = department.pk
        serializer = ProjectSerializer(data=data, context={"request": self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=user)
        return serializer.data
