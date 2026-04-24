"""
accounts/tests_security.py — Regression tests for all security findings

Run with:
    python manage.py test accounts.tests_security --verbosity=2

Findings covered:
  [CRITICAL] #1  Refresh token in HttpOnly cookie (not response body)
  [HIGH]     #2  Auth relies on HttpOnly cookie, not JS-accessible storage
  [HIGH]     #3  Access token short-lived (15 min)
  [HIGH]     #5  CSP header present on all responses
  [HIGH]     #6  Login endpoint rate-limited (5 req / 15 min via middleware)
  [MEDIUM]   #10 No error detail leakage in 500 responses
  [MEDIUM]   #11 HttpOnly, Secure, SameSite on cookie
  [LOW]      #14 Referrer-Policy header present
  [LOW]      #15 X-Frame-Options header present
  [INFO]     #16 X-RateLimit-Limit header present
  [INFO]     #18 Permissions-Policy header present
"""
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from analyzer.middleware import IPRateLimitMiddleware

User = get_user_model()

# Use a unique IP per test class to avoid cross-test rate limit bleed
_AUTH_TEST_IP   = '10.0.99.1'
_HEADER_TEST_IP = '10.0.99.2'
_RATE_TEST_IP   = '10.0.99.3'
_ERROR_TEST_IP  = '10.0.99.4'
_COOKIE_TEST_IP = '10.0.99.5'


class SecurityHeadersTest(TestCase):
    """Every response must carry the mandatory security headers (findings #5, #14, #15, #18)."""

    def setUp(self):
        IPRateLimitMiddleware.reset()
        self.client = APIClient(REMOTE_ADDR=_HEADER_TEST_IP)

    def _get_response(self):
        # /api/schema/ is always public and handled by drf_spectacular
        return self.client.get('/api/schema/', format='json')

    def test_csp_header_present(self):
        """[HIGH #5] Content-Security-Policy must be set."""
        res = self._get_response()
        self.assertIn('Content-Security-Policy', res)
        csp = res['Content-Security-Policy']
        self.assertIn("default-src 'self'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("frame-ancestors 'none'", csp)

    def test_x_frame_options(self):
        """[LOW #15] X-Frame-Options: DENY must be present."""
        res = self._get_response()
        self.assertEqual(res.get('X-Frame-Options', '').upper(), 'DENY')

    def test_referrer_policy(self):
        """[LOW #14] Referrer-Policy must be strict-origin-when-cross-origin."""
        res = self._get_response()
        self.assertEqual(
            res.get('Referrer-Policy', ''),
            'strict-origin-when-cross-origin'
        )

    def test_permissions_policy(self):
        """[INFO #18] Permissions-Policy must be present."""
        res = self._get_response()
        self.assertIn('Permissions-Policy', res)
        pp = res['Permissions-Policy']
        self.assertIn('camera=()', pp)
        self.assertIn('microphone=()', pp)

    def test_x_ratelimit_headers(self):
        """[INFO #16] X-RateLimit-Limit and X-RateLimit-Remaining must be present."""
        res = self._get_response()
        self.assertIn('X-RateLimit-Limit', res,
                      "X-RateLimit-Limit header missing from non-health-check response")
        self.assertIn('X-RateLimit-Remaining', res,
                      "X-RateLimit-Remaining header missing")


class RefreshTokenCookieTest(TestCase):
    """
    [CRITICAL #1, HIGH #2, MEDIUM #11]
    Refresh token must be in an HttpOnly cookie, never in the response body.
    Each test uses its own IP bucket so the middleware counter doesn't bleed.
    """

    def setUp(self):
        IPRateLimitMiddleware.reset()
        self.client = APIClient(REMOTE_ADDR=_COOKIE_TEST_IP)
        self.user = User.objects.create_user(
            username='sectest@example.com',
            email='sectest@example.com',
            password='StrongPass!99',
        )

    def test_login_sets_httponly_cookie(self):
        """Refresh token is in an HttpOnly cookie after successful login."""
        res = self.client.post('/api/auth/token/', {
            'email': 'sectest@example.com',
            'password': 'StrongPass!99',
        }, format='json', REMOTE_ADDR='10.0.99.10')

        self.assertEqual(res.status_code, 200,
                         f"Login failed with {res.status_code}: {res.content}")

        # ── The refresh cookie must exist ──
        cookie_name = settings.JWT_AUTH_COOKIE
        self.assertIn(cookie_name, res.cookies, "Refresh cookie must be set")

        cookie = res.cookies[cookie_name]
        self.assertTrue(cookie['httponly'], "Cookie must be HttpOnly")
        self.assertIn(cookie.get('samesite', '').lower(), ('lax', 'strict', 'none'))

        # ── The refresh token must NOT appear in the JSON body ──
        body = res.json()
        self.assertNotIn('refresh', body, "Refresh token must NOT be in JSON body")
        self.assertIn('access', body, "Access token must be in JSON body")

    def test_refresh_reads_from_cookie(self):
        """Token refresh must read from the HttpOnly cookie, not the request body."""
        # Use a fresh unique IP to avoid hitting the rate limit
        fresh_ip = '10.0.99.11'
        # Login to get a cookie
        self.client.post('/api/auth/token/', {
            'email': 'sectest@example.com',
            'password': 'StrongPass!99',
        }, format='json', REMOTE_ADDR=fresh_ip)

        # Refresh WITHOUT providing a body token — must still work via cookie
        res = self.client.post('/api/auth/token/refresh/', {}, format='json',
                               REMOTE_ADDR=fresh_ip)
        self.assertEqual(res.status_code, 200,
                         f"Refresh failed with {res.status_code}: {res.content}")
        body = res.json()
        self.assertIn('access', body)

    def test_refresh_fails_without_cookie(self):
        """Without the HttpOnly cookie the refresh endpoint returns 401."""
        fresh_client = APIClient(REMOTE_ADDR='10.0.99.12')  # no cookie jar
        res = fresh_client.post('/api/auth/token/refresh/', {}, format='json')
        self.assertEqual(res.status_code, 401,
                         f"Expected 401 without cookie, got {res.status_code}")

    def test_body_refresh_token_ignored(self):
        """A refresh token submitted in the body (old behaviour) is ignored."""
        refresh = RefreshToken.for_user(self.user)
        fresh_client = APIClient(REMOTE_ADDR='10.0.99.13')  # no cookie jar
        res = fresh_client.post('/api/auth/token/refresh/', {
            'refresh': str(refresh),
        }, format='json')
        # Without the cookie this must fail even though a valid token is in the body
        self.assertEqual(res.status_code, 401,
                         f"Body-only refresh should be rejected, got {res.status_code}")


class LoginRateLimitTest(TestCase):
    """[HIGH #6, #7] Login endpoint must be rate-limited by the middleware."""

    def setUp(self):
        IPRateLimitMiddleware.reset()
        # Use a dedicated IP so only THIS test's requests are counted
        self.rl_ip = '10.0.99.20'
        self.client = APIClient(REMOTE_ADDR=self.rl_ip)
        User.objects.create_user(
            username='ratetest@example.com',
            email='ratetest@example.com',
            password='StrongPass!99',
        )

    def test_auth_middleware_rate_limited(self):
        """After 5 failed attempts from the same IP, the middleware returns 429."""
        payload = {'email': 'ratetest@example.com', 'password': 'wrong_password'}
        responses = [
            self.client.post('/api/auth/token/', payload, format='json',
                             REMOTE_ADDR=self.rl_ip)
            for _ in range(7)
        ]
        status_codes = [r.status_code for r in responses]
        self.assertIn(429, status_codes,
                      f"Expected a 429 after repeated attempts, got: {status_codes}")


class ErrorLeakageTest(TestCase):
    """[MEDIUM #10] 500 errors must not expose stack traces or internal details."""

    def setUp(self):
        IPRateLimitMiddleware.reset()
        self.client = APIClient(REMOTE_ADDR=_ERROR_TEST_IP)

    def test_internal_error_is_sanitised(self):
        """
        Simulate a view raising an unhandled exception; the response must NOT
        contain any exception message.
        """
        User.objects.filter(username='leak@example.com').delete()
        with patch('accounts.views.RegisterSerializer.save',
                   side_effect=RuntimeError("DB is down!")):
            res = self.client.post('/api/auth/register/', {
                'email': 'leak@example.com',
                'username': 'leak@example.com',
                'password': 'StrongPass!99',
                'first_name': 'Leak',
            }, format='json')

        # In DEBUG=False the message must be generic
        if not settings.DEBUG:
            body = res.json()
            self.assertNotIn('DB is down', str(body),
                             "Internal error detail must not be leaked")
            self.assertNotIn('Traceback', str(body))


class JWTLifetimeTest(TestCase):
    """[HIGH #3/4] Access token lifetime must be ≤ 15 minutes."""

    def test_access_token_lifetime(self):
        expected_max = timedelta(minutes=15)
        actual = settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(days=1))
        self.assertLessEqual(
            actual, expected_max,
            f"ACCESS_TOKEN_LIFETIME {actual} exceeds the 15-minute security limit"
        )

    def test_refresh_token_rotation_enabled(self):
        self.assertTrue(
            settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False),
            "ROTATE_REFRESH_TOKENS must be True"
        )

    def test_refresh_token_blacklist_enabled(self):
        self.assertTrue(
            settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION', False),
            "BLACKLIST_AFTER_ROTATION must be True"
        )
