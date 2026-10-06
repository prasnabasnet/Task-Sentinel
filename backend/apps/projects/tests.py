from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.department.models import Department
from apps.organization.models import Organization
from apps.projects.models import Project, ProjectMember

User = get_user_model()


class ProjectAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_superuser(
            email="admin@example.com", username="admin", password="password123", role="ADMIN"
        )
        self.pm_user = User.objects.create_user(
            email="pm@example.com",
            password="password123",
            role="PM",
            username="pm_user",
        )
        self.other_pm = User.objects.create_user(
            email="otherpm@example.com",
            password="password123",
            role="PM",
            username="other_pm",
        )
        self.dev_user = User.objects.create_user(
            email="dev@example.com",
            password="password123",
            role="TM",
            username="dev_user",
        )
        self.outsider = User.objects.create_user(
            email="outsider@example.com",
            password="password123",
            role="TM",
            username="outsider",
        )

        self.org = Organization.objects.create(name="Org A", owner=self.pm_user)
        self.dept = Department.objects.create(organization=self.org, name="Eng")
        self.project = Project.objects.create(name="Test Project", owner=self.pm_user, department=self.dept)
        ProjectMember.objects.create(project=self.project, user=self.dev_user)

        self.list_url = reverse("project-list")
        self.detail_url = reverse("project-detail", kwargs={"pk": self.project.pk})

    def get_auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_create_project_by_pm_success(self):
        client = self.get_auth_client(self.pm_user)
        data = {"name": "New Project", "description": "desc", "department": self.dept.id}
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["owner"]["email"], self.pm_user.email)

    def test_create_project_by_admin_success(self):
        client = self.get_auth_client(self.admin)
        data = {"name": "Admin Project", "department": self.dept.id}
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_project_by_team_member_forbidden(self):
        client = self.get_auth_client(self.dev_user)
        data = {"name": "Should Fail", "department": self.dept.id}
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_create_project_unauthenticated_denied(self):
        response = self.client.post(self.list_url, {"name": "No Auth", "department": self.dept.id}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_create_project_duplicate_name_rejected(self):
        client = self.get_auth_client(self.pm_user)
        response = client.post(self.list_url, {"name": "Test Project", "department": self.dept.id}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_create_project_owner_forced_to_requester(self):
        client = self.get_auth_client(self.pm_user)
        data = {"name": "Owner Override Attempt", "owner": self.other_pm.id, "department": self.dept.id}
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["owner"]["email"], self.pm_user.email)

    def test_owner_sees_own_project_in_list(self):
        client = self.get_auth_client(self.pm_user)
        response = client.get(self.list_url)
        ids = [p["id"] for p in response.data]
        self.assertIn(self.project.id, ids)

    def test_member_sees_project_in_list(self):
        client = self.get_auth_client(self.dev_user)
        response = client.get(self.list_url)
        ids = [p["id"] for p in response.data]
        self.assertIn(self.project.id, ids)

    def test_outsider_does_not_see_project_in_list(self):
        client = self.get_auth_client(self.outsider)
        response = client.get(self.list_url)
        ids = [p["id"] for p in response.data]
        self.assertNotIn(self.project.id, ids)

    def test_admin_sees_all_projects_in_list(self):
        client = self.get_auth_client(self.admin)
        response = client.get(self.list_url)
        ids = [p["id"] for p in response.data]
        self.assertIn(self.project.id, ids)

    def test_list_member_count_annotation(self):
        client = self.get_auth_client(self.pm_user)
        response = client.get(self.list_url)
        project_data = next(p for p in response.data if p["id"] == self.project.id)
        self.assertEqual(project_data["member_count"], 1)

    def test_retrieve_by_owner_success(self):
        client = self.get_auth_client(self.pm_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Test Project")

    def test_retrieve_by_outsider_not_found(self):
        client = self.get_auth_client(self.outsider)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, 404)

    def test_update_by_owner_success(self):
        client = self.get_auth_client(self.pm_user)
        response = client.patch(
            self.detail_url, {"description": "updated"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["description"], "updated")

    def test_update_by_admin_success(self):
        client = self.get_auth_client(self.admin)
        response = client.patch(
            self.detail_url, {"description": "admin edit"}, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_update_by_member_forbidden(self):
        client = self.get_auth_client(self.dev_user)
        response = client.patch(self.detail_url, {"description": "nope"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_update_by_other_pm_forbidden(self):
        client = self.get_auth_client(self.other_pm)
        response = client.patch(self.detail_url, {"description": "nope"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_delete_by_owner_success(self):
        client = self.get_auth_client(self.pm_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Project.objects.filter(id=self.project.id).exists())

    def test_delete_by_member_forbidden(self):
        client = self.get_auth_client(self.dev_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Project.objects.filter(id=self.project.id).exists())

    def test_filter_by_name_icontains(self):
        Project.objects.create(name="Zeta Rollout", owner=self.pm_user, department=self.dept)
        client = self.get_auth_client(self.admin)
        response = client.get(self.list_url, {"name": "zeta"})
        names = [p["name"] for p in response.data]
        self.assertIn("Zeta Rollout", names)
        self.assertNotIn("Test Project", names)

    def test_filter_by_owner_id(self):
        Project.objects.create(name="Other PM Project", owner=self.other_pm, department=self.dept)
        client = self.get_auth_client(self.admin)
        response = client.get(self.list_url, {"owner": self.other_pm.id})
        names = [p["name"] for p in response.data]
        self.assertIn("Other PM Project", names)
        self.assertNotIn("Test Project", names)

    def test_project_with_department(self):
        org = Organization.objects.create(name="Unique Org X", owner=self.pm_user)
        dept = Department.objects.create(organization=org, name="Eng Unique")
        client = self.get_auth_client(self.pm_user)
        project = Project.objects.create(
            name="Dept Project", owner=self.pm_user, department=dept
        )
        detail_url = reverse("project-detail", kwargs={"pk": project.pk})
        response = client.get(detail_url)
        self.assertEqual(response.status_code, 200)


class ProjectMemberAPITests(TestCase):
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
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="password123",
            role="TM",
            username="candidate",
        )
        self.outsider = User.objects.create_user(
            email="outsider@example.com",
            password="password123",
            role="TM",
            username="outsider",
        )

        self.org = Organization.objects.create(name="Member Test Org", owner=self.owner)
        self.dept = Department.objects.create(organization=self.org, name="Member Test Dept")
        self.project = Project.objects.create(
            name="Member Test Project", owner=self.owner, department=self.dept
        )
        ProjectMember.objects.create(project=self.project, user=self.member)

        self.members_url = reverse("project-members", kwargs={"pk": self.project.pk})

    def get_auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def remove_url(self, uid):
        return reverse(
            "project-member-remove", kwargs={"pk": self.project.pk, "uid": uid}
        )

    def test_list_members_as_owner(self):
        client = self.get_auth_client(self.owner)
        response = client.get(self.members_url)
        self.assertEqual(response.status_code, 200)
        emails = [m["email"] for m in response.data]
        self.assertIn(self.member.email, emails)

    def test_list_members_as_member(self):
        client = self.get_auth_client(self.member)
        response = client.get(self.members_url)
        self.assertEqual(response.status_code, 200)

    def test_list_members_as_admin(self):
        client = self.get_auth_client(self.admin)
        response = client.get(self.members_url)
        self.assertEqual(response.status_code, 200)

    def test_list_members_as_outsider_forbidden(self):
        client = self.get_auth_client(self.outsider)
        response = client.get(self.members_url)
        self.assertEqual(response.status_code, 403)

    def test_list_members_project_not_found(self):
        client = self.get_auth_client(self.owner)
        url = reverse("project-members", kwargs={"pk": 999999})
        response = client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_add_member_as_owner_success(self):
        client = self.get_auth_client(self.owner)
        response = client.post(
            self.members_url, {"user_id": self.candidate.id}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            ProjectMember.objects.filter(
                project=self.project, user=self.candidate
            ).exists()
        )

    def test_add_member_as_admin_success(self):
        client = self.get_auth_client(self.admin)
        response = client.post(
            self.members_url, {"user_id": self.candidate.id}, format="json"
        )
        self.assertEqual(response.status_code, 201)

    def test_add_member_as_regular_member_forbidden(self):
        client = self.get_auth_client(self.member)
        response = client.post(
            self.members_url, {"user_id": self.candidate.id}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_add_member_already_member_conflict(self):
        client = self.get_auth_client(self.owner)
        response = client.post(
            self.members_url, {"user_id": self.member.id}, format="json"
        )
        self.assertEqual(response.status_code, 409)

    def test_add_member_nonexistent_user_rejected(self):
        client = self.get_auth_client(self.owner)
        response = client.post(self.members_url, {"user_id": 999999}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_add_member_project_not_found(self):
        client = self.get_auth_client(self.owner)
        url = reverse("project-members", kwargs={"pk": 999999})
        response = client.post(url, {"user_id": self.candidate.id}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_remove_member_as_owner_success(self):
        client = self.get_auth_client(self.owner)
        response = client.delete(self.remove_url(self.member.id))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            ProjectMember.objects.filter(
                project=self.project, user=self.member
            ).exists()
        )

    def test_remove_member_as_admin_success(self):
        client = self.get_auth_client(self.admin)
        response = client.delete(self.remove_url(self.member.id))
        self.assertEqual(response.status_code, 204)

    def test_remove_member_as_regular_member_forbidden(self):
        client = self.get_auth_client(self.member)
        response = client.delete(self.remove_url(self.member.id))
        self.assertEqual(response.status_code, 403)

    def test_remove_member_not_a_member(self):
        client = self.get_auth_client(self.owner)
        response = client.delete(self.remove_url(self.candidate.id))
        self.assertEqual(response.status_code, 404)

    def test_remove_member_project_not_found(self):
        client = self.get_auth_client(self.owner)
        url = reverse(
            "project-member-remove", kwargs={"pk": 999999, "uid": self.member.id}
        )
        response = client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_member_endpoints_unauthenticated_denied(self):
        response = self.client.get(self.members_url)
        self.assertEqual(response.status_code, 401)
