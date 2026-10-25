from rest_framework import serializers
from core.documents import validate_upload, DocumentError
from core.file_access import document_url
from .models import PrescriptionUpload, PersonalCorrection, ClinicianReview


class UploadInputSerializer(serializers.Serializer):
    file = serializers.FileField()
    recognition_mode = serializers.ChoiceField(choices=['printed', 'handwritten'], default='printed')
    external_consent = serializers.BooleanField(default=False)

    def validate_file(self, value):
        try:
            validate_upload(value)
        except DocumentError as exc:
            raise serializers.ValidationError(str(exc))
        return value


class CorrectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalCorrection
        fields = ['id', 'text', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {'text': {'max_length': 40000}}


class ReviewSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)

    class Meta:
        model = ClinicianReview
        fields = ['id', 'doctor_name', 'notes', 'created_at']
        read_only_fields = ['id', 'doctor_name', 'created_at']
        extra_kwargs = {'notes': {'max_length': 10000}}


class UploadSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    personal_correction = serializers.SerializerMethodField()
    reviews = ReviewSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)

    class Meta:
        model = PrescriptionUpload
        fields = ['id', 'patient_name', 'original_filename', 'mime_type', 'size_bytes', 'recognition_mode',
                  'status', 'result', 'error_code', 'error_message', 'attempt_count', 'file_url',
                  'personal_correction', 'reviews', 'review_requested_at', 'created_at', 'updated_at']
        read_only_fields = fields

    def get_file_url(self, obj):
        request = self.context.get('request')
        # Doctors receive a view-specific original endpoint after workflow authorization.
        return document_url(request, 'prescription-upload', obj.pk)

    def get_personal_correction(self, obj):
        correction = obj.corrections.first()
        return CorrectionSerializer(correction).data if correction else None
