from django.test import TestCase
from rest_framework.test import APIClient
from .models import User


class AccountSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_staff_self_registration_rejected(self):
        for role in ('doctor', 'hospital_admin', 'laboratory', 'pharmacy'):
            response = self.client.post('/api/auth/register/', {'username': 'test_' + role, 'email': role + '@synthetic.example.test',
                'password': 'Test-only-Aihms-346!', 'password_confirm': 'Test-only-Aihms-346!',
                'first_name': 'Synthetic', 'last_name': 'Test', 'role': role})
            self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_login_refresh_cookie_csrf_and_profile_privilege_separation(self):
        user = User.objects.create_user(username='test', email='test@synthetic.example.test', password='Test-only-Aihms-346!', role='patient')
        response = self.client.post('/api/auth/token/', {'email': user.email, 'password': 'Test-only-Aihms-346!'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('refresh', response.data)
        self.assertTrue(response.cookies['aihms_refresh']['httponly'])
        self.assertEqual(self.client.post('/api/auth/token/refresh/').status_code, 403)
        csrf = response.cookies['aihms_csrf'].value
        self.assertEqual(self.client.post('/api/auth/token/refresh/', HTTP_X_CSRFTOKEN=csrf).status_code, 200)
        self.client.force_authenticate(user)
        response = self.client.patch('/api/auth/me/', {'role': 'hospital_admin', 'is_2fa_enabled': True, 'is_phone_verified': True})
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.role, 'patient')
        self.assertFalse(user.is_2fa_enabled)
        self.assertFalse(user.is_phone_verified)

    def test_two_factor_step_cannot_skip_password(self):
        response = self.client.post('/api/auth/2fa/login-verify/', {'user_id': '00000000-0000-0000-0000-000000000000', 'code': '123456'})
        self.assertEqual(response.status_code, 400)

    def test_patient_registration_and_login(self):
        payload = {'username': 'synthetic_registration', 'email': 'registration@synthetic.example.test',
                   'password': 'Test-only-Aihms-346!', 'password_confirm': 'Test-only-Aihms-346!',
                   'first_name': 'Synthetic', 'last_name': 'Patient', 'role': 'patient'}
        response = self.client.post('/api/auth/register/', payload)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(User.objects.get(email=payload['email']).role, 'patient')
        login = self.client.post('/api/auth/token/', {'email': payload['email'], 'password': payload['password']})
        self.assertEqual(login.status_code, 200, login.data)
        self.assertIn('access', login.data)

    def test_invalid_refresh_is_unauthorized_not_server_error(self):
        from .session_views import COOKIE, CSRF_COOKIE
        self.client.cookies[COOKIE] = 'synthetic-invalid-token'
        self.client.cookies[CSRF_COOKIE] = 'synthetic-csrf'
        response = self.client.post('/api/auth/token/refresh/', HTTP_X_CSRFTOKEN='synthetic-csrf')
        self.assertEqual(response.status_code, 401, response.data)

    def test_blacklisted_refresh_is_unauthorized(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        from .session_views import COOKIE, CSRF_COOKIE
        user = User.objects.create_user(username='revoked', email='revoked@synthetic.example.test', role='patient')
        token = RefreshToken.for_user(user)
        token.blacklist()
        self.client.cookies[COOKIE] = str(token)
        self.client.cookies[CSRF_COOKIE] = 'synthetic-csrf'
        response = self.client.post('/api/auth/token/refresh/', HTTP_X_CSRFTOKEN='synthetic-csrf')
        self.assertEqual(response.status_code, 401, response.data)
