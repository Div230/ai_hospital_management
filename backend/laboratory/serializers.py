from rest_framework import serializers
from patients.models import Patient
from core.documents import validate_upload, DocumentError
from core.file_access import document_url
from .models import Laboratory, LabTestRequest, LabReport


class LaboratorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratory
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'user', 'is_verified', 'created_at']


class LabTestRequestSerializer(serializers.ModelSerializer):
    patient_id = serializers.PrimaryKeyRelatedField(source='patient', queryset=Patient.objects.all(), write_only=True, required=False)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    report = serializers.SerializerMethodField()

    class Meta:
        model = LabTestRequest
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'patient', 'ordered_by_doctor', 'status', 'created_at']

    def validate(self, attrs):
        request = self.context['request']
        if request.user.role == 'patient':
            attrs.pop('patient', None)
        elif request.user.role == 'doctor':
            patient = attrs.get('patient')
            if not patient or not patient.appointments.filter(doctor__user=request.user, status__in=['CONFIRMED', 'COMPLETED']).exists():
                raise serializers.ValidationError('Select a patient within your clinical workflow.')
        else:
            raise serializers.ValidationError('Only patients and treating doctors can request tests.')
        return attrs

    def get_report(self, obj):
        report = getattr(obj, 'report', None)
        if not report:
            return None
        return {
            'result_summary': report.result_summary,
            'ai_abnormal_findings': report.ai_abnormal_findings,
            'file_url': document_url(self.context.get('request'), 'lab', report.pk) if report.file else None,
        }


class LabReportSerializer(serializers.ModelSerializer):
    def validate_file(self, value):
        try:
            validate_upload(value)
        except DocumentError as exc:
            raise serializers.ValidationError(str(exc))
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['file'] = document_url(self.context.get('request'), 'lab', instance.pk)
        return data

    class Meta:
        model = LabReport
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at',
            'id', 'test_request', 'ai_abnormal_findings', 'structured_results',
            'is_notified', 'created_at',
        ]
