from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm

from .models import LoginActivity, PhoneOTP, User


class UserAdminCreationForm(forms.ModelForm):
    """Password is optional: only staff need one (to log into /admin)."""

    password1 = forms.CharField(
        label="Password (optional – only for staff)",
        widget=forms.PasswordInput, required=False,
    )

    class Meta:
        model = User
        fields = ("phone_number", "first_name", "last_name", "email", "is_staff")

    def save(self, commit=True):
        user = super().save(commit=False)
        pw = self.cleaned_data.get("password1")
        if pw:
            user.set_password(pw)
        else:
            user.set_unusable_password()
        if commit:
            user.save()
        return user


class UserAdminChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


class LoginActivityInline(admin.TabularInline):
    model = LoginActivity
    extra = 0
    can_delete = False
    fields = ("event", "ip_address", "user_agent", "created_at")
    readonly_fields = fields
    ordering = ("-created_at",)
    max_num = 0  # hides "add another"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    inlines = [LoginActivityInline]

    list_display = ("phone_number", "display_name", "email", "is_phone_verified",
                    "is_active", "is_staff", "date_joined", "last_login")
    list_filter = ("is_active", "is_staff", "is_superuser", "is_phone_verified",
                   "is_email_verified", "gender", "date_joined")
    search_fields = ("phone_number", "first_name", "last_name", "email")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "updated_at", "last_login")
    list_per_page = 25
    actions = ["activate_users", "deactivate_users"]

    fieldsets = (
        (None, {"fields": ("id", "phone_number", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email",
                                      "date_of_birth", "gender", "avatar_url")}),
        ("Verification", {"fields": ("is_phone_verified", "is_email_verified")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser",
                                    "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "updated_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone_number", "first_name", "last_name", "email",
                       "is_staff", "password1"),
        }),
    )

    @admin.display(description="Name")
    def display_name(self, obj):
        return obj.full_name or "—"

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_active=True)} user(s) activated.")

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_active=False)} user(s) deactivated.")


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "purpose", "attempts", "is_used",
                    "expired", "created_at", "expires_at", "verified_at")
    list_filter = ("purpose", "is_used", "created_at")
    search_fields = ("phone_number",)
    readonly_fields = [f.name for f in PhoneOTP._meta.fields]

    @admin.display(boolean=True, description="Expired")
    def expired(self, obj):
        return obj.is_expired

    def has_add_permission(self, request):
        return False


@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "user", "event", "ip_address", "created_at")
    list_filter = ("event", "created_at")
    search_fields = ("phone_number", "ip_address", "user__first_name", "user__email")
    readonly_fields = [f.name for f in LoginActivity._meta.fields]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False