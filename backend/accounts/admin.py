from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import User, EmailVerificationToken, PasswordResetToken, OTPVerification


class AccountCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'username', 'role', 'first_name', 'last_name')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = AccountCreationForm
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'username', 'role', 'first_name', 'last_name', 'password1', 'password2')}),)
    list_display = ('email', 'username', 'role', 'is_email_verified', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'is_email_verified')
    search_fields = ('email', 'username', 'phone_number')
    ordering = ('-created_at',)
    fieldsets = UserAdmin.fieldsets + (
        ('Healthcare Role', {'fields': ('role', 'phone_number', 'is_email_verified',
                                          'is_phone_verified', 'is_2fa_enabled',
                                          'profile_picture', 'whatsapp_opt_in')}),
    )


# Verification/reset/TOTP secrets are intentionally not exposed through the admin UI.
