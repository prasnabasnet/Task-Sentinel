from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_projects",
        help_text="The user who owns this project. Cannot be deleted while owning a project.",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="projects.ProjectMember",
        related_name="member_projects",
    )
    department = models.ForeignKey(
        "department.Department",
        on_delete=models.CASCADE,
        related_name="projects",
        help_text="The department this project belongs to.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.name
