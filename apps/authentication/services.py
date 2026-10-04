"""
Business logic lives here so views stay thin and this is easy to unit-test.
"""
import logging
import secrets
from datetime import timedelta
from typing import NamedTuple

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .models import LoginActivity, PhoneOTP

logger = logging.getLogger(__name__)

OTP_USE_DUMMY = getattr(settings, "OTP_USE_DUMMY", True)
OTP_DUMMY_CODE = getattr(settings, "OTP_DUMMY_CODE", "123456")
OTP_LENGTH = getattr(settings, "OTP_LENGTH", 6)
OTP_EXPIRY_SECONDS = getattr(settings, "OTP_EXPIRY_SECONDS", 300)
OTP_RESEND_COOLDOWN_SECONDS = getattr(settings, "OTP_RESEND_COOLDOWN_SECONDS", 30)


class OTPResult(NamedTuple):
    ok: bool
    code: str      # machine-readable code for the frontend
    message: str   # human-readable message


# ---------------------------------------------------------------- OTP
def generate_otp_code() -> str:
    if OTP_USE_DUMMY:
        return OTP_DUMMY_CODE
    return f"{secrets.randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}"


def send_sms(phone_number: str, code: str) -> None:
    """Replace with Twilio / MSG91 / AWS SNS etc. later."""
    logger.info("[DUMMY SMS] OTP for %s is %s", phone_number, code)


def otp_cooldown_remaining(phone_number: str) -> int:
    """Seconds the user must wait before requesting another OTP (0 = allowed)."""
    last = PhoneOTP.objects.filter(phone_number=phone_number).only("created_at").first()
    if not last:
        return 0
    elapsed = (timezone.now() - last.created_at).total_seconds()
    return max(int(OTP_RESEND_COOLDOWN_SECONDS - elapsed), 0)


@transaction.atomic
def create_and_send_otp(phone_number: str, purpose: str) -> str:
    # Invalidate any previous unused OTPs for this number
    PhoneOTP.objects.filter(phone_number=phone_number, is_used=False).update(is_used=True)

    raw_code = generate_otp_code()
    otp = PhoneOTP(
        phone_number=phone_number,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(seconds=OTP_EXPIRY_SECONDS),
    )
    otp.set_code(raw_code)
    otp.save()

    send_sms(phone_number, raw_code)
    return raw_code


@transaction.atomic
def verify_otp(phone_number: str, raw_code: str, purpose: str) -> OTPResult:
    otp = (
        PhoneOTP.objects.select_for_update()  # avoid two parallel requests using one OTP
        .filter(phone_number=phone_number, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if otp is None:
        return OTPResult(False, "OTP_NOT_FOUND", "No active OTP. Please request a new one.")
    if otp.is_expired:
        return OTPResult(False, "OTP_EXPIRED", "OTP has expired. Please request a new one.")
    if otp.attempts >= PhoneOTP.MAX_ATTEMPTS:
        return OTPResult(False, "OTP_MAX_ATTEMPTS", "Too many wrong attempts. Request a new OTP.")

    if not otp.check_code(raw_code):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        return OTPResult(False, "OTP_INVALID", f"Invalid OTP. {otp.attempts_left} attempt(s) left.")

    otp.is_used = True
    otp.verified_at = timezone.now()
    otp.save(update_fields=["is_used", "verified_at"])
    return OTPResult(True, "OTP_VERIFIED", "OTP verified.")


# ---------------------------------------------------------------- JWT
def get_tokens_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)
    # Custom claims (copied into the access token too). Don't put secrets here,
    # JWT payloads are only base64-encoded, not encrypted.
    refresh["phone_number"] = user.phone_number
    refresh["is_staff"] = user.is_staff

    access = refresh.access_token
    return {
        "access": str(access),
        "refresh": str(refresh),
        "token_type": "Bearer",
        "access_expires_in": int(access.lifetime.total_seconds()),
        "refresh_expires_in": int(refresh.lifetime.total_seconds()),
    }


# ---------------------------------------------------------------- Audit
def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_activity(request, event, phone_number, user=None):
    LoginActivity.objects.create(
        user=user,
        phone_number=phone_number,
        event=event,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
    )