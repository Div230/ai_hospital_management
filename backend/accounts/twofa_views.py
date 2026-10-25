"""
Optional TOTP-based Two-Factor Authentication.
Flow:
  1. POST /2fa/setup/        -> generates a secret + otpauth:// URI (frontend renders as QR)
  2. POST /2fa/enable/       -> verifies a code from the authenticator app, flips is_2fa_enabled on
  3. Login (accounts/views.py LoginView) still returns tokens normally for users without 2FA.
     For users WITH 2FA enabled, login instead returns {"requires_2fa": true, "user_id": ...}
     and the frontend must call /2fa/login-verify/ with a TOTP code to receive the actual JWT pair.
  4. POST /2fa/disable/      -> turns 2FA back off (requires current password)
"""
import pyotp
from django.core import signing
from django.core.cache import cache
from .views import LoginThrottle
from .session_views import RefreshCookieMixin, check_origin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import CustomTokenObtainPairSerializer, UserSerializer


class TwoFactorSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_2fa_enabled:
            return Response({'message': 'Disable existing 2FA before replacing its secret.'}, status=409)
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.save(update_fields=['totp_secret'])

        totp = pyotp.TOTP(secret)
        otpauth_uri = totp.provisioning_uri(name=user.email, issuer_name='AI Hospital Management System')

        return Response({
            'success': True,
            'secret': secret,
            'otpauth_uri': otpauth_uri,
            'message': 'Scan the otpauth_uri as a QR code in Google Authenticator / Authy, then confirm with /2fa/enable/.',
        })


class TwoFactorEnableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        code = request.data.get('code', '')
        if not user.totp_secret:
            return Response({'success': False, 'message': 'Call /2fa/setup/ first.'}, status=400)

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            return Response({'success': False, 'message': 'Invalid code.'}, status=400)

        user.is_2fa_enabled = True
        user.save(update_fields=['is_2fa_enabled'])
        return Response({'success': True, 'message': '2FA enabled successfully.'})


class TwoFactorDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        password = request.data.get('password', '')
        if not user.check_password(password):
            return Response({'success': False, 'message': 'Incorrect password.'}, status=400)

        user.is_2fa_enabled = False
        user.totp_secret = ''
        user.save(update_fields=['is_2fa_enabled', 'totp_secret'])
        return Response({'success': True, 'message': '2FA disabled.'})


class TwoFactorLoginVerifyView(RefreshCookieMixin, APIView):
    """Second step of login for users with 2FA enabled."""
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        check_origin(request)
        try:
            challenge = signing.loads(request.data.get('challenge', ''), salt='2fa-login', max_age=300)
            user_id = challenge['user']
            nonce = challenge['nonce']
            if cache.get('2fa:' + nonce) != user_id:
                raise signing.BadSignature('Consumed challenge')
        except (signing.BadSignature, KeyError, TypeError):
            return Response({'message': 'Restart login to obtain a valid challenge.'}, status=400)
        code = request.data.get('code', '')

        try:
            user = User.objects.get(id=user_id, is_2fa_enabled=True, is_active=True)
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'Invalid request.'}, status=400)

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            return Response({'success': False, 'message': 'Invalid or expired code.'}, status=400)

        if not cache.delete('2fa:' + nonce):
            return Response({'message': 'Challenge already used.'}, status=400)
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        return Response({
            'success': True,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
        })
