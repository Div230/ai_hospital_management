import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('healthcare')


def custom_exception_handler(exc, context):
    """
    Uniform error envelope for every API error:
    { "success": false, "error": { "code": ..., "message": ..., "details": ... } }
    """
    response = exception_handler(exc, context)

    if response is not None:
        request = context.get('request')
        logger.warning('API request rejected: %s', response.status_code)
        error_payload = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': _extract_message(response.data),
                'details': response.data,
            }
        }
        response.data = error_payload
        return response

    # Unhandled exception -> log full trace, return generic 500
    logger.error('Unhandled API exception: %s', type(exc).__name__)
    return Response(
        {
            'success': False,
            'error': {
                'code': 500,
                'message': 'Internal server error. Please try again later.',
                'details': str(exc) if context.get('request') and context['request'].META.get('DEBUG') else None,
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _extract_message(data):
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        first_key = next(iter(data), None)
        if first_key:
            val = data[first_key]
            if isinstance(val, list) and val:
                return f'{first_key}: {val[0]}'
            return f'{first_key}: {val}'
    if isinstance(data, list) and data:
        return str(data[0])
    return 'Request failed.'
