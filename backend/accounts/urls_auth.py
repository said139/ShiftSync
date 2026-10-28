from django.urls import path
from .views import (
    ChangePasswordAPIView,
    CurrentUserProfileAPIView,
    LoginAPIView,
    LogoutAPIView,
    PasswordRecoveryRequestAPIView,
    PasswordResetConfirmAPIView,
    RefreshTokenAPIView,
    RegisterAPIView,
    TestEmailAPIView,
)

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="auth-register"),
    path("login/", LoginAPIView.as_view(), name="auth-login"),
    path("refresh/", RefreshTokenAPIView.as_view(), name="auth-refresh"),
    path("logout/", LogoutAPIView.as_view(), name="auth-logout"),
    path("me/", CurrentUserProfileAPIView.as_view(), name="auth-me"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="auth-change-password"),
    path("password-recovery/", PasswordRecoveryRequestAPIView.as_view(), name="auth-password-recovery"),
    path("password-reset/", PasswordResetConfirmAPIView.as_view(), name="auth-password-reset"),
    path("test-email/", TestEmailAPIView.as_view(), name="auth-test-email"),
]
