import logging
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email_task(self, user_id: int):
    """
    Task to send a welcome email to a newly registered user.
    """
    try:
        user = User.objects.filter(id=user_id).first()
        if not user or not user.email:
            logger.warning(f"[send_welcome_email_task] User with ID '{user_id}' not found or has no email.")
            return

        subject = "Welcome to Task Manager!"
        message = (
            f"Hello {user.username or user.first_name or 'there'},\n\n"
            "Welcome to Task Manager! We are excited to have you on board.\n\n"
            "Best regards,\n"
            "The Task Manager Team"
        )
        recipient_list = [user.email]

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info(f"[send_welcome_email_task] Welcome email successfully sent to {user.email}.")
    except Exception as exc:
        logger.error(f"[send_welcome_email_task] Error sending welcome email to user_id={user_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_member_welcome_email_task(self, email: str, raw_password: str, organization_name: str = ""):
    """
    Task to email a newly created team member/PM their login credentials.
    """
    try:
        subject = "Your Task Manager Account Details"
        org_info = f" for organization '{organization_name}'" if organization_name else ""
        message = (
            f"Hello,\n\n"
            f"An account has been created for you{org_info} in Task Manager.\n\n"
            f"Here are your login credentials:\n"
            f"- Email: {email}\n"
            f"- Password: {raw_password}\n\n"
            f"Please log in and change your password as soon as possible.\n\n"
            f"Best regards,\n"
            f"The Task Manager Team"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"[send_member_welcome_email_task] Member credentials successfully sent to {email}.")
    except Exception as exc:
        logger.error(f"[send_member_welcome_email_task] Error sending member welcome email to {email}: {exc}", exc_info=True)
        raise self.retry(exc=exc)



@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_task_completion_email_task(self, task_id: int):
    """
    Task to send an email notification when a task status moves to 'DONE'.
    """
    try:
        from apps.tasks.models import Task

        task = Task.objects.select_related("project", "created_by").prefetch_related("assignees").filter(id=task_id).first()
        if not task:
            logger.warning(f"[send_task_completion_email_task] Task with ID '{task_id}' not found.")
            return

        recipients = set()
        if task.created_by and task.created_by.email:
            recipients.add(task.created_by.email)
        for assignee in task.assignees.all():
            if assignee.email:
                recipients.add(assignee.email)

        if not recipients:
            logger.info(f"[send_task_completion_email_task] No recipients found for completed task ID '{task_id}'.")
            return

        subject = f"Task Completed: {task.title}"
        message = (
            f"Great news!\n\n"
            f"The task '{task.title}' in project '{task.project.name}' has been marked as DONE.\n\n"
            f"Task Details:\n"
            f"- Title: {task.title}\n"
            f"- Project: {task.project.name}\n"
            f"- Priority: {task.get_priority_display()}\n\n"
            f"Regards,\nTask Manager System"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(recipients),
            fail_silently=False,
        )
        logger.info(f"[send_task_completion_email_task] Task completion email sent to {list(recipients)} for task ID '{task_id}'.")
    except Exception as exc:
        logger.error(f"[send_task_completion_email_task] Error sending task completion email for task_id={task_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_task_update_email_task(self, task_id: int, status_changed: bool = False, priority_changed: bool = False):
    """
    Task to send an email notification when a task status or priority is updated.
    """
    try:
        from apps.tasks.models import Task

        task = Task.objects.select_related("project", "created_by").prefetch_related("assignees").filter(id=task_id).first()
        if not task:
            logger.warning(f"[send_task_update_email_task] Task with ID '{task_id}' not found.")
            return

        recipients = set()
        if task.created_by and task.created_by.email:
            recipients.add(task.created_by.email)
        for assignee in task.assignees.all():
            if assignee.email:
                recipients.add(assignee.email)

        if not recipients:
            logger.info(f"[send_task_update_email_task] No recipients found for updated task ID '{task_id}'.")
            return

        changes_summary = []
        if status_changed:
            changes_summary.append(f"Status updated to '{task.get_status_display()}'")
        if priority_changed:
            changes_summary.append(f"Priority updated to '{task.get_priority_display()}'")

        changes_text = ", ".join(changes_summary) if changes_summary else "Details updated"

        subject = f"Task Updated: {task.title}"
        message = (
            f"Hello,\n\n"
            f"The task '{task.title}' in project '{task.project.name}' has been updated.\n\n"
            f"Changes: {changes_text}\n"
            f"Current Status: {task.get_status_display()}\n"
            f"Current Priority: {task.get_priority_display()}\n\n"
            f"Regards,\nTask Manager System"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(recipients),
            fail_silently=False,
        )
        logger.info(f"[send_task_update_email_task] Task update email sent to {list(recipients)} for task ID '{task_id}'.")
    except Exception as exc:
        logger.error(f"[send_task_update_email_task] Error sending task update email for task_id={task_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task
def send_daily_productivity_summary_task():
    """
    Cron task executed daily via Celery Beat to send a summary of open and completed tasks.
    """
    try:
        from apps.tasks.models import Task

        total_tasks = Task.objects.count()
        done_tasks = Task.objects.filter(status=Task.Status.DONE).count()
        in_progress_tasks = Task.objects.filter(status=Task.Status.IN_PROGRESS).count()
        todo_tasks = Task.objects.filter(status=Task.Status.TODO).count()

        active_users = User.objects.filter(is_active=True, email__isnull=False).exclude(email="")
        recipient_emails = list(active_users.values_list("email", flat=True))

        if not recipient_emails:
            logger.info("[send_daily_productivity_summary_task] No active users with email addresses found.")
            return

        subject = "Daily Productivity Summary"
        message = (
            "Good day!\n\n"
            "Here is your daily Task Manager productivity summary:\n"
            f"- Total Tasks: {total_tasks}\n"
            f"- Tasks Done: {done_tasks}\n"
            f"- Tasks In Progress: {in_progress_tasks}\n"
            f"- Tasks To Do: {todo_tasks}\n\n"
            "Keep up the great work!\n"
            "The Task Manager Team"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
            fail_silently=False,
        )
        logger.info(f"[send_daily_productivity_summary_task] Daily summary sent to {len(recipient_emails)} user(s).")
    except Exception as exc:
        logger.error(f"[send_daily_productivity_summary_task] Error sending daily summary: {exc}", exc_info=True)
