from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (
    LoginView, LogoutAllView, LogoutView, MeView, RegisterView, SendOTPView,
)

app_name = "accounts"

urlpatterns = [
    path("otp/send/", SendOTPView.as_view(), name="send-otp"),
    path("otp/verify/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logout-all/", LogoutAllView.as_view(), name="logout-all"),
    path("me/", MeView.as_view(), name="me"),
]