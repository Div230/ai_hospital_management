"""Short-lived in-memory access tokens; rotating HttpOnly refresh cookies."""
import secrets
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

COOKIE = 'aihms_refresh'
CSRF_COOKIE = 'aihms_csrf'


def check_origin(request):
    origin = request.headers.get('Origin')
    if origin and origin not in settings.CORS_ALLOWED_ORIGINS:
        raise PermissionDenied('Untrusted request origin.')


def check_refresh_csrf(request):
    check_origin(request)
    cookie, header = request.COOKIES.get(CSRF_COOKIE, ''), request.headers.get('X-CSRFToken', '')
    if not cookie or not secrets.compare_digest(cookie, header):
        raise PermissionDenied('Refresh request requires a valid CSRF token.')


def attach_refresh(response, refresh):
    response.set_cookie(COOKIE, refresh, max_age=7 * 86400, httponly=True,
                        secure=not settings.DEBUG, samesite='Lax', path='/api/auth/')
    response.set_cookie(CSRF_COOKIE, secrets.token_urlsafe(32), max_age=7 * 86400,
                        httponly=False, secure=not settings.DEBUG, samesite='Lax', path='/')
    response['Cache-Control'] = 'no-store'
    return response


class RefreshCookieMixin:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if isinstance(getattr(response, 'data', None), dict):
            refresh = response.data.pop('refresh', None)
            if refresh:
                attach_refresh(response, refresh)
        return response


class RefreshCookieView(RefreshCookieMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_authenticate_header(self, request):
        return 'Bearer'

    def post(self, request):
        check_refresh_csrf(request)
        serializer = TokenRefreshSerializer(data={'refresh': request.COOKIES.get(COOKIE, '')})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            # Match SimpleJWT's token views: expired/blacklisted/malformed
            # credentials are authentication failures, not server errors.
            raise InvalidToken('The session has expired. Please log in again.') from exc
        return Response(serializer.validated_data)


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        check_refresh_csrf(request)
        refresh = request.COOKIES.get(COOKIE)
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass
        response = Response({'success': True})
        response.delete_cookie(COOKIE, path='/api/auth/')
        response.delete_cookie(CSRF_COOKIE, path='/')
        return response
