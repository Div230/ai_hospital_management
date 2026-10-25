from rest_framework import serializers
from .models import Doctor, DoctorAvailability, ClinicalNote


class DoctorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)

    class Meta:
        model = Doctor
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'user', 'is_verified', 'rating', 'hospital', 'department', 'created_at']


class DoctorPublicSerializer(serializers.ModelSerializer):
    """Slim serializer used when patients browse doctors for booking."""
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id', 'full_name', 'specialization', 'qualification',
            'years_of_experience', 'consultation_fee', 'bio',
            'is_available_for_video', 'rating', 'hospital_name',
        ]


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        start = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end = attrs.get('end_time', getattr(self.instance, 'end_time', None))
        duration = attrs.get('slot_duration_minutes', getattr(self.instance, 'slot_duration_minutes', 15))
        if not start or not end or start >= end or not 1 <= duration <= 120:
            raise serializers.ValidationError('Use an increasing interval and a 1–120 minute duration.')
        return attrs

    class Meta:
        model = DoctorAvailability
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'doctor', 'created_at']


class ClinicalNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalNote
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'doctor', 'created_at']
