from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
# Register your models here.

from .models import *


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass

admin.site.register(DemoData)

admin.site.register(Organization)

admin.site.register(OrganizationMembership)

