from django.contrib import admin
from django.apps import apps

class ClinicalReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

for model in apps.get_app_config('appointments').get_models():
    admin.site.register(model, ClinicalReadOnlyAdmin if model.__name__ in {'PrescriptionItem', 'Prescription'} else admin.ModelAdmin)
