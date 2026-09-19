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