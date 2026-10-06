from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.organization.models import Organization, OrganizationMember
from apps.department.models import Department
from apps.projects.models import Project

User = get_user_model()


class DepartmentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_superuser(
            email='admin@example.com', username='admin', password='password123', role='ADMIN'
        )
        self.org_owner = User.objects.create_user(
            email='owner@example.com', password='password123', role='PM', username='org_owner'
        )
        self.org_member = User.objects.create_user(
            email='member@example.com', password='password123', role='TM', username='org_member'
        )
        self.non_member = User.objects.create_user(
            email='nonmember@example.com', password='password123', role='TM', username='non_member'
        )

        self.org = Organization.objects.create(name='Test Org', owner=self.org_owner)
        OrganizationMember.objects.create(organization=self.org, user=self.org_member)

        self.department = Department.objects.create(
            organization=self.org,
            name='Engineering',
            description='Product Engineering Team',
            head=self.org_member
        )
        self.department.members.add(self.org_member)

        self.project = Project.objects.create(
            name='Project A',
            owner=self.org_owner,
            department=self.department
        )

    def get_auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_departments_success(self):
        client = self.get_auth_client(self.org_member)
        url = reverse('dept-list', kwargs={'oid': self.org.id})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Engineering')
        self.assertEqual(response.data[0]['member_count'], 1)
        self.assertEqual(response.data[0]['project_count'], 1)

    def test_list_departments_non_member_forbidden(self):
        client = self.get_auth_client(self.non_member)
        url = reverse('dept-list', kwargs={'oid': self.org.id})
        response = client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_create_department_by_owner_success(self):
        client = self.get_auth_client(self.org_owner)
        url = reverse('dept-list', kwargs={'oid': self.org.id})
        data = {
            'name': 'Marketing',
            'description': 'Marketing Division',
            'head_id': self.org_member.id
        }
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Marketing')
        self.assertEqual(response.data['head']['email'], self.org_member.email)

    def test_create_department_by_admin_success(self):
        client = self.get_auth_client(self.admin)
        url = reverse('dept-list', kwargs={'oid': self.org.id})
        data = {
            'name': 'Sales',
            'description': 'Sales Division'
        }
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_create_department_by_member_forbidden(self):
        client = self.get_auth_client(self.org_member)
        url = reverse('dept-list', kwargs={'oid': self.org.id})
        data = {
            'name': 'Finance',
        }
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_retrieve_department_success(self):
        client = self.get_auth_client(self.org_member)
        url = reverse('dept-detail', kwargs={'oid': self.org.id, 'pk': self.department.id})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Engineering')

    def test_update_department_success(self):
        client = self.get_auth_client(self.org_owner)
        url = reverse('dept-detail', kwargs={'oid': self.org.id, 'pk': self.department.id})
        data = {'description': 'New Description'}
        response = client.patch(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['description'], 'New Description')

    def test_delete_department_success(self):
        client = self.get_auth_client(self.org_owner)
        url = reverse('dept-detail', kwargs={'oid': self.org.id, 'pk': self.department.id})
        response = client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Department.objects.filter(id=self.department.id).exists())

    def test_get_department_projects_success(self):
        client = self.get_auth_client(self.org_member)
        url = reverse('dept-project-list', kwargs={'oid': self.org.id, 'pk': self.department.id})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Project A')
