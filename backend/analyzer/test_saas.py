import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AnalysisRecord, Product, ProductFavorite, SearchEvent


User = get_user_model()


class SaaSEndpointsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def _auth_client(self, user):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        return access_token

    def test_support_endpoint_public(self):
        response = self.client.get(reverse("support"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("message", payload)
        self.assertIn("links", payload)

    def test_favorites_toggle_and_list(self):
        user = User.objects.create_user(username="fav@example.com", email="fav@example.com", password="TestPassword123!")
        access_token = self._auth_client(user)

        product = Product.objects.create(
            barcode="8900000000000",
            name="Test Product",
            brand="TestBrand",
            ingredients_text="water, sugar, salt, refined wheat flour",
            categories="Instant Food",
            country="India",
            is_indian=True,
        )

        # Add favorite
        response = self.client.post(
            reverse("favorites"),
            data=json.dumps({"product_barcode": product.barcode}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["status"], "added")

        # List favorites
        response = self.client.get(reverse("favorites"), HTTP_AUTHORIZATION=f"Bearer {access_token}")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["items"]), 1)

        # Toggle remove
        response = self.client.post(
            reverse("favorites"),
            data=json.dumps({"product_barcode": product.barcode}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "removed")

        response = self.client.get(reverse("favorites"), HTTP_AUTHORIZATION=f"Bearer {access_token}")
        payload = response.json()
        self.assertEqual(len(payload["items"]), 0)

    def test_search_event_and_analysis_history_recording(self):
        # Ensure SearchEvent is created by searches (anonymous supported).
        before_search_events = SearchEvent.objects.count()
        response = self.client.get(reverse("search_product"), {"q": "Maggi"})
        self.assertEqual(response.status_code, 200)
        self.assertGreater(SearchEvent.objects.count(), before_search_events)

        # Ensure AnalysisRecord is created by authenticated analysis.
        user = User.objects.create_user(username="hist@example.com", email="hist@example.com", password="TestPassword123!")
        access_token = self._auth_client(user)

        before_analysis = AnalysisRecord.objects.count()
        response = self.client.post(
            reverse("analyze_text"),
            data=json.dumps({"text": "water, sugar, salt, refined wheat flour", "user_goal": "Regular", "food_type": "Solid"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(AnalysisRecord.objects.count(), before_analysis)

        response = self.client.get(reverse("analysis_history"), HTTP_AUTHORIZATION=f"Bearer {access_token}")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertGreaterEqual(len(payload["items"]), 1)

