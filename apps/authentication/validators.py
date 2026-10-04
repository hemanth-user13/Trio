import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

# We always STORE numbers in E.164 format: "+" + country code + number
# e.g. +919876543210
E164_REGEX = r"^\+[1-9]\d{9,14}$"

phone_validator = RegexValidator(
    regex=E164_REGEX,
    message="Phone number must be in E.164 format, e.g. +919876543210",
)


def normalize_phone_number(value: str) -> str:
    """
    Accepts user-friendly input and converts it to E.164.
      "98765 43210"      -> "+919876543210"  (uses DEFAULT_COUNTRY_CODE)
      "0091-9876543210"  -> "+919876543210"
      "+91 98765-43210"  -> "+919876543210"
    """
    if not value:
        raise ValidationError("Phone number is required.")

    value = re.sub(r"[\s\-().]", "", value.strip())

    if value.startswith("00"):
        value = "+" + value[2:]

    if not value.startswith("+"):
        if len(value) == 10:  # local number without country code
            value = getattr(settings, "DEFAULT_COUNTRY_CODE", "+91") + value
        else:
            value = "+" + value

    if not re.fullmatch(E164_REGEX, value):
        raise ValidationError("Enter a valid phone number, e.g. +919876543210")

    return value