from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from core.file_views import PrivateDocumentView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Swagger / OpenAPI documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Auth
    path('api/auth/', include('accounts.urls')),

    # Role modules
    path('api/patients/', include('patients.urls')),
    path('api/doctors/', include('doctors.urls')),
    path('api/hospital-admin/', include('hospital_admin.urls')),
    path('api/laboratory/', include('laboratory.urls')),
    path('api/pharmacy/', include('pharmacy.urls')),

    # Cross-cutting
    path('api/appointments/', include('appointments.urls')),
    path('api/ai/', include('ai_assistant.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/core/', include('core.urls')),
    path('api/prescription-reader/', include('prescription_reader.urls')),
    path('api/documents/<str:kind>/<uuid:pk>/', PrivateDocumentView.as_view(), name='private-document'),
]
