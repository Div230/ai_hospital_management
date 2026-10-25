from django.urls import path
from .session_views import RefreshCookieView, LogoutView
from .views import (
    RegisterView, LoginView, VerifyEmailView, ForgotPasswordView,
    ResetPasswordView, ChangePasswordView, MeView,
)
from .twofa_views import (
    TwoFactorSetupView, TwoFactorEnableView, TwoFactorDisableView, TwoFactorLoginVerifyView,
)

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', RefreshCookieView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('me/', MeView.as_view(), name='me'),
    path('2fa/setup/', TwoFactorSetupView.as_view(), name='2fa_setup'),
    path('2fa/enable/', TwoFactorEnableView.as_view(), name='2fa_enable'),
    path('2fa/disable/', TwoFactorDisableView.as_view(), name='2fa_disable'),
    path('2fa/login-verify/', TwoFactorLoginVerifyView.as_view(), name='2fa_login_verify'),
]
