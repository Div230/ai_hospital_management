import logging
from rest_framework import generics, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from appointments.serializers import PrescriptionSerializer

from core.permissions import IsPharmacy, IsPatient
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from notifications.services import notify_user, dispatch_webhook_event
from .models import Pharmacy, Medicine, MedicineOrder, MedicineOrderItem
from .serializers import (
    PharmacySerializer, MedicineSerializer, MedicineOrderSerializer, MedicineOrderItemSerializer,
)

logger = logging.getLogger('healthcare')


class MyPharmacyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = PharmacySerializer
    permission_classes = [IsPharmacy]

    def get_object(self):
        profile, _ = Pharmacy.objects.get_or_create(
            user=self.request.user, defaults={'name': self.request.user.get_full_name() or 'Pharmacy'}
        )
        return profile


class MedicineViewSet(viewsets.ModelViewSet):
    """CRUD for a pharmacy's own inventory; read-only availability search for patients."""
    serializer_class = MedicineSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['pharmacy', 'requires_prescription']
    search_fields = ['name', 'generic_name']

    def get_queryset(self):
        if self.request.user.role == 'pharmacy':
            return Medicine.objects.filter(pharmacy__user=self.request.user)
        return Medicine.objects.filter(stock_quantity__gt=0)

    def get_permissions(self):
        return [permissions.IsAuthenticated()] if self.request.method in permissions.SAFE_METHODS else [IsPharmacy()]

    def perform_create(self, serializer):
        pharmacy, _ = Pharmacy.objects.get_or_create(user=self.request.user)
        serializer.save(pharmacy=pharmacy)


class ReceivePrescriptionView(APIView):
    """Pharmacy receives a doctor's digital prescription and converts it to an order."""
    permission_classes = [IsPharmacy]

    def post(self, request, prescription_id):
        # This schema has no patient-directed sharing target. Only already
        # assigned orders may be retrieved; no pharmacy may claim strangers' prescriptions.
        order = MedicineOrder.objects.filter(prescription_id=prescription_id, pharmacy__user=request.user).first()
        if not order:
            return Response({'message': 'Prescription is not assigned to your pharmacy. Direct sharing is unavailable.'}, status=404)
        return Response({'success': True, 'data': MedicineOrderSerializer(order).data})



class MedicineOrderViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'patch', 'head', 'options']
    serializer_class = MedicineOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'pharmacy':
            return MedicineOrder.objects.filter(pharmacy__user=user)
        if user.role == 'patient':
            return MedicineOrder.objects.filter(patient__user=user)
        return MedicineOrder.objects.none()

    def perform_update(self, serializer):
        from rest_framework.exceptions import ValidationError
        from decimal import Decimal
        if self.request.user.role != 'pharmacy':
            raise PermissionDenied('Only the assigned pharmacy can update an order.')
        transitions = {'PLACED': {'CONFIRMED', 'CANCELLED'}, 'CONFIRMED': {'PACKED', 'CANCELLED'},
                       'PACKED': {'OUT_FOR_DELIVERY', 'CANCELLED'}, 'OUT_FOR_DELIVERY': {'DELIVERED', 'CANCELLED'},
                       'DELIVERED': set(), 'CANCELLED': set()}
        with transaction.atomic():
            order = MedicineOrder.objects.select_for_update().get(pk=serializer.instance.pk)
            old_status = order.status
            new_status = serializer.validated_data.get('status', old_status)
            if new_status != old_status and new_status not in transitions[old_status]:
                raise ValidationError('This order status transition is not permitted.')
            items = list(order.items.order_by('medicine_id'))
            medicines = {m.pk: m for m in Medicine.objects.select_for_update().filter(pk__in=[i.medicine_id for i in items]).order_by('pk')}
            if new_status == 'CONFIRMED' and old_status == 'PLACED':
                for item in items:
                    medicine = medicines[item.medicine_id]
                    if medicine.stock_quantity < item.quantity:
                        raise ValidationError('Insufficient stock to confirm this order.')
                    medicine.stock_quantity -= item.quantity
                    medicine.save(update_fields=['stock_quantity'])
            elif new_status == 'CANCELLED' and old_status in ('CONFIRMED', 'PACKED', 'OUT_FOR_DELIVERY'):
                for item in items:
                    medicine = medicines[item.medicine_id]
                    medicine.stock_quantity += item.quantity
                    medicine.save(update_fields=['stock_quantity'])
            serializer.instance = order
            serializer.save()
            if new_status != old_status:
                transaction.on_commit(lambda: notify_user(order.patient.user, 'ORDER_UPDATE', 'Order Status Updated',
                    'A pharmacy order status changed. Check your portal for details.'))


class PendingPrescriptionsView(generics.ListAPIView):
    """Prescriptions not yet claimed by any pharmacy — pharmacy browses this to pick one up."""
    serializer_class = PrescriptionSerializer
    permission_classes = [IsPharmacy]

    def get_queryset(self):
        from appointments.models import Prescription
        return Prescription.objects.filter(is_sent_to_pharmacy=False, orders__pharmacy__user=self.request.user).distinct()
