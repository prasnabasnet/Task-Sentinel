from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_project_notification(project_id, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"project_{project_id}", {"type": "project_notification", "data": data}
    )
