from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)

from apps.department.models import Department
from apps.projects.models import Project, ProjectMember
from apps.projects.utils import send_project_notification
from apps.shared.services import (
    BaseService,
)

User = get_user_model()


class Conflict(ValidationError):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict"
    default_code = "conflict"


class CreateProjectService(BaseService):
    def validate(self):
        department_id = getattr(self, "department", None)
        if not department_id:
            raise ValidationError({"department": "This field is required."})

        try:
            department = Department.objects.get(pk=department_id)
        except Department.DoesNotExist:
            raise ValidationError({"department": "Department not found."})

        user_role = getattr(self.user, "role", "")
        if user_role not in ("SUPERADMIN", "ORG_ADMIN") and not getattr(self.user, "is_superuser", False):
            if user_role == "PM":
                is_head = department.head_id == self.user.id
                is_dept_member = department.members.filter(id=self.user.id).exists()
                if not (is_head or is_dept_member):
                    raise PermissionDenied(
                        "Project Managers can only create projects within their assigned department."
                    )
            else:
                raise PermissionDenied("Team Members are not allowed to create projects.")


    def process(self):
        name = getattr(self, "name", None)
        department_id = getattr(self, "department", None)
        member_ids = getattr(self, "member_ids", None) or []

        if not name:
            raise ValidationError({"name": "This field is required."})

        project = Project.objects.create(
            owner=self.user,
            name=name,
            description=getattr(self, "description", "") or "",
            department_id=department_id,
        )

        if member_ids:
            for uid in member_ids:
                try:
                    u = User.objects.get(pk=uid)
                    ProjectMember.objects.get_or_create(project=project, user=u)
                except User.DoesNotExist:
                    pass

        send_project_notification(
            project.id,
            {
                "type": "project_created",
                "project_id": project.id,
                "project_name": project.name,
                "message": f'Project "{project.name}" was created',
                "triggered_by": self.user.email,
            },
        )

        return project


class UpdateProjectService(BaseService):
    def process(self):
        project = self.project
        for field, model_field in (
            ("name", "name"),
            ("description", "description"),
            ("department", "department_id"),
        ):
            value = getattr(self, field, None)
            if value not in (None, ""):
                setattr(project, model_field, value)
        project.save()

        send_project_notification(
            project.id,
            {
                "type": "project_updated",
                "project_id": project.id,
                "project_name": project.name,
                "message": f'Project "{project.name}" was updated',
                "triggered_by": project.owner.email,
            },
        )

        return project


class DeleteProjectService(BaseService):
    def process(self):
        project_id = self.project.id
        project_name = self.project.name
        self.project.delete()

        send_project_notification(
            project_id,
            {
                "type": "project_deleted",
                "project_id": project_id,
                "project_name": project_name,
                "message": f'Project "{project_name}" was deleted',
            },
        )


class AddProjectMemberService(BaseService):
    def process(self):
        project = self.project
        requesting_user = self.requesting_user

        if requesting_user.role not in ("SUPERADMIN", "ORG_ADMIN") and project.owner != requesting_user:
            raise PermissionDenied("Only the project owner or admin can add members.")

        email = getattr(self, "email", None)
        user_id = getattr(self, "user_id", None)

        if email:
            try:
                user_to_add = User.objects.get(email=email.strip())
            except User.DoesNotExist:
                raise ValidationError("User not found.")
        elif user_id:
            try:
                user_to_add = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise ValidationError("User not found.")
        else:
            raise ValidationError("Email or user_id is required.")


        if ProjectMember.objects.filter(project=project, user=user_to_add).exists():
            raise Conflict("User is already a member of this project.")

        membership = ProjectMember.objects.create(project=project, user=user_to_add)

        send_project_notification(
            project.id,
            {
                "type": "member_added",
                "project_id": project.id,
                "project_name": project.name,
                "user_email": user_to_add.email,
                "message": f'{user_to_add.email} was added to "{project.name}"',
            },
        )

        return membership


class RemoveProjectMemberService(BaseService):
    def process(self):
        project = self.project
        requesting_user = self.requesting_user

        if requesting_user.role != "ADMIN" and project.owner != requesting_user:
            raise PermissionDenied(
                "Only the project owner or admin can remove members."
            )

        try:
            membership = ProjectMember.objects.get(
                project=project, user__id=self.user_id
            )
        except ProjectMember.DoesNotExist:
            raise NotFound("User is not a member of this project.")

        user_email = membership.user.email
        membership.delete()

        send_project_notification(
            project.id,
            {
                "type": "member_removed",
                "project_id": project.id,
                "project_name": project.name,
                "user_email": user_email,
                "message": f'{user_email} was removed from "{project.name}"',
            },
        )
