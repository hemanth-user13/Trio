from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser):
    pass


class DemoData(models.Model):
    first_name=models.CharField(max_length=200)
    last_name=models.TextField()


    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Organization(models.Model):
    name=models.CharField(max_length=40)
    slug=models.SlugField(unique=True)
    is_active=models.BooleanField(default=True)
    created_at=models.DateField(auto_now_add=True)
    updated_at=models.DateField(auto_now=True)
    
    def __str__(self):
        return f"{self.name}"
    
class OrganizationMembership(models.Model):
    user=models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="organization_memberships"
    )

    organization=models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships"
    )
    role=models.CharField(max_length=100)
    is_active=models.BooleanField(default=True)
    joined_at=models.DateField(auto_now_add=True)
    created_at=models.DateField(auto_now_add=True)
    updated_at=models.DateField(auto_now=True)

    class Meta:
        constraints=[
            models.UniqueConstraint(
                fields=["user","organization"],
                name="unique_user_organization"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.organization} - {self.role}"

