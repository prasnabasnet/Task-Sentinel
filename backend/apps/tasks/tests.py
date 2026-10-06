from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.organization.models import Organization
from apps.department.models import Department
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task

User = get_user_model()


class TaskAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_superuser(
            email="admin@example.com", username="admin", password="password123", role="ADMIN"
        )
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="password123",
            role="PM",
            username="owner",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="password123",
            role="TM",
            username="member",
        )
        self.other_member = User.objects.create_user(
            email="othermember@example.com",
            password="password123",
            role="TM",
            username="other_member",
        )
        self.outsider = User.objects.create_user(
            email="outsider@example.com",
            password="password123",
            role="TM",
            username="outsider",
        )

        self.org = Organization.objects.create(name="Task Org", owner=self.owner)
        self.dept = Department.objects.create(organization=self.org, name="Task Dept")
        self.project = Project.objects.create(
            name="Task Test Project", owner=self.owner, department=self.dept
        )
        ProjectMember.objects.create(project=self.project, user=self.member)
        ProjectMember.objects.create(project=self.project, user=self.other_member)

        self.task = Task.objects.create(
            project=self.project,
            title="Existing Task",
            created_by=self.member,
        )

        self.list_url = reverse("task-list")
        self.detail_url = reverse("task-detail", kwargs={"pk": self.task.pk})

    def get_auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_create_task_by_owner_success(self):
        client = self.get_auth_client(self.owner)
        data = {"project": self.project.id, "title": "New Task"}
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created_by"]["email"], self.owner.email)

    def test_create_task_by_member_success(self):
        client = self.get_auth_client(self.member)
        data = {"project": self.project.id, "title": "Member Task"}
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_task_by_admin_success(self):
        client = self.get_auth_client(self.admin)
        data = {"project": self.project.id, "title": "Admin Task"}
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_task_by_outsider_forbidden(self):
        client = self.get_auth_client(self.outsider)
        data = {"project": self.project.id, "title": "Should Fail"}
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_create_task_unauthenticated_denied(self):
        data = {"project": self.project.id, "title": "No Auth"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 401)

    def test_create_task_with_valid_assignee(self):
        client = self.get_auth_client(self.owner)
        data = {
            "project": self.project.id,
            "title": "Assigned Task",
            "assignees": [self.member.id],
        }
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["assignees"][0]["email"], self.member.email)

    def test_create_task_with_invalid_assignee_rejected(self):
        client = self.get_auth_client(self.owner)
        data = {
            "project": self.project.id,
            "title": "Bad Assignee",
            "assignees": [999999],
        }
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_owner_sees_project_tasks_in_list(self):
        client = self.get_auth_client(self.owner)
        response = client.get(self.list_url)
        ids = [t["id"] for t in response.data]
        self.assertIn(self.task.id, ids)

    def test_member_sees_project_tasks_in_list(self):
        client = self.get_auth_client(self.other_member)
        response = client.get(self.list_url)
        ids = [t["id"] for t in response.data]
        self.assertIn(self.task.id, ids)

    def test_outsider_does_not_see_tasks_in_list(self):
        client = self.get_auth_client(self.outsider)
        response = client.get(self.list_url)
        ids = [t["id"] for t in response.data]
        self.assertNotIn(self.task.id, ids)

    def test_admin_sees_all_tasks_in_list(self):
        client = self.get_auth_client(self.admin)
        response = client.get(self.list_url)
        ids = [t["id"] for t in response.data]
        self.assertIn(self.task.id, ids)

    def test_retrieve_by_member_success(self):
        client = self.get_auth_client(self.other_member)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Existing Task")

    def test_retrieve_by_outsider_not_found(self):
        client = self.get_auth_client(self.outsider)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, 404)

    def test_update_by_creator_success(self):
        client = self.get_auth_client(self.member)
        response = client.patch(
            self.detail_url, {"title": "Updated Title"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Updated Title")

    def test_update_by_project_owner_success(self):
        client = self.get_auth_client(self.owner)
        response = client.patch(
            self.detail_url, {"status": "IN_PROGRESS"}, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_update_by_admin_success(self):
        client = self.get_auth_client(self.admin)
        response = client.patch(self.detail_url, {"status": "DONE"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_update_by_assignee_success(self):
        self.task.assignees.add(self.other_member)
        client = self.get_auth_client(self.other_member)
        response = client.patch(self.detail_url, {"status": "DONE"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_update_by_unrelated_member_forbidden(self):
        client = self.get_auth_client(self.other_member)
        response = client.patch(self.detail_url, {"title": "Nope"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_update_by_outsider_not_found(self):
        client = self.get_auth_client(self.outsider)
        response = client.patch(self.detail_url, {"title": "Nope"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_delete_by_creator_success(self):
        client = self.get_auth_client(self.member)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_delete_by_unrelated_member_forbidden(self):
        client = self.get_auth_client(self.other_member)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Task.objects.filter(id=self.task.id).exists())

    def test_filter_by_status(self):
        Task.objects.create(
            project=self.project,
            title="Done Task",
            created_by=self.owner,
            status="DONE",
        )
        client = self.get_auth_client(self.owner)
        response = client.get(self.list_url, {"status": "DONE"})
        titles = [t["title"] for t in response.data]
        self.assertIn("Done Task", titles)
        self.assertNotIn("Existing Task", titles)

    def test_filter_by_priority(self):
        Task.objects.create(
            project=self.project,
            title="Critical Task",
            created_by=self.owner,
            priority="CRITICAL",
        )
        client = self.get_auth_client(self.owner)
        response = client.get(self.list_url, {"priority": "CRITICAL"})
        titles = [t["title"] for t in response.data]
        self.assertIn("Critical Task", titles)

    def test_filter_by_title_icontains(self):
        Task.objects.create(
            project=self.project, title="Zebra Migration", created_by=self.owner
        )
        client = self.get_auth_client(self.owner)
        response = client.get(self.list_url, {"title": "zebra"})
        titles = [t["title"] for t in response.data]
        self.assertIn("Zebra Migration", titles)
        self.assertNotIn("Existing Task", titles)

    def test_filter_by_assignee(self):
        task = Task.objects.create(
            project=self.project,
            title="Assigned To Other",
            created_by=self.owner,
        )
        task.assignees.add(self.other_member)
        client = self.get_auth_client(self.owner)
        response = client.get(self.list_url, {"assignees": self.other_member.id})
        titles = [t["title"] for t in response.data]
        self.assertIn("Assigned To Other", titles)
        self.assertNotIn("Existing Task", titles)
