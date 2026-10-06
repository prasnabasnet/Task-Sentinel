from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from apps.shared.services import BaseService
from apps.shared.tasks import (
    send_task_completion_email_task,
    send_task_update_email_task,
)
from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer


class CreateTaskService(BaseService):
    def validate(self) -> None:
        project = self.validated_data.get("project")
        user_role = getattr(self.user, "role", "")
        can_create = (
            user_role in ("SUPERADMIN", "ORG_ADMIN")
            or getattr(self.user, "is_superuser", False)
            or (user_role == "PM" and (
                project.department.head_id == self.user.id
                or project.department.members.filter(id=self.user.id).exists()
                or project.owner_id == self.user.id
                or project.members.filter(id=self.user.id).exists()
                or project.department.organization.owner_id == self.user.id
                or project.department.organization.memberships.filter(user=self.user).exists()
            ))
        )
        self.check_permission(
            can_create, "Team members are not allowed to create tasks."
        )



    def process(self) -> Task:
        assignees = self.validated_data.pop("assignees", [])
        task = Task.objects.create(created_by=self.user, **self.validated_data)

        if assignees:
            task.assignees.set(assignees)
            for u in assignees:
                task.project.members.add(u)

        self.log_info(
            f"Task '{task.title}' created by user '{self.user.username}' in project '{task.project.name}'."
        )

        self._broadcast_websocket_event(task, action="created")

        return task

    def _broadcast_websocket_event(self, task: Task, action: str) -> None:
        channel_layer = get_channel_layer()
        group_name = f"project_{task.project.id}_tasks"
        serialized_data = TaskSerializer(task).data

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "task_event",
                "action": action,
                "task": serialized_data,
            },
        )


class UpdateTaskService(BaseService):
    def validate(self) -> None:
        user_role = getattr(self.user, "role", "")
        is_elevated = (
            user_role in ("SUPERADMIN", "ORG_ADMIN")
            or getattr(self.user, "is_superuser", False)
            or (user_role == "PM" and (
                self.task.project.department.head_id == self.user.id
                or self.task.project.department.members.filter(id=self.user.id).exists()
                or self.task.project.owner_id == self.user.id
                or self.task.project.members.filter(id=self.user.id).exists()
                or self.task.project.department.organization.owner_id == self.user.id
                or self.task.project.department.organization.memberships.filter(user=self.user).exists()
            ))
            or self.task.created_by_id == self.user.id
        )

        if not is_elevated:
            # User is a regular Team Member (TM)
            disallowed_fields = set(self.validated_data.keys()) - {"status", "priority"}
            if disallowed_fields:
                raise PermissionDenied(
                    "Team Members are only allowed to change status and priority of a task."
                )


    def process(self) -> Task:
        assignees = self.validated_data.pop("assignees", None)
        old_status = self.task.status
        old_priority = self.task.priority

        for attr, value in self.validated_data.items():
            setattr(self.task, attr, value)
        self.task.save()

        if assignees is not None:
            self.task.assignees.set(assignees)
            for u in assignees:
                self.task.project.members.add(u)

        status_changed = old_status != self.task.status
        priority_changed = old_priority != self.task.priority

        self.log_info(
            f"Task '{self.task.title}' updated by user '{self.user.username}' in project '{self.task.project.name}'. "
            f"Status changed: {status_changed}, Priority changed: {priority_changed}."
        )

        if status_changed and self.task.status == Task.Status.DONE:
            task_id = self.task.id
            transaction.on_commit(
                lambda: send_task_completion_email_task.delay(task_id)
            )

        if status_changed or priority_changed:
            task_id = self.task.id
            sc = status_changed
            pc = priority_changed
            transaction.on_commit(
                lambda: send_task_update_email_task.delay(
                    task_id, status_changed=sc, priority_changed=pc
                )
            )

        self._broadcast_websocket_event(
            task=self.task,
            action="updated",
            status_changed=status_changed,
            priority_changed=priority_changed,
        )

        return self.task

    def _broadcast_websocket_event(self, task: Task, action: str, **kwargs) -> None:
        channel_layer = get_channel_layer()
        group_name = f"project_{task.project.id}_tasks"
        serialized_data = TaskSerializer(task).data

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "task_event",
                "action": action,
                "task": serialized_data,
                "status_changed": kwargs.get("status_changed", False),
                "priority_changed": kwargs.get("priority_changed", False),
            },
        )


class DeleteTaskService(BaseService):
    def process(self) -> None:
        project_id = self.task.project_id
        project_name = self.task.project.name
        task_id = self.task.id

        self.task.delete()
        self.log_info(
            f"Task '{task_id}' deleted by user '{self.user.username}' from project '{project_name}' (ID: {project_id})."
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"project_{project_id}_tasks",
            {
                "type": "task_event",
                "action": "deleted",
                "task_id": task_id,
            },
        )
