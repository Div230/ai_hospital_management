from django.core import signing
from django.http import FileResponse, Http404
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from accounts.models import User


class PrivateDocumentView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, kind, pk):
        try:
            token = signing.loads(request.query_params.get('t', ''), salt='private-file', max_age=60)
            if token['kind'] != kind or token['id'] != str(pk):
                raise Http404
            user = User.objects.get(pk=token['user'], is_active=True)
        except (signing.BadSignature, User.DoesNotExist, KeyError, ValueError):
            raise Http404
        if kind == 'medical':
            from patients.models import MedicalReport
            qs = MedicalReport.objects.filter(pk=pk)
            if user.role == 'patient':
                qs = qs.filter(patient__user=user)
            elif user.role == 'doctor':
                qs = qs.filter(patient__appointments__doctor__user=user, patient__appointments__status__in=['CONFIRMED', 'COMPLETED'])
            else:
                raise Http404
        elif kind == 'lab':
            from laboratory.models import LabReport
            qs = LabReport.objects.filter(pk=pk)
            if user.role == 'patient':
                qs = qs.filter(test_request__patient__user=user)
            elif user.role == 'laboratory':
                qs = qs.filter(test_request__laboratory__user=user)
            elif user.role == 'doctor':
                qs = qs.filter(test_request__ordered_by_doctor__user=user)
            else:
                raise Http404
        elif kind == 'prescription-upload':
            from prescription_reader.models import PrescriptionUpload
            qs = PrescriptionUpload.objects.filter(pk=pk)
            if user.role == 'patient':
                qs = qs.filter(patient__user=user)
            elif user.role == 'doctor':
                qs = qs.filter(review_requested_at__isnull=False, patient__appointments__doctor__user=user, patient__appointments__status__in=['CONFIRMED', 'COMPLETED'])
            else:
                raise Http404
        else:
            raise Http404
        obj = qs.first()
        if not obj or not obj.file:
            raise Http404
        try:
            response = FileResponse(obj.file.open('rb'), as_attachment=False, filename='document' + Path(obj.file.name).suffix)
        except FileNotFoundError:
            raise Http404
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Content-Security-Policy'] = "sandbox; default-src 'none'"
        return response
