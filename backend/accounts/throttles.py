"""
Per-endpoint throttle classes for authentication views.
Rates are configured in settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].

These use the Redis cache (via django-redis) so limits are shared across
Gunicorn workers and survive restarts.
"""
from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """5 login attempts per 15 minutes per IP (finding #6)."""
    scope = 'login'


class RegisterRateThrottle(AnonRateThrottle):
    """10 registration attempts per hour per IP."""
    scope = 'register'


class GoogleLoginRateThrottle(AnonRateThrottle):
    """10 Google OAuth attempts per hour per IP."""
    scope = 'google'
