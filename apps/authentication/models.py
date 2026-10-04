from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
import uuid
from django.utils import timezone
from .manager import *



class User(AbstractBaseUser,PermissionsMixin):


    class Gender(models.TextChoices):
        MALE="M","Male"
        FEMALE="F","Female"
        OTHER="o","Other"
        NOT_SAID="N","Perfer not to say"

    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    phone_number=models.CharField(
        max_length=16,unique=True
    )
    first_name=models.CharField(max_length=150,blank=True)
    last_name=models.CharField(max_length=150,blank=True)


    email=models.EmailField(unique=True,null=True,blank=True)
    date_of_birth=models.DateField(null=True,blank=True)
    gender=models.CharField(max_length=1,choices=Gender.choices,blank=True)
    avatar_url=models.URLField(blank=True)


    ###-----status flags-----
    is_phone_verified=models.BooleanField(default=False)
    is_email_verified=models.BooleanField(default=False)

    is_active=models.BooleanField(default=True)
    is_staff=models.BooleanField(default=False)


    date_joined=models.DateTimeField(default=timezone.now)
    updated_at=models.DateTimeField(auto_now=True)

    objects=UserManager()

    USERNAME_FIELD="phone_number"
    REQUIRED_FIELDS=[]


    class Meta:
        ordering=["-date_joined"]
        verbose_name="user"
        verbose_name_plural="users"

    def __str__(self):
        return self.full_name or self.phone_number


    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self,*args,**kwargs):
        self.email=self.email.strip().lower() if self.email else None
        super().save(*args,**kwargs)











