from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
import uuid
from django.utils import timezone
from .manager import *
from .validators import *
from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings



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





class PhoneOTP(models.Model):
    """
    One row per OTP sent. The code is HASHED (like a password) so a DB leak
    doesn't leak live OTPs. Old OTPs are kept for auditing/experimenting.
    """
 
    class Purpose(models.TextChoices):
        LOGIN = "login", "Login"
        REGISTER = "register", "Register"
 
    MAX_ATTEMPTS = 5
 
    phone_number = models.CharField(max_length=16, validators=[phone_validator])
    code_hash = models.CharField(max_length=128)
    purpose = models.CharField(max_length=10, choices=Purpose.choices)
    attempts = models.PositiveSmallIntegerField(default=0)
    # True once consumed OR invalidated by a newer OTP
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["phone_number", "purpose", "is_used", "-created_at"])]
        verbose_name = "phone OTP"
 
    def __str__(self):
        return f"{self.phone_number} [{self.purpose}] @ {self.created_at:%Y-%m-%d %H:%M:%S}"
 
    def set_code(self, raw_code: str):
        self.code_hash = make_password(raw_code)
 
    def check_code(self, raw_code: str) -> bool:
        return check_password(raw_code, self.code_hash)
 
    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at
 
    @property
    def attempts_left(self) -> int:
        return max(self.MAX_ATTEMPTS - self.attempts, 0)
 
 
class LoginActivity(models.Model):
    """Audit log: who logged in/registered/failed, from where."""
 
    class Event(models.TextChoices):
        OTP_SENT = "otp_sent", "OTP sent"
        OTP_FAILED = "otp_failed", "OTP failed"
        LOGIN = "login", "Login"
        REGISTER = "register", "Register"
        LOGOUT = "logout", "Logout"
        LOGOUT_ALL = "logout_all", "Logout all devices"
        DEACTIVATED = "deactivated", "Account deactivated"
 
    # user = models.ForeignKey(
    #     "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
    #     related_name="activities",
    # )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="activities",
    )
    phone_number = models.CharField(max_length=16)
    event = models.CharField(max_length=20, choices=Event.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "login activities"
 
    def __str__(self):
        return f"{self.phone_number} - {self.event} - {self.created_at:%Y-%m-%d %H:%M}"






