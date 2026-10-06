from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from apps.projects.models import Project


class TaskConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.tasks_group_name = f"project_{self.project_id}_tasks"

        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        is_member = await self.check_membership(user, self.project_id)
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.tasks_group_name, self.channel_name)
        await self.accept()

    @database_sync_to_async
    def check_membership(self, user, project_id):
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return False
        if getattr(user, "is_admin", False) or getattr(user, "role", "") == "ADMIN":
            return True
        return (
            project.owner_id == user.id
            or project.members.filter(id=user.id).exists()
            or project.tasks.filter(assignees=user).exists()
        )

    async def disconnect(self, close_code):
        if hasattr(self, "tasks_group_name"):
            await self.channel_layer.group_discard(self.tasks_group_name, self.channel_name)

    async def task_event(self, event):
        await self.send_json({
            "action": event.get("action"),
            "task": event.get("task"),
            "task_id": event.get("task_id"),
            "status_changed": event.get("status_changed", False),
            "priority_changed": event.get("priority_changed", False),
        })