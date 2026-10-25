from rest_framework import serializers
from core.documents import validate_upload, DocumentError
from core.file_access import document_url
from .models import (
    Patient, FamilyMember, MedicalHistory, MedicalReport,
    MedicineReminder, VaccinationReminder, SOSAlert, AmbulanceRequest,
)


class PatientSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'user', 'ai_health_score', 'ai_risk_flags', 'created_at']


class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'patient', 'created_at']


class MedicalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalHistory
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'patient', 'recorded_by', 'created_at']


class MedicalReportSerializer(serializers.ModelSerializer):
    def validate_file(self, value):
        try:
            validate_upload(value)
        except DocumentError as exc:
            raise serializers.ValidationError(str(exc))
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['file'] = document_url(self.context.get('request'), 'medical', instance.pk)
        return data

    class Meta:
        model = MedicalReport
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at',
            'id', 'patient', 'uploaded_by', 'status',
            'ocr_extracted_text', 'ai_structured_summary', 'ai_abnormal_values', 'created_at',
        ]


class MedicineReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineReminder
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'patient', 'created_at']


class VaccinationReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = VaccinationReminder
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'patient', 'created_at']


class SOSAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SOSAlert
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'patient', 'status', 'created_at']


class AmbulanceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmbulanceRequest
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'sos_alert', 'created_at']
