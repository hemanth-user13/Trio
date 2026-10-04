from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .validators import normalize_phone_number

User = get_user_model()


class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        try:
            return normalize_phone_number(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)


class VerifyOTPSerializer(PhoneNumberSerializer):
    otp = serializers.RegexField(
        regex=r"^\d{4,6}$",
        error_messages={"invalid": "OTP must be 4-6 digits."},
    )


class RegisterSerializer(VerifyOTPSerializer):
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    def validate_phone_number(self, value):
        value = super().validate_phone_number(value)
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This number is already registered. Please login.")
        return value

    def validate_email(self, value):
        if not value:
            return None
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class UserSerializer(serializers.ModelSerializer):
    """Read-only representation returned to clients."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "phone_number", "first_name", "last_name", "full_name",
            "email", "date_of_birth", "gender", "avatar_url",
            "is_phone_verified", "is_email_verified",
            "date_joined", "last_login",
        ]
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    What a user may edit on their own profile.
    phone_number is deliberately NOT here: changing it should need a new OTP
    (good experiment: build a 'change phone' flow!).
    """

    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "date_of_birth", "gender", "avatar_url"]

    def validate_email(self, value):
        if not value:
            return None
        value = value.lower()
        qs = User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def update(self, instance, validated_data):
        if "email" in validated_data and validated_data["email"] != instance.email:
            instance.is_email_verified = False  # new email must be re-verified
        return super().update(instance, validated_data)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()