from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class SilkIntegrationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            first_name="Admin",
            last_name="User",
        )
        self.regular_user = User.objects.create_user(
            username="regularuser",
            email="user@example.com",
            password="password123",
            first_name="Regular",
            last_name="User",
        )

    def test_silk_unauthenticated_redirects_to_login(self):
        """Unauthenticated requests to /silk/ should redirect to /djadmin/login/?next=/silk/"""
        response = self.client.get("/silk/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/djadmin/login/", response.url)

    def test_admin_login_page_renders(self):
        """Admin login page configured as LOGIN_URL should return 200 OK."""
        response = self.client.get("/djadmin/login/")
        self.assertEqual(response.status_code, 200)

    def test_silk_authenticated_superuser_access(self):
        """Authenticated staff/superuser can access the Silk dashboard."""
        self.client.login(email="admin@example.com", password="password123")
        response = self.client.get("/silk/")
        self.assertEqual(response.status_code, 200)


from django.core import mail
from apps.shared.tasks import (
    send_welcome_email_task,
    send_task_completion_email_task,
    send_task_update_email_task,
    send_daily_productivity_summary_task,
)
from apps.organization.models import Organization
from apps.department.models import Department
from apps.projects.models import Project
from apps.tasks.models import Task


class TaskCeleryEmailTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="emailtestuser",
            email="testuser@example.com",
            password="password123",
        )
        self.org = Organization.objects.create(name="Org 1", owner=self.user)
        self.dept = Department.objects.create(organization=self.org, name="Dept 1")
        self.project = Project.objects.create(
            name="Proj 1", owner=self.user, department=self.dept
        )
        self.task = Task.objects.create(
            project=self.project,
            title="Sample Task",
            created_by=self.user,
        )

    def test_send_welcome_email_task(self):
        send_welcome_email_task(self.user.id)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Welcome to Task Manager!", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_send_task_completion_email_task(self):
        send_task_completion_email_task(self.task.id)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Task Completed: Sample Task", mail.outbox[0].subject)

    def test_send_task_update_email_task(self):
        send_task_update_email_task(
            self.task.id, status_changed=True, priority_changed=True
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Task Updated: Sample Task", mail.outbox[0].subject)

    def test_send_daily_productivity_summary_task(self):
        send_daily_productivity_summary_task()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Daily Productivity Summary", mail.outbox[0].subject)

