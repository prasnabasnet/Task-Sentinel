from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.organization.models import Organization, OrganizationMember

User = get_user_model()


class OrganizationAPITests(TestCase):
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
        self.outsider = User.objects.create_user(
            email="outsider@example.com",
            password="password123",
            role="TM",
            username="outsider",
        )

        self.org = Organization.objects.create(name="Acme Corp", owner=self.owner)
        OrganizationMember.objects.create(organization=self.org, user=self.member)

        self.list_url = reverse("organization-list")
        self.detail_url = reverse("organization-detail", kwargs={"pk": self.org.id})

    def get_auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_organizations_does_not_500(self):
        client = self.get_auth_client(self.owner)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_organization_returns_expected_fields(self):
        client = self.get_auth_client(self.owner)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Acme Corp")
        self.assertEqual(response.data["owner"]["email"], self.owner.email)
        self.assertIn("slug", response.data)
        self.assertIn("created_at", response.data)

    def test_slug_auto_generated_on_create(self):
        client = self.get_auth_client(self.owner)
        data = {"name": "Beta Industries"}
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["slug"], "beta-industries")

    def test_create_organization_sets_owner_to_requester(self):
        client = self.get_auth_client(self.owner)
        data = {"name": "New Org"}
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["owner"]["email"], self.owner.email)

    def test_create_organization_by_team_member_forbidden(self):
        client = self.get_auth_client(self.member)
        data = {"name": "Forbidden Org"}
        response = client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_create_organization_unauthenticated_denied(self):
        response = self.client.post(
            self.list_url, {"name": "No Auth Org"}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_create_organization_duplicate_name_rejected(self):
        client = self.get_auth_client(self.owner)
        response = client.post(self.list_url, {"name": "Acme Corp"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_owner_sees_own_organization_in_list(self):
        client = self.get_auth_client(self.owner)
        response = client.get(self.list_url)
        ids = [o["id"] for o in response.data]
        self.assertIn(self.org.id, ids)

    def test_member_sees_organization_in_list(self):
        client = self.get_auth_client(self.member)
        response = client.get(self.list_url)
        ids = [o["id"] for o in response.data]
        self.assertIn(self.org.id, ids)

    def test_outsider_does_not_see_organization_in_list(self):
        client = self.get_auth_client(self.outsider)
        response = client.get(self.list_url)
        ids = [o["id"] for o in response.data]
        self.assertNotIn(self.org.id, ids)

    def test_admin_sees_all_organizations_in_list(self):
        client = self.get_auth_client(self.admin)
        response = client.get(self.list_url)
        ids = [o["id"] for o in response.data]
        self.assertIn(self.org.id, ids)

    def test_update_by_owner_success(self):
        client = self.get_auth_client(self.owner)
        response = client.patch(
            self.detail_url, {"description": "Updated desc"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["description"], "Updated desc")

    def test_update_by_admin_success(self):
        client = self.get_auth_client(self.admin)
        response = client.patch(
            self.detail_url, {"description": "Admin edit"}, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_update_by_member_forbidden(self):
        client = self.get_auth_client(self.member)
        response = client.patch(self.detail_url, {"description": "Nope"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_update_by_outsider_forbidden(self):
        client = self.get_auth_client(self.outsider)
        response = client.patch(self.detail_url, {"description": "Nope"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_delete_by_owner_success(self):
        client = self.get_auth_client(self.owner)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Organization.objects.filter(id=self.org.id).exists())

    def test_delete_by_member_forbidden(self):
        client = self.get_auth_client(self.member)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Organization.objects.filter(id=self.org.id).exists())

    def test_delete_unauthenticated_denied(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 401)

    def test_retrieve_by_outsider_not_in_queryset(self):
        client = self.get_auth_client(self.outsider)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, 404)
