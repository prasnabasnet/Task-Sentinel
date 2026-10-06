from django.db import models
from django.utils.text import slugify

# Create your models here.
class Organization(models.Model):

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey('users.User',on_delete=models.PROTECT,related_name='owned_organization')
    slug = models.SlugField(max_length=250, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    members = models.ManyToManyField(
        'users.User',
        through='OrganizationMember',
        related_name='member_organizations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['name']

    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        


            



