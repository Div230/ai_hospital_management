from rest_framework.permissions import BasePermission


class IsRole(BasePermission):
    """Generic factory-style role check. Subclass per role below."""
    role = None

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == self.role
        )


class IsPatient(IsRole):
    role = 'patient'


class IsDoctor(IsRole):
    role = 'doctor'


class IsHospitalAdmin(IsRole):
    role = 'hospital_admin'


class IsLaboratory(IsRole):
    role = 'laboratory'


class IsPharmacy(IsRole):
    role = 'pharmacy'


class IsOwnerOrReadOnly(BasePermission):
    """Object-level check: only the owning user can modify their own record."""
    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, 'user', None) or getattr(obj, 'patient', None)
        return owner == request.user or request.user.role == 'hospital_admin'
