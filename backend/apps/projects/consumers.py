import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.projects.models import Project


class ProjectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.group_name = f"project_{self.project_id}"

        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        is_member = await self.check_membership(user, self.project_id)
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": f"Connected to project {self.project_id}",
                }
            )
        )

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
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    async def project_notification(self, event):
        await self.send(text_data=json.dumps(event["data"]))
