from django.conf import settings
from django.db import models

from apps.shared.models.basemodel import BaseModel


class Profile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    display_name = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "users_profile"

    def __str__(self):
        return f"Profile for {self.user.username}"
