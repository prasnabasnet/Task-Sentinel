import logging

from django.contrib.auth import authenticate, get_user_model
from django.db import models, transaction
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from apps.organization.models import Organization, OrganizationMember
from apps.shared.services import BaseService
from apps.shared.tasks import send_member_welcome_email_task, send_welcome_email_task
from apps.users.models import Profile, RoleChoices
from apps.users.serializers import ProfileUpdateSerializer, UserRegisterSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterUserService(BaseService):
    def process(self):
        organization_name = self.data.get("organization_name")
        if not organization_name:
            raise ValidationError({"organization_name": "Organization name is required."})

        if Organization.objects.filter(name__iexact=organization_name.strip()).exists():
            raise ValidationError({"organization_name": f"An organization named '{organization_name}' already exists."})

        serializer = self.validate_serializer(UserRegisterSerializer, self.data)
        user = serializer.save()

        # Atomically create Organization for ORG_ADMIN
        org = Organization.objects.create(
            name=organization_name.strip(),
            owner=user,
        )
        OrganizationMember.objects.create(organization=org, user=user)

        token, _ = Token.objects.get_or_create(user=user)
        transaction.on_commit(lambda: send_welcome_email_task.delay(user.id))
        return user, token



class CreateMemberService(BaseService):
    def validate(self):
        if not self.user or not self.user.is_authenticated:
            raise ValidationError("Authentication required.")
        if self.user.role not in (RoleChoices.SUPERADMIN, RoleChoices.ORG_ADMIN) and not self.user.is_superuser:
            raise ValidationError("Only ORG_ADMIN can create organization members.")

    def process(self):
        email = self.data.get("email")
        username = self.data.get("username")
        password = self.data.get("password")
        role = self.data.get("role", RoleChoices.TM)

        if not email or not username or not password:
            raise ValidationError("email, username, and password are required.")

        if role not in (RoleChoices.PM, RoleChoices.TM):
            raise ValidationError("Role must be PM or TM.")

        # Find user's organization
        org = Organization.objects.filter(owner=self.user).first()
        if not org:
            membership = OrganizationMember.objects.filter(user=self.user).first()
            org = membership.organization if membership else None

        if not org:
            raise ValidationError("Organization not found for the requesting admin.")

        new_user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            role=role,
        )
        OrganizationMember.objects.create(organization=org, user=new_user)

        department_id = self.data.get("department_id")
        if department_id:
            from apps.department.models import Department
            dept = Department.objects.filter(id=department_id, organization=org).first()
            if dept:
                dept.members.add(new_user)

        transaction.on_commit(
            lambda: send_member_welcome_email_task.delay(
                email=new_user.email,
                raw_password=password,
                organization_name=org.name,
            )
        )
        return new_user



class AuthenticateUserService(BaseService):
    def validate(self):
        if not getattr(self, "email", None) or not getattr(self, "password", None):
            raise ValidationError("Email and password are required.")

    def process(self):
        request = getattr(self, "request", None)
        user = authenticate(request, username=self.email, password=self.password)

        if user is None:
            raise AuthenticationFailed("Invalid email or password.")

        token, _ = Token.objects.get_or_create(user=user)
        return user, token


class LogoutUserService(BaseService):
    def process(self):
        if self.request and self.request.auth:
            self.request.auth.delete()


class UpdateProfileService(BaseService):
    def process(self):
        profile, _ = Profile.objects.get_or_create(user=self.user)
        serializer = self.validate_serializer(
            ProfileUpdateSerializer, self.data, instance=profile, partial=True
        )
        serializer.save()

        self.user.refresh_from_db()
        return self.user


class DeactivateUserService(BaseService):
    def process(self):
        user = self.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        return user


class GetAllUsersService(BaseService):
    def process(self):
        user = self.user
        if getattr(user, "role", "") == "SUPERADMIN" or getattr(user, "is_superuser", False):
            return User.objects.select_related("profile").all()
        
        # Scoped to ORG_ADMIN's organization members
        org = Organization.objects.filter(owner=user).first()
        if not org:
            membership = OrganizationMember.objects.filter(user=user).first()
            org = membership.organization if membership else None

        if not org:
            return User.objects.none()

        return User.objects.select_related("profile").filter(
            models.Q(owned_organization=org) | models.Q(organization_memberships__organization=org)
        ).distinct()

