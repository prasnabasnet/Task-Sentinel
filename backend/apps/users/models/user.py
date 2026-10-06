from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.users.models.usermanager import UserManager


class RoleChoices(models.TextChoices):
    SUPERADMIN = "SUPERADMIN", "Super Admin"
    ORG_ADMIN = "ORG_ADMIN", "Org Admin"
    PM = "PM", "Project Manager"
    TM = "TM", "Team Member"


class User(AbstractUser):
    objects = UserManager()

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=15, choices=RoleChoices.choices, default=RoleChoices.TM
    )

    USERNAME_FIELD = "email"
    # REQUIRED_FIELDS = ["username", "role"]
    REQUIRED_FIELDS = ("username",)

    @property
    def is_admin(self):
        return self.role in (RoleChoices.SUPERADMIN, RoleChoices.ORG_ADMIN) or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.email})"

