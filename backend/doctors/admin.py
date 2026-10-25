from django.contrib import admin
from django.apps import apps

class ClinicalReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

for model in apps.get_app_config('doctors').get_models():
    admin.site.register(model, ClinicalReadOnlyAdmin if model.__name__ in {'ClinicalNote'} else admin.ModelAdmin)
