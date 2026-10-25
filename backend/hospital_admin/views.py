from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from core.permissions import IsHospitalAdmin
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db import transaction
from doctors.models import Doctor
from doctors.serializers import DoctorSerializer
from patients.models import Patient
from patients.serializers import PatientSerializer
from appointments.models import Appointment
from pharmacy.models import MedicineOrder
from .models import Hospital, Department, Staff
from .serializers import HospitalSerializer, DepartmentSerializer, StaffSerializer


class MyHospitalView(generics.RetrieveUpdateAPIView):
    serializer_class = HospitalSerializer
    permission_classes = [IsHospitalAdmin]

    def get_object(self):
        hospital, _ = Hospital.objects.get_or_create(
            admin=self.request.user,
            defaults={
                'name': f"{self.request.user.get_full_name()}'s Hospital",
                'address': '', 'city': '', 'state': '', 'pincode': '',
                'contact_phone': self.request.user.phone_number, 'contact_email': self.request.user.email,
            },
        )
        return hospital


class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [IsHospitalAdmin]

    def get_queryset(self):
        return Department.objects.filter(hospital__admin=self.request.user)

    def perform_create(self, serializer):
        hospital, _ = Hospital.objects.get_or_create(admin=self.request.user)
        serializer.save(hospital=hospital)


class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = StaffSerializer
    permission_classes = [IsHospitalAdmin]
    filterset_fields = ['role', 'is_active', 'department']
    search_fields = ['full_name']

    def get_queryset(self):
        return Staff.objects.filter(hospital__admin=self.request.user)

    def perform_create(self, serializer):
        hospital, _ = Hospital.objects.get_or_create(admin=self.request.user)
        serializer.save(hospital=hospital)


class ManagedDoctorsView(generics.ListAPIView):
    """List/manage doctors belonging to this hospital admin's hospital."""
    serializer_class = DoctorSerializer
    permission_classes = [IsHospitalAdmin]
    filterset_fields = ['specialization', 'department', 'is_verified']
    search_fields = ['user__first_name', 'user__last_name', 'specialization']

    def get_queryset(self):
        return Doctor.objects.filter(hospital__admin=self.request.user)


class UpdateDoctorStatusView(APIView):
    """Verify/unverify or assign a doctor to this hospital + a department."""
    permission_classes = [IsHospitalAdmin]

    def patch(self, request, pk):
        class StatusInput(serializers.Serializer):
            is_verified = serializers.BooleanField(required=False)
            department_id = serializers.UUIDField(required=False, allow_null=True)
            assign_to_hospital = serializers.BooleanField(required=False)
            consultation_fee = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0, required=False)
        input_data = StatusInput(data=request.data)
        input_data.is_valid(raise_exception=True)
        data = input_data.validated_data
        with transaction.atomic():
            doctor = get_object_or_404(Doctor.objects.select_for_update().filter(Q(hospital__admin=request.user) | Q(hospital__isnull=True)), pk=pk)
            hospital, _ = Hospital.objects.get_or_create(admin=request.user)
            if 'department_id' in data:
                doctor.department = get_object_or_404(Department, pk=data['department_id'], hospital=hospital) if data['department_id'] else None
            if data.get('assign_to_hospital'):
                doctor.hospital = hospital
            if 'is_verified' in data:
                doctor.is_verified = data['is_verified']
            if 'consultation_fee' in data:
                doctor.consultation_fee = data['consultation_fee']
            doctor.save()
        return Response({'success': True, 'data': DoctorSerializer(doctor).data})


class AllDoctorsForAssignmentView(generics.ListAPIView):
    """All doctors on the platform (regardless of hospital) — used when a
    hospital admin wants to browse and assign/verify a doctor."""
    serializer_class = DoctorSerializer

    def get_queryset(self):
        return Doctor.objects.filter(Q(hospital__admin=self.request.user) | Q(hospital__isnull=True)).select_related('user', 'hospital')

    permission_classes = [IsHospitalAdmin]
    search_fields = ['user__first_name', 'user__last_name', 'specialization']


class ManagedPatientsView(generics.ListAPIView):
    """Patients who've had at least one appointment at this hospital."""
    serializer_class = PatientSerializer
    permission_classes = [IsHospitalAdmin]
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

    def get_queryset(self):
        return Patient.objects.filter(
            appointments__hospital__admin=self.request.user
        ).distinct()


class AppointmentAnalyticsView(APIView):
    """Appointment volume, status breakdown, last-30-days trend."""
    permission_classes = [IsHospitalAdmin]

    def get(self, request):
        qs = Appointment.objects.filter(hospital__admin=request.user)
        since = timezone.now().date() - timedelta(days=30)

        status_breakdown = qs.values('status').annotate(count=Count('id'))
        daily_trend = (
            qs.filter(scheduled_date__gte=since)
            .values('scheduled_date')
            .annotate(count=Count('id'))
            .order_by('scheduled_date')
        )
        top_doctors = (
            qs.values('doctor__user__first_name', 'doctor__user__last_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        return Response({
            'success': True,
            'total_appointments': qs.count(),
            'status_breakdown': list(status_breakdown),
            'daily_trend_last_30_days': list(daily_trend),
            'top_doctors': list(top_doctors),
        })


class RevenueDashboardView(APIView):
    """Demo revenue view — consultation fees + pharmacy order totals. Payment gateway is mocked."""
    permission_classes = [IsHospitalAdmin]

    def get(self, request):
        completed_appointments = Appointment.objects.filter(
            hospital__admin=request.user, status='COMPLETED'
        )
        consult_revenue = sum(
            float(a.doctor.consultation_fee) for a in completed_appointments.select_related('doctor')
        )
        pharmacy_revenue = MedicineOrder.objects.filter(
            patient__in=Patient.objects.filter(appointments__hospital__admin=request.user),
            status='DELIVERED',
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        return Response({
            'success': True,
            'consultation_revenue': consult_revenue,
            'pharmacy_revenue': float(pharmacy_revenue),
            'total_revenue': consult_revenue + float(pharmacy_revenue),
            'note': 'Demo figures — real payment gateway integration is out of scope for this build.',
        })


class HospitalStatisticsView(APIView):
    permission_classes = [IsHospitalAdmin]

    def get(self, request):
        hospital, _ = Hospital.objects.get_or_create(admin=request.user)
        return Response({
            'success': True,
            'total_doctors': Doctor.objects.filter(hospital=hospital).count(),
            'total_departments': Department.objects.filter(hospital=hospital).count(),
            'total_staff': Staff.objects.filter(hospital=hospital, is_active=True).count(),
            'total_patients_served': Patient.objects.filter(appointments__hospital=hospital).distinct().count(),
            'appointments_today': Appointment.objects.filter(
                hospital=hospital, scheduled_date=timezone.now().date()
            ).count(),
        })
