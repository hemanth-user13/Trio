from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from .models import LoginActivity, PhoneOTP
from .serializers import (
    LogoutSerializer, PhoneNumberSerializer, RegisterSerializer,
    UserSerializer, UserUpdateSerializer, VerifyOTPSerializer,
)
from .services import (
    OTP_EXPIRY_SECONDS, create_and_send_otp, get_tokens_for_user,
    log_activity, otp_cooldown_remaining, verify_otp,
)

User = get_user_model()

# Status code used when the phone number is NOT in the DB.
# 404 = "user not found". Change to 200 if your frontend prefers
# to read only the `code` / `is_registered` fields.
UNREGISTERED_STATUS = status.HTTP_404_NOT_FOUND


def api_response(status_text, code, message, data=None, http_status=status.HTTP_200_OK):
    """Consistent envelope: {status, code, message, data}."""
    body = {"status": status_text, "code": code, "message": message}
    if data is not None:
        body["data"] = data
    return Response(body, status=http_status)


class PublicAPIView(APIView):
    """
    For endpoints used BEFORE login.
    authentication_classes = [] so an expired token in the header
    doesn't cause a 401 on the login screen.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]


# ------------------------------------------------------------------ Step 1
class SendOTPView(PublicAPIView):
    """
    POST /api/auth/otp/send/   {"phone_number": "9876543210"}

    200 USER_EXISTS          -> go to login (otp/verify/)
    404 USER_NOT_REGISTERED  -> go to register (register/)
    403 ACCOUNT_DISABLED
    429 OTP_COOLDOWN
    """
    throttle_scope = "otp_send"

    def post(self, request):
        serializer = PhoneNumberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]

        user = User.objects.filter(phone_number=phone).first()
        if user and not user.is_active:
            return api_response("error", "ACCOUNT_DISABLED",
                                "This account has been disabled.",
                                http_status=status.HTTP_403_FORBIDDEN)

        wait = otp_cooldown_remaining(phone)
        if wait > 0:
            return api_response("error", "OTP_COOLDOWN",
                                f"Please wait {wait}s before requesting another OTP.",
                                data={"retry_after": wait},
                                http_status=status.HTTP_429_TOO_MANY_REQUESTS)

        purpose = PhoneOTP.Purpose.LOGIN if user else PhoneOTP.Purpose.REGISTER
        raw_code = create_and_send_otp(phone, purpose)
        log_activity(request, LoginActivity.Event.OTP_SENT, phone, user)

        data = {
            "phone_number": phone,
            "is_registered": user is not None,
            "otp_expires_in": OTP_EXPIRY_SECONDS,
        }
        if settings.DEBUG:
            data["debug_otp"] = raw_code  # NEVER do this in production

        if user:
            return api_response("ok", "USER_EXISTS",
                                "OTP sent. Verify it to log in.", data)

        return api_response("register", "USER_NOT_REGISTERED",
                            "Number not registered. OTP sent, complete registration.",
                            data, http_status=UNREGISTERED_STATUS)


# ------------------------------------------------------------------ Step 2a
class LoginView(PublicAPIView):
    """POST /api/auth/otp/verify/   {"phone_number": "...", "otp": "123456"}"""
    throttle_scope = "otp_verify"

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp"]

        user = User.objects.filter(phone_number=phone).first()
        if user is None:
            return api_response("register", "USER_NOT_REGISTERED",
                                "Number not registered. Please register.",
                                http_status=UNREGISTERED_STATUS)
        if not user.is_active:
            return api_response("error", "ACCOUNT_DISABLED",
                                "This account has been disabled.",
                                http_status=status.HTTP_403_FORBIDDEN)

        result = verify_otp(phone, otp, PhoneOTP.Purpose.LOGIN)
        if not result.ok:
            log_activity(request, LoginActivity.Event.OTP_FAILED, phone, user)
            return api_response("error", result.code, result.message,
                                http_status=status.HTTP_400_BAD_REQUEST)

        if not user.is_phone_verified:
            user.is_phone_verified = True
            user.save(update_fields=["is_phone_verified"])

        update_last_login(None, user)
        log_activity(request, LoginActivity.Event.LOGIN, phone, user)

        return api_response("ok", "LOGIN_SUCCESS", "Logged in successfully.", {
            "tokens": get_tokens_for_user(user),
            "user": UserSerializer(user).data,
        })


# ------------------------------------------------------------------ Step 2b
class RegisterView(PublicAPIView):
    """
    POST /api/auth/register/
    {"phone_number": "...", "otp": "123456",
     "first_name": "optional", "last_name": "optional", "email": "optional"}
    """
    throttle_scope = "otp_verify"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone = data["phone_number"]

        result = verify_otp(phone, data["otp"], PhoneOTP.Purpose.REGISTER)
        if not result.ok:
            log_activity(request, LoginActivity.Event.OTP_FAILED, phone)
            return api_response("error", result.code, result.message,
                                http_status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.create_user(
                phone_number=phone,
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                email=data.get("email"),
                is_phone_verified=True,
            )

        update_last_login(None, user)
        log_activity(request, LoginActivity.Event.REGISTER, phone, user)

        return api_response("ok", "REGISTER_SUCCESS", "Account created.", {
            "tokens": get_tokens_for_user(user),
            "user": UserSerializer(user).data,
        }, http_status=status.HTTP_201_CREATED)


# ------------------------------------------------------------------ Logged in
class LogoutView(APIView):
    """POST /api/auth/logout/   {"refresh": "<refresh token>"}  (needs Bearer access token)"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            if str(token.get("user_id")) != str(request.user.id):
                return api_response("error", "TOKEN_MISMATCH",
                                    "Refresh token does not belong to this user.",
                                    http_status=status.HTTP_400_BAD_REQUEST)
            token.blacklist()
        except TokenError:
            return api_response("error", "TOKEN_INVALID",
                                "Token is invalid or already blacklisted.",
                                http_status=status.HTTP_400_BAD_REQUEST)

        log_activity(request, LoginActivity.Event.LOGOUT, request.user.phone_number, request.user)
        return api_response("ok", "LOGOUT_SUCCESS", "Logged out.")


class LogoutAllView(APIView):
    """POST /api/auth/logout-all/  -> blacklists every refresh token of this user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        tokens = OutstandingToken.objects.filter(user=request.user)
        for t in tokens:
            BlacklistedToken.objects.get_or_create(token=t)

        log_activity(request, LoginActivity.Event.LOGOUT_ALL, request.user.phone_number, request.user)
        return api_response("ok", "LOGOUT_ALL_SUCCESS",
                            f"Logged out from {tokens.count()} session(s).")


class MeView(PublicAPIView):
    """
    GET    /api/auth/me/   -> profile
    PATCH  /api/auth/me/   -> update profile
    DELETE /api/auth/me/   -> deactivate account (soft delete)
    """

    def get(self, request):
        return api_response("ok", "PROFILE", "Profile fetched.", UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_response("ok", "PROFILE_UPDATED", "Profile updated.",
                            UserSerializer(request.user).data)

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        for t in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=t)

        log_activity(request, LoginActivity.Event.DEACTIVATED, user.phone_number, user)
        return api_response("ok", "ACCOUNT_DEACTIVATED", "Account deactivated.")