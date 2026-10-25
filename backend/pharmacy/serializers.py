from rest_framework import serializers
from .models import Pharmacy, Medicine, MedicineOrder, MedicineOrderItem


class PharmacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pharmacy
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'user', 'is_verified', 'created_at']


class MedicineSerializer(serializers.ModelSerializer):
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Price cannot be negative.')
        return value

    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Medicine
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'pharmacy', 'created_at']


class MedicineOrderItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    class Meta:
        model = MedicineOrderItem
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'order', 'price_at_order', 'created_at']


class MedicineOrderSerializer(serializers.ModelSerializer):
    items = MedicineOrderItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)

    class Meta:
        model = MedicineOrder
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'patient', 'total_amount', 'is_paid', 'pharmacy', 'prescription', 'items', 'payment_reference', 'created_at']
