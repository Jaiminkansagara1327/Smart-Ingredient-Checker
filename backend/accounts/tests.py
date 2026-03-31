import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class AuthSaaSFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse("register")
        self.token_url = reverse("token_obtain_pair")
        self.me_url = reverse("me")

        self.email = "tester@example.com"
        self.password = "TestPassword123!"
        self.name = "Test User"

    def test_register_login_and_me(self):
        # Register
        response = self.client.post(
            self.register_url,
            data=json.dumps({"email": self.email, "password": self.password, "name": self.name}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["user"]["email"], self.email)

        # Login (JWT obtain) using email
        response = self.client.post(
            self.token_url,
            data=json.dumps({"email": self.email, "password": self.password}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        tokens = response.json()
        self.assertIn("access", tokens)

        # Get current user
        access_token = tokens["access"]
        response = self.client.get(
            self.me_url,
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["user"]["email"], self.email)

    def test_me_requires_auth(self):
        response = self.client.get(self.me_url)
        # DRF/JWT typically returns 401 when unauthenticated
        self.assertIn(response.status_code, (401, 403))

    def test_refresh_token_access_token_still_works(self):
        # Create a user directly to avoid depending on password validators behavior.
        user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
            first_name=self.name,
        )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = self.client.get(
            self.me_url,
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["user"]["email"], self.email)

