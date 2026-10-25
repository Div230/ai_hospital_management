"""Private file capabilities are issued only inside authorized API responses."""
from urllib.parse import urlencode
from django.core import signing
from django.urls import reverse


def document_url(request, kind, object_id):
    if not request or not request.user.is_authenticated:
        return None
    token = signing.dumps({'user': str(request.user.pk), 'kind': kind, 'id': str(object_id)}, salt='private-file')
    return reverse('private-document', kwargs={'kind': kind, 'pk': object_id}) + '?' + urlencode({'t': token})
