from rest_framework import serializers
from .models import Hospital, Department, Staff


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'admin', 'created_at']


class DepartmentSerializer(serializers.ModelSerializer):
    doctor_count = serializers.IntegerField(source='doctors.count', read_only=True)

    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'hospital', 'created_at']


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'hospital', 'created_at']
