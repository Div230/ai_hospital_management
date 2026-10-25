import secrets
import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.core import signing
from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle

class LoginThrottle(AnonRateThrottle):
    scope = 'login'

from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .session_views import RefreshCookieMixin, check_origin
from .models import User, EmailVerificationToken, PasswordResetToken
from .serializers import (
    RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
)
from notifications.services import send_email_notification

logger = logging.getLogger('healthcare')


class RegisterView(generics.CreateAPIView):
    """Public registration is restricted to patients."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Fire off email verification token (console backend in demo mode)
        token = EmailVerificationToken.objects.create(
            user=user, token=secrets.token_urlsafe(32)
        )
        send_email_notification(
            to_email=user.email,
            subject='Verify your AIHMS account',
            message=(
                f'Hi {user.first_name}, verify your account using this token: '
                f'{token.token} (valid 24 hours).'
            ),
        )
        logger.info('Patient account registered')

        return Response(
            {
                'success': True,
                'message': 'Registration successful. Check your email to verify your account.',
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(RefreshCookieMixin, TokenObtainPairView):
    """
    JWT login. Returns access + refresh tokens plus user profile/role for
    users without 2FA. For users with 2FA enabled, returns
    {"requires_2fa": true, "user_id": ...} instead — the frontend must then
    call /api/auth/2fa/login-verify/ with a TOTP code to get actual tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        check_origin(request)
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user and user.is_active and user.is_2fa_enabled:
            # Validate password first without issuing tokens yet
            if not user.check_password(request.data.get('password', '')):
                return Response({'success': False, 'message': 'Invalid credentials.'}, status=401)
            nonce = secrets.token_urlsafe(32)
            cache.set('2fa:' + nonce, str(user.pk), timeout=300)
            challenge = signing.dumps({'user': str(user.pk), 'nonce': nonce}, salt='2fa-login')
            return Response({
                'challenge': challenge,
                'success': True,
                'requires_2fa': True,
                'user_id': user.id,
                'message': 'Enter your 2FA code to complete login.',
            })

        return super().post(request, *args, **kwargs)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token_str = request.data.get('token')
        try:
            token = EmailVerificationToken.objects.get(token=token_str)
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Invalid verification token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not token.is_valid():
            return Response(
                {'success': False, 'message': 'Token expired. Request a new one.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token.used = True
        token.save(update_fields=['used'])
        token.user.is_email_verified = True
        token.user.save(update_fields=['is_email_verified'])
        return Response({'success': True, 'message': 'Email verified successfully.'})


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't leak whether the email exists
            return Response({'success': True, 'message': 'If that email exists, a reset link was sent.'})

        reset_token = PasswordResetToken.objects.create(user=user, token=secrets.token_urlsafe(32))
        send_email_notification(
            to_email=user.email,
            subject='Reset your AIHMS password',
            message=f'Use this token to reset your password: {reset_token.token} (valid 1 hour).',
        )
        return Response({'success': True, 'message': 'If that email exists, a reset link was sent.'})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_str = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            token = PasswordResetToken.objects.get(token=token_str)
        except PasswordResetToken.DoesNotExist:
            return Response({'success': False, 'message': 'Invalid token.'}, status=400)

        if not token.is_valid():
            return Response({'success': False, 'message': 'Token expired.'}, status=400)

        user = token.user
        user.set_password(new_password)
        user.save(update_fields=['password'])
        token.used = True
        token.save(update_fields=['used'])
        return Response({'success': True, 'message': 'Password reset successfully.'})


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'success': False, 'message': 'Old password is incorrect.'}, status=400)

        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response({'success': True, 'message': 'Password changed successfully.'})


class MeView(generics.RetrieveUpdateAPIView):
    """Current user profile. Account deletion requires an administrative retention review."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
