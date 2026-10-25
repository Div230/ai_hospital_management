import logging
from .models import AuditLog

logger = logging.getLogger('healthcare')

# Only log state-changing requests to keep the audit table meaningful
AUDIT_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
SKIP_PATHS = ('/api/auth/token/', '/api/docs/', '/admin/')


class AuditLogMiddleware:
    """
    Records who hit which endpoint with which method, for compliance-style
    traceability. Kept intentionally lightweight for a demo build.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            if (
                request.method in AUDIT_METHODS
                and not request.path.startswith(SKIP_PATHS)
                and getattr(request, 'user', None)
                and request.user.is_authenticated
            ):
                AuditLog.objects.create(
                    user=request.user,
                    action='CREATE' if request.method == 'POST' else
                           'UPDATE' if request.method in ('PUT', 'PATCH') else 'DELETE',
                    path=request.path,
                    method=request.method,
                    ip_address=self._get_client_ip(request),
                    extra={'status_code': response.status_code},
                )
        except Exception as e:
            # Audit logging must never break the actual request
            logger.warning(f'Audit log failed: {e}')

        return response

    @staticmethod
    def _get_client_ip(request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
