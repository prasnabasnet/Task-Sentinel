from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.comments.models import Comment
from apps.organization.models import Organization
from apps.department.models import Department
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task

User = get_user_model()


class CommentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin_user",
            password="password123",
            role="ADMIN",
        )
        self.pm_user = User.objects.create_user(
            email="pm@example.com",
            password="password123",
            role="PM",
            username="pm_user",
        )
        self.dev_user = User.objects.create_user(
            email="dev@example.com",
            password="password123",
            role="TM",
            username="dev_user",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            role="TM",
            username="other_user",
        )

        self.org = Organization.objects.create(name="Comment Org", owner=self.pm_user)
        self.dept = Department.objects.create(organization=self.org, name="Comment Dept")
        self.project = Project.objects.create(name="Test Project", owner=self.pm_user, department=self.dept)
        ProjectMember.objects.create(project=self.project, user=self.dev_user)

        self.task = Task.objects.create(
            project=self.project, title="Test Task", created_by=self.pm_user
        )

        self.url = reverse("comment-list")

    def get_auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_post_comment_success(self):
        client = self.get_auth_client(self.dev_user)
        data = {
            "body": "This is a test comment.",
            "parent": None,
            "target_type": "task",
            "target_id": self.task.id,
        }
        response = client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["body"], "This is a test comment.")
        self.assertEqual(response.data["author"]["email"], self.dev_user.email)

    def test_post_comment_with_mention(self):
        client = self.get_auth_client(self.dev_user)
        data = {
            "body": "Hey @pm please look at this",
            "parent": None,
            "target_type": "task",
            "target_id": self.task.id,
        }
        response = client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201)

        comment = Comment.objects.get(id=response.data["id"])
        self.assertIn(self.pm_user, comment.mentions.all())
        self.assertEqual(comment.mentions.count(), 1)
        self.assertEqual(response.data["mentions"][0]["email"], self.pm_user.email)

    def test_post_comment_with_username_mention(self):
        client = self.get_auth_client(self.dev_user)
        data = {
            "body": "Hey @pm_user please look at this",
            "parent": None,
            "target_type": "task",
            "target_id": self.task.id,
        }
        response = client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201)

        comment = Comment.objects.get(id=response.data["id"])
        self.assertIn(self.pm_user, comment.mentions.all())
        self.assertEqual(comment.mentions.count(), 1)
        self.assertEqual(response.data["mentions"][0]["username"], "pm_user")

    def test_post_comment_with_punctuation_mention(self):
        client = self.get_auth_client(self.dev_user)
        data = {
            "body": "Hey @pm_user, can you check this out?",
            "parent": None,
            "target_type": "task",
            "target_id": self.task.id,
        }
        response = client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201)
        comment = Comment.objects.get(id=response.data["id"])
        self.assertIn(self.pm_user, comment.mentions.all())

    def test_post_comment_email_not_parsed_as_mention(self):
        client = self.get_auth_client(self.dev_user)
        data = {
            "body": "Contact me at dev@example.com for details",
            "parent": None,
            "target_type": "task",
            "target_id": self.task.id,
        }
        response = client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201)
        comment = Comment.objects.get(id=response.data["id"])
        self.assertEqual(comment.mentions.count(), 0)

    def test_threaded_replies(self):
        client = self.get_auth_client(self.dev_user)
        task_ct = ContentType.objects.get_for_model(self.task)
        parent = Comment.objects.create(
            content_type=task_ct,
            object_id=self.task.id,
            author=self.pm_user,
            body="Parent comment",
        )

        data = {"body": "This is a reply.", "parent": parent.id}
        response = client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["parent"], parent.id)

        get_response = client.get(
            self.url, {"target_type": "task", "target_id": self.task.id}
        )
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(get_response.data), 1)
        self.assertEqual(get_response.data[0]["id"], parent.id)
        self.assertEqual(len(get_response.data[0]["replies"]), 1)
        self.assertEqual(get_response.data[0]["replies"][0]["id"], response.data["id"])

    def test_edit_own_comment(self):
        task_ct = ContentType.objects.get_for_model(self.task)
        comment = Comment.objects.create(
            content_type=task_ct,
            object_id=self.task.id,
            author=self.dev_user,
            body="Old comment",
        )
        client = self.get_auth_client(self.dev_user)
        detail_url = reverse("comment-detail", kwargs={"pk": comment.id})

        data = {"body": "Updated comment content"}
        response = client.patch(detail_url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["body"], "Updated comment content")

    def test_edit_other_comment_fails(self):
        task_ct = ContentType.objects.get_for_model(self.task)
        comment = Comment.objects.create(
            content_type=task_ct,
            object_id=self.task.id,
            author=self.dev_user,
            body="Old comment",
        )
        client = self.get_auth_client(self.pm_user)
        detail_url = reverse("comment-detail", kwargs={"pk": comment.id})

        data = {"body": "Trying to update"}
        response = client.patch(detail_url, data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_delete_own_comment(self):
        task_ct = ContentType.objects.get_for_model(self.task)
        comment = Comment.objects.create(
            content_type=task_ct,
            object_id=self.task.id,
            author=self.dev_user,
            body="Comment to delete",
        )
        client = self.get_auth_client(self.dev_user)
        detail_url = reverse("comment-detail", kwargs={"pk": comment.id})

        response = client.delete(detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_delete_other_comment_fails(self):
        task_ct = ContentType.objects.get_for_model(self.task)
        comment = Comment.objects.create(
            content_type=task_ct,
            object_id=self.task.id,
            author=self.dev_user,
            body="Comment to delete",
        )
        client = self.get_auth_client(self.pm_user)
        detail_url = reverse("comment-detail", kwargs={"pk": comment.id})

        response = client.delete(detail_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())

    def test_non_project_member_denied(self):
        client = self.get_auth_client(self.other_user)

        data = {
            "body": "Denied comment",
            "parent": None,
            "target_type": "task",
            "target_id": self.task.id,
        }
        response_post = client.post(self.url, data, format="json")
        self.assertEqual(response_post.status_code, 403)

        response_get = client.get(
            self.url, {"target_type": "task", "target_id": self.task.id}
        )
        self.assertEqual(response_get.status_code, 403)

        task_ct = ContentType.objects.get_for_model(self.task)
        comment = Comment.objects.create(
            content_type=task_ct,
            object_id=self.task.id,
            author=self.dev_user,
            body="Secret comment",
        )
        detail_url = reverse("comment-detail", kwargs={"pk": comment.id})
        response_detail = client.get(detail_url)
        self.assertEqual(response_detail.status_code, 403)
