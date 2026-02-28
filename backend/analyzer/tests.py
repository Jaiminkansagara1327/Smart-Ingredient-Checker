"""
Ingrexa Backend — Automated Test Suite
======================================
Tests cover:
  1. Unit Tests  — pure service logic (no HTTP, no DB)
  2. API Tests   — full HTTP round-trips via Django test client
  3. Security Tests — input validation edge cases

Run with:
    python manage.py test analyzer
"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache
import json

from .openfoodfacts_service import (
    _is_known_indian_brand,
    _is_english_text,
    _is_quality_product,
)

# Disable throttling globally for all tests so rate limits don't interfere.
# In production the throttling is active; in tests we want clean, isolated results.
NO_THROTTLE = {
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
}


# =============================================================================
# 1. UNIT TESTS — Service Logic
#    Tests pure Python functions. No network calls, no DB.
# =============================================================================

class IndianBrandDetectionTest(TestCase):
    """Tests for the Indian brand prioritization logic."""

    def test_known_indian_brands_are_detected(self):
        """Famous Indian brands should always be recognized."""
        self.assertTrue(_is_known_indian_brand("haldiram"))
        self.assertTrue(_is_known_indian_brand("amul"))
        self.assertTrue(_is_known_indian_brand("parle"))
        self.assertTrue(_is_known_indian_brand("britannia"))
        self.assertTrue(_is_known_indian_brand("Mother Dairy"))

    def test_global_brands_are_not_detected_as_indian(self):
        """Foreign brands should not be mistaken for Indian ones."""
        self.assertFalse(_is_known_indian_brand("Nestle Global"))
        self.assertFalse(_is_known_indian_brand("Kelloggs"))
        self.assertFalse(_is_known_indian_brand("Heinz"))

    def test_case_insensitive_detection(self):
        """Detection must be case-insensitive: HALDIRAM == haldiram."""
        self.assertTrue(_is_known_indian_brand("HALDIRAM"))
        self.assertTrue(_is_known_indian_brand("Amul"))
        self.assertTrue(_is_known_indian_brand("PARLE"))

    def test_empty_brand_string(self):
        """An empty brand string must return False without crashing."""
        self.assertFalse(_is_known_indian_brand(""))

    def test_random_string_is_not_indian(self):
        """Random words must not be treated as Indian brands."""
        self.assertFalse(_is_known_indian_brand("xyzabc"))
        self.assertFalse(_is_known_indian_brand("RandomBrand123"))


class EnglishTextDetectionTest(TestCase):
    """Tests for the English language detection logic (used to filter OFF results)."""

    def test_plain_english_is_detected(self):
        """Standard ASCII ingredient text must be recognized as English."""
        self.assertTrue(_is_english_text("water, sugar, salt, refined wheat flour"))

    def test_non_latin_text_is_rejected(self):
        """Hindi (Devanagari) text must NOT pass as English."""
        self.assertFalse(_is_english_text("पानी, चीनी, नमक"))

    def test_empty_text(self):
        """Empty string edge case must be handled gracefully."""
        result = _is_english_text("")
        # Should return a bool without crashing
        self.assertIsInstance(result, bool)


class ProductQualityFilterTest(TestCase):
    """Tests for the junk/spam product filter used in OpenFoodFacts results."""

    def test_real_product_passes_filter(self):
        """A valid product entry should pass the quality check."""
        self.assertTrue(_is_quality_product("Oreo Chocolate Sandwich Cookies", "Nabisco"))

    def test_junk_entries_are_rejected(self):
        """Obvious test/junk entries (single char name, 'test' brand) must be filtered out."""
        self.assertFalse(_is_quality_product("test", "test"))
        self.assertFalse(_is_quality_product("a", "b"))

    def test_very_short_name_is_rejected(self):
        """Single-character product names must not pass."""
        self.assertFalse(_is_quality_product("a", "brand"))


# =============================================================================
# 2. API TESTS — Full HTTP Round-Trips via Django Test Client
#    Uses Django's built-in test client (no real server needed).
# =============================================================================

class HealthCheckAPITest(TestCase):
    """Tests for GET /api/health/"""

    def setUp(self):
        self.client = Client()

    def test_health_check_returns_200(self):
        """Health endpoint must return HTTP 200 OK."""
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)

    def test_health_check_response_structure(self):
        """Response must contain 'status: healthy'."""
        response = self.client.get(reverse('health_check'))
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')

    def test_health_check_services_present(self):
        """Response must declare available services."""
        response = self.client.get(reverse('health_check'))
        data = response.json()
        self.assertIn('services', data)


class SearchProductAPITest(TestCase):
    """Tests for GET /api/search-product/"""

    def setUp(self):
        self.client = Client()

    def test_missing_query_returns_400(self):
        """Search with no query param must return HTTP 400 Bad Request."""
        response = self.client.get(reverse('search_product'))
        self.assertEqual(response.status_code, 400)

    def test_empty_query_returns_400(self):
        """An empty 'q' parameter must return HTTP 400."""
        response = self.client.get(reverse('search_product'), {'q': ''})
        self.assertEqual(response.status_code, 400)

    def test_valid_search_returns_200(self):
        """A real query must return HTTP 200 (may return empty products but not error)."""
        response = self.client.get(reverse('search_product'), {'q': 'Maggi'})
        self.assertEqual(response.status_code, 200)

    def test_query_too_long_returns_400(self):
        """A query longer than 200 characters must return HTTP 400."""
        long_query = 'a' * 201
        response = self.client.get(reverse('search_product'), {'q': long_query})
        self.assertEqual(response.status_code, 400)

    def test_search_response_has_success_key(self):
        """All search responses must have a 'success' key."""
        response = self.client.get(reverse('search_product'), {'q': 'Oreo'})
        data = response.json()
        self.assertIn('success', data)


class AnalyzeTextAPITest(TestCase):
    """Tests for POST /api/analyze/text/"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('analyze_text')

    def _post(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

    def test_empty_text_returns_400(self):
        """Empty ingredient text must return HTTP 400."""
        response = self._post({'text': ''})
        self.assertEqual(response.status_code, 400)

    def test_missing_text_returns_400(self):
        """No 'text' key in body must return HTTP 400."""
        response = self._post({})
        self.assertEqual(response.status_code, 400)

    def test_text_too_short_returns_400(self):
        """Text under 3 characters must return HTTP 400."""
        response = self._post({'text': 'ab'})
        self.assertEqual(response.status_code, 400)

    def test_text_too_long_returns_400(self):
        """Text over 5000 characters must return HTTP 400."""
        long_text = 'water, ' * 900  # ~5400 chars
        response = self._post({'text': long_text})
        self.assertEqual(response.status_code, 400)

    def test_valid_text_returns_200(self):
        """Valid ingredient text must return HTTP 200."""
        response = self._post({'text': 'water, sugar, salt, refined wheat flour'})
        self.assertEqual(response.status_code, 200)

    def test_response_has_success_key(self):
        """All responses must include a 'success' key."""
        response = self._post({'text': 'water, sugar, salt'})
        data = response.json()
        self.assertIn('success', data)


class AnalyzeProductAPITest(TestCase):
    """Tests for POST /api/analyze-product/"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('analyze_product')

    def _post(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

    def test_no_barcode_no_ingredients_returns_400(self):
        """Body with neither barcode nor ingredients_text must return HTTP 400."""
        response = self._post({})
        self.assertEqual(response.status_code, 400)

    def test_empty_barcode_and_no_ingredients_returns_400(self):
        """Empty barcode and no ingredients must return HTTP 400."""
        response = self._post({'barcode': '', 'ingredients_text': ''})
        self.assertEqual(response.status_code, 400)

    def test_with_ingredients_text_returns_200(self):
        """Supplying ingredients_text directly (no barcode) must return HTTP 200."""
        response = self._post({'ingredients_text': 'water, sugar, citric acid, natural flavors'})
        self.assertEqual(response.status_code, 200)


class AlternativesAPITest(TestCase):
    """Tests for GET /api/alternatives/"""

    def setUp(self):
        self.client = Client()

    def test_missing_category_returns_400(self):
        """No category param must return HTTP 400."""
        response = self.client.get(reverse('get_alternatives'))
        self.assertEqual(response.status_code, 400)

    def test_valid_category_returns_200(self):
        """A valid category must return HTTP 200."""
        response = self.client.get(reverse('get_alternatives'), {'category': 'biscuits'})
        self.assertEqual(response.status_code, 200)


class ContactAPITest(TestCase):
    """Tests for POST /api/contact/"""

    def setUp(self):
        # DRF throttling uses Django's cache backend to count requests per IP.
        # Clearing the cache before each test resets that counter to zero,
        # so the 5/hour ContactRateThrottle doesn't block test-to-test requests.
        cache.clear()
        self.client = Client()
        self.url = reverse('contact_submit')

    def _post(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

    def test_valid_contact_returns_201(self):
        """A fully valid contact form must return HTTP 201 Created."""
        response = self._post({
            'name': 'Test User',
            'email': 'test@example.com',
            'message': 'Hello, this is a test message.'
        })
        self.assertEqual(response.status_code, 201)

    def test_missing_name_returns_400(self):
        """Missing name field must return HTTP 400."""
        response = self._post({'email': 'test@example.com', 'message': 'Hi'})
        self.assertEqual(response.status_code, 400)

    def test_invalid_email_returns_400(self):
        """Invalid email format must return HTTP 400."""
        response = self._post({'name': 'Test', 'email': 'not-an-email', 'message': 'Hi'})
        self.assertEqual(response.status_code, 400)

    def test_name_too_long_returns_400(self):
        """Name over 100 characters must return HTTP 400."""
        response = self._post({
            'name': 'A' * 101,
            'email': 'test@example.com',
            'message': 'Valid message.'
        })
        self.assertEqual(response.status_code, 400)

    def test_message_too_long_returns_400(self):
        """Message over 2000 characters must return HTTP 400."""
        response = self._post({
            'name': 'Test',
            'email': 'test@example.com',
            'message': 'x' * 2001
        })
        self.assertEqual(response.status_code, 400)


# =============================================================================
# 3. SECURITY TESTS — Input Validation Edge Cases
#    Proves that your security guards correctly block malicious input.
# =============================================================================

class SecurityInputValidationTest(TestCase):
    """Tests that security guards block malicious input to POST /api/analyze/text/."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('analyze_text')

    def _post(self, text):
        return self.client.post(
            self.url,
            data=json.dumps({'text': text}),
            content_type='application/json'
        )

    def test_sql_injection_is_blocked(self):
        """SQL injection patterns must be rejected with HTTP 400."""
        response = self._post("UNION SELECT * FROM users; DROP TABLE analyzer_contact")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get('error'), 'INVALID_INPUT')

    def test_xss_script_tag_is_blocked(self):
        """XSS script injection must be rejected with HTTP 400."""
        response = self._post("<script>alert('xss')</script>")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get('error'), 'INVALID_INPUT')

    def test_javascript_protocol_is_blocked(self):
        """javascript: protocol in input must be blocked."""
        response = self._post("javascript:void(0)")
        self.assertEqual(response.status_code, 400)

    def test_iframe_injection_is_blocked(self):
        """iframe tag injection must be blocked."""
        response = self._post("<iframe src='evil.com'></iframe>")
        self.assertEqual(response.status_code, 400)

    def test_excessive_special_chars_are_blocked(self):
        """More than 10 special characters must be rejected."""
        response = self._post("water{{{{{{{{{{{{{")
        self.assertEqual(response.status_code, 400)

    def test_normal_ingredient_text_passes(self):
        """Normal unicode ingredient text (e.g., µg, %, °) must not be blocked."""
        response = self._post("water, sugar (12%), vitamin C (ascorbic acid), salt")
        self.assertEqual(response.status_code, 200)
