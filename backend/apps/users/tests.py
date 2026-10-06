from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.users.models import Profile

User = get_user_model()


class AuthAPITestCase(TestCase):
    """
    Tests for Registration, Login, Logout, and the 'Me' profile endpoint.
    """

    def setUp(self):
        self.client = APIClient()
        # Created with mandatory username
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            role="TM",
        )
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.me_url = reverse("me")

    def test_register_success(self):
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "NewPass123",
            "organization_name": "Acme Corp",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["email"], "newuser@example.com")
        self.assertEqual(response.data["user"]["username"], "newuser")
        user = User.objects.get(email="newuser@example.com")
        self.assertEqual(user.role, "ORG_ADMIN")

    def test_register_creates_org_admin(self):
        data = {
            "email": "attacker@example.com",
            "username": "attacker",
            "password": "AttackPass123",
            "organization_name": "Initech",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="attacker@example.com")
        self.assertEqual(user.role, "ORG_ADMIN")


    def test_login_success(self):
        data = {"email": "test@example.com", "password": "testpass123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_login_invalid_password(self):
        data = {"email": "test@example.com", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"], "Invalid email or password.")

    def test_logout_authenticated(self):
        # Obtain token
        login_data = {"email": "test@example.com", "password": "testpass123"}
        login_response = self.client.post(self.login_url, login_data, format="json")
        token = login_response.data["token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Successfully logged out.")
        # Token should be deleted from DB
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_me_authenticated(self):
        login_data = {"email": "test@example.com", "password": "testpass123"}
        login_response = self.client.post(self.login_url, login_data, format="json")
        token = login_response.data["token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["role"], "TM")

    def test_me_unauthenticated(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 401)


class UserViewSetTestCase(TestCase):
    """
    Tests for the User Admin ViewSet (Admin access to all users).
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@example.com",
            username="admin_user",
            password="adminpass123",
            role="ADMIN",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            username="member_user",
            password="memberpass123",
            role="TM",
        )
        self.admin_token = Token.objects.create(user=self.admin)
        self.member_token = Token.objects.create(user=self.member)
        self.list_url = "/api/users/"

    def _auth_as(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_list_users_as_admin(self):
        self._auth_as(self.admin_token)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        # Verify both users are present in the list
        emails = [u["email"] for u in response.data]
        self.assertIn("member@example.com", emails)
        self.assertIn("admin@example.com", emails)

    def test_list_users_as_non_admin_forbidden(self):
        self._auth_as(self.member_token)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 403)

    def test_retrieve_user_as_admin(self):
        self._auth_as(self.admin_token)
        response = self.client.get(f"{self.list_url}{self.member.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "member_user")

    def test_partial_update_role_as_admin(self):
        self._auth_as(self.admin_token)
        response = self.client.patch(
            f"{self.list_url}{self.member.id}/", {"role": "PM"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, "PM")

    def test_destroy_soft_deletes_as_admin(self):
        self._auth_as(self.admin_token)
        response = self.client.delete(f"{self.list_url}{self.member.id}/")
        self.assertEqual(response.status_code, 204)
        self.member.refresh_from_db()
        # Custom logic: destroy sets is_active to False
        self.assertFalse(self.member.is_active)
        self.assertTrue(User.objects.filter(id=self.member.id).exists())

    def test_destroy_as_non_admin_forbidden(self):
        self._auth_as(self.member_token)
        response = self.client.delete(f"{self.list_url}{self.admin.id}/")
        self.assertEqual(response.status_code, 403)

    def test_list_users_includes_nested_profile(self):
        self._auth_as(self.admin_token)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        member_data = next(
            u for u in response.data if u["email"] == "member@example.com"
        )
        self.assertIn("profile", member_data)
        self.assertIn("avatar_url", member_data["profile"])


class ProfileAPITestCase(TestCase):
    """
    Tests for the Profile model, its auto-creation signal, and the
    profile-editing surface exposed on /api/users/auth/me/.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="profile_test@example.com",
            username="profile_tester",
            password="testpass123",
            role="TM",
        )
        self.me_url = reverse("me")
        self.token = Token.objects.create(user=self.user)

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_profile_auto_created_on_user_creation(self):
        # The signal should have fired during setUp's create_user call
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_profile_defaults(self):
        profile = self.user.profile
        self.assertEqual(profile.bio, "")
        self.assertEqual(profile.display_name, "")
        self.assertIsNone(profile.avatar_url)

    def test_get_or_create_is_idempotent_for_backfill(self):
        # Simulates re-running the backfill script against a user that
        # already has a profile; should not create a duplicate or raise.
        _, created_first = Profile.objects.get_or_create(user=self.user)
        _, created_second = Profile.objects.get_or_create(user=self.user)
        self.assertFalse(created_first)
        self.assertFalse(created_second)
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)

    def test_me_get_includes_profile_block(self):
        self._auth()
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("profile", response.data)
        self.assertEqual(response.data["profile"]["bio"], "")

    def test_me_patch_updates_profile_fields(self):
        self._auth()
        data = {
            "display_name": "Azhar K",
            "bio": "Backend intern",
            "avatar_url": "https://example.com/avatar.jpg",
        }
        response = self.client.patch(self.me_url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["display_name"], "Azhar K")
        self.assertEqual(response.data["profile"]["bio"], "Backend intern")

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.display_name, "Azhar K")

    def test_me_patch_partial_update_only_changes_given_fields(self):
        self._auth()
        self.client.patch(self.me_url, {"bio": "Original bio"}, format="json")
        response = self.client.patch(
            self.me_url, {"display_name": "New Name"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["display_name"], "New Name")
        # bio should be untouched by the second partial patch
        self.assertEqual(response.data["profile"]["bio"], "Original bio")

    def test_me_patch_cannot_change_email(self):
        self._auth()
        original_email = self.user.email
        response = self.client.patch(
            self.me_url, {"email": "hacked@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, original_email)

    def test_me_patch_cannot_change_role(self):
        self._auth()
        response = self.client.patch(self.me_url, {"role": "ADMIN"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "TM")

    def test_me_patch_unauthenticated_denied(self):
        response = self.client.patch(self.me_url, {"bio": "test"}, format="json")
        self.assertEqual(response.status_code, 401)


class UserServiceTestCase(TestCase):
    def test_service_register_user(self):
        from apps.users.services import RegisterUserService

        data = {
            "email": "serviceuser@example.com",
            "username": "serviceuser",
            "password": "ServicePass123",
            "organization_name": "Test Org",
        }
        user, token = RegisterUserService.execute(data=data)
        self.assertEqual(user.email, "serviceuser@example.com")
        self.assertEqual(user.role, "ORG_ADMIN")
        self.assertIsNotNone(token.key)


    def test_service_authenticate_user(self):
        from apps.users.services import AuthenticateUserService

        User.objects.create_user(
            email="authservice@example.com",
            username="authservice",
            password="Password123",
        )
        user, token = AuthenticateUserService.execute(
            email="authservice@example.com", password="Password123"
        )
        self.assertEqual(user.email, "authservice@example.com")
        self.assertIsNotNone(token.key)

    def test_service_deactivate_user(self):
        from apps.users.services import DeactivateUserService

        user = User.objects.create_user(
            email="deact@example.com", username="deactuser", password="Password123"
        )
        DeactivateUserService.execute(user=user)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
