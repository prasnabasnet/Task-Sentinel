from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task

_task_previous_state = {}


def send_project_notification(project_id, data):

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"project_{project_id}", {"type": "project_notification", "data": data}
    )


@receiver(post_save, sender=Project)
def project_saved(sender, instance, created, **kwargs):
    if created:
        send_project_notification(
            instance.id,
            {
                "type": "project_created",
                "project_id": instance.id,
                "project_name": instance.name,
                "message": f'Project "{instance.name}" was created',
                "triggered_by": instance.owner.email,
            },
        )
    else:
        send_project_notification(
            instance.id,
            {
                "type": "project_updated",
                "project_id": instance.id,
                "project_name": instance.name,
                "message": f'Project "{instance.name}" was updated',
                "triggered_by": instance.owner.email,
            },
        )


@receiver(post_delete, sender=Project)
def project_deleted(sender, instance, **kwargs):
    send_project_notification(
        instance.id,
        {
            "type": "project_deleted",
            "project_id": instance.id,
            "project_name": instance.name,
            "message": f'Project "{instance.name}" was deleted',
        },
    )


@receiver(post_save, sender=ProjectMember)
def member_added(sender, instance, created, **kwargs):
    if created:
        send_project_notification(
            instance.project.id,
            {
                "type": "member_added",
                "project_id": instance.project.id,
                "project_name": instance.project.name,
                "user_email": instance.user.email,
                "message": f'{instance.user.email} was added to "{instance.project.name}"',
            },
        )


@receiver(post_delete, sender=ProjectMember)
def member_removed(sender, instance, **kwargs):
    send_project_notification(
        instance.project.id,
        {
            "type": "member_removed",
            "project_id": instance.project.id,
            "project_name": instance.project.name,
            "user_email": instance.user.email,
            "message": f'{instance.user.email} was removed from "{instance.project.name}"',
        },
    )


@receiver(post_save, sender=Task)
def task_saved(sender, instance, created, **kwargs):
    if created:
        send_project_notification(
            instance.project.id,
            {
                "type": "task_created",
                "project_id": instance.project.id,
                "task_id": instance.id,
                "task_title": instance.title,
                "status": instance.status,
                "priority": instance.priority,
                "message": f'Task "{instance.title}" was created',
                "triggered_by": instance.created_by.email,
            },
        )

    else:
        prev = _task_previous_state.get(instance.id, {})
        old_status = prev.get("status", instance.status)
        old_assignee_id = prev.get("assignee_id")

        status_labels = {
            "TODO": "To Do",
            "IN_PROGRESS": "In Progress",
            "DONE": "Done",
        }

        data = {
            "type": "task_updated",
            "project_id": instance.project.id,
            "task_id": instance.id,
            "task_title": instance.title,
            "status": instance.status,
            "priority": instance.priority,
            "message": f'Task "{instance.title}" was updated',
        }

        if old_status != instance.status:
            data["type"] = "task_status_changed"
            data["old_status"] = old_status
            data["new_status"] = instance.status
            data["message"] = (
                f'Task "{instance.title}" moved from '
                f"{status_labels.get(old_status, old_status)} "
                f"to {status_labels.get(instance.status, instance.status)}"
            )

        elif old_assignee_id != instance.assignee_id:
            if instance.assignee:
                data["type"] = "task_assigned"
                data["assigned_to"] = instance.assignee.email
                data["message"] = (
                    f'Task "{instance.title}" was assigned to {instance.assignee.email}'
                )
            else:
                data["type"] = "task_unassigned"
                data["message"] = f'Task "{instance.title}" was unassigned'

        send_project_notification(instance.project.id, data)

    _task_previous_state[instance.id] = {
        "status": instance.status,
        "assignee_id": instance.assignee_id,
    }


@receiver(post_delete, sender=Task)
def task_deleted(sender, instance, **kwargs):
    _task_previous_state.pop(instance.id, None)
    send_project_notification(
        instance.project.id,
        {
            "type": "task_deleted",
            "project_id": instance.project.id,
            "task_id": instance.id,
            "task_title": instance.title,
            "message": f'Task "{instance.title}" was deleted',
        },
    )
