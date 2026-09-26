from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from books.factories import create_admin, create_user
from users.permissions import IsAdminGroup

User = get_user_model()


# ---------- Auth ----------

class RegistrationTest(APITestCase):

    def test_register_success(self):
        url = reverse('users:register')
        response = self.client.post(url, {
            'email': 'new@test.com',
            'password': 'strongpass123',
            'phone_number': '+79990000000',
            'city': 'Москва',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='new@test.com').exists())

    def test_register_duplicate_email(self):
        User.objects.create_user(email='dup@test.com', password='pass12345')
        url = reverse('users:register')
        response = self.client.post(url, {
            'email': 'dup@test.com',
            'password': 'pass12345',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='login@test.com', password='pass12345')

    def test_login_success(self):
        url = reverse('users:login')
        response = self.client.post(url, {
            'email': 'login@test.com',
            'password': 'pass12345',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        url = reverse('users:login')
        response = self.client.post(url, {
            'email': 'login@test.com',
            'password': 'wrong',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------- User viewset ----------

class CustomUserViewSetTest(APITestCase):

    def setUp(self):
        self.user = create_user(email='u1@test.com')
        self.other = create_user(email='u2@test.com')
        self.admin = create_admin()
        self.url = reverse('users:users-list')

    def _count(self, data):
        if isinstance(data, dict) and 'count' in data:
            return data['count']
        return len(data)

    def test_list_requires_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_sees_only_self(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._count(response.data), 1)

    def test_admin_sees_all(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(self._count(response.data), 3)

    def test_update_own_profile(self):
        self.client.force_authenticate(self.user)
        url = reverse('users:users-detail', args=[self.user.id])
        response = self.client.patch(url, {'city': 'СПб'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.city, 'СПб')

    def test_update_other_profile_forbidden(self):
        self.client.force_authenticate(self.user)
        url = reverse('users:users-detail', args=[self.other.id])
        response = self.client.patch(url, {'city': 'СПб'})
        self.assertIn(response.status_code, (
            status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND,
        ))


# ---------- Permissions ----------

class IsAdminGroupTest(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsAdminGroup()

    def _request_for(self, user):
        request = self.factory.get('/')
        request.user = user
        return request

    def test_superuser_allowed(self):
        user = create_user(email='su@test.com')
        user.is_superuser = True
        user.save()
        self.assertTrue(self.permission.has_permission(self._request_for(user), None))

    def test_group_member_allowed(self):
        admin = create_admin()
        self.assertTrue(self.permission.has_permission(self._request_for(admin), None))

    def test_regular_user_denied(self):
        user = create_user(email='regular@test.com')
        self.assertFalse(self.permission.has_permission(self._request_for(user), None))
