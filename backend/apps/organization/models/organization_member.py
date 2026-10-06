from django.db import models
from apps.users.models import User
from apps.organization.models import Organization

class OrganizationMember(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        verbose_name = 'Organization Member'
        verbose_name_plural = 'Organization Members'

        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'user'],
                name='unique_organization_member')
        ]

        db_table = 'organization_member'

    def __str__(self):
        return f'{self.user} in {self.organization}'