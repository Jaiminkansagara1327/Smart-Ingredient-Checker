"""
Custom Security Middleware for Ingrexa
Provides additional security layers beyond Django's built-in protections
"""
import logging
import time
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger('django.security')


class SecurityHeadersMiddleware:
    """
    Add comprehensive security headers to all responses.
    Covers findings: CSP (HIGH), Referrer-Policy (LOW), X-Frame-Options (LOW),
    Permissions-Policy (INFO).
    """
    # Auth endpoints that issue tokens — need strict SameSite cookie policy
    _AUTH_PATHS = (
        '/api/auth/token/',
        '/api/auth/register/',
        '/api/auth/google-login/',
        '/api/auth/token/refresh/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # ── Fundamental headers (always) ──────────────────────────────────
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), payment=(self)'
        )
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Resource-Policy'] = 'same-site'

        # ── Content-Security-Policy ───────────────────────────────────────
        # Using a strict allowlist.  'unsafe-inline' for style is required
        # by many font/icon CDNs; tighten further with nonces if you add
        # a template-rendering layer.
        csp_directives = [
            "default-src 'self'",
            "script-src 'self'",                          # no inline JS
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://api.razorpay.com https://lumberjack.razorpay.com",
            "frame-src https://api.razorpay.com",
            "object-src 'none'",
            "base-uri 'self'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "upgrade-insecure-requests",
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)

        # ── Remove server information leakage ─────────────────────────────
        for header in ('Server', 'X-Powered-By'):
            if header in response:
                try:
                    del response[header]
                except (KeyError, TypeError):
                    pass

        return response


class RequestValidationMiddleware:
    """
    Validate all incoming requests for suspicious patterns
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Suspicious patterns to block
        self.blocked_patterns = [
            'eval(', 'exec(', '__import__',  # Python code injection
            'base64_decode', 'system(',       # Shell injection
            'file_get_contents',               # PHP injection
            '../', '..\\',                     # Path traversal
            'etc/passwd', 'etc/shadow',        # Linux system files
            'win.ini', 'boot.ini',             # Windows system files
        ]
    
    def __call__(self, request):
        # Check request path
        path = request.get_full_path()
        for pattern in self.blocked_patterns:
            if pattern in path.lower():
                logger.warning(f"[SECURITY] Blocked suspicious request: {path} from {self.get_client_ip(request)}")
                return JsonResponse({
                    'error': 'Invalid request',
                    'message': 'Your request has been blocked for security reasons.'
                }, status=403)
        
        # Check request body for POST requests
        if request.method == 'POST':
            try:
                body = request.body.decode('utf-8').lower()
                for pattern in self.blocked_patterns:
                    if pattern in body:
                        logger.warning(f"[SECURITY] Blocked suspicious POST data from {self.get_client_ip(request)}")
                        return JsonResponse({
                            'error': 'Invalid input',
                            'message': 'Your input has been blocked for security reasons.'
                        }, status=403)
            except (UnicodeDecodeError, AttributeError):
                pass
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class IPRateLimitMiddleware:
    """
    IP-based rate limiting (global across all endpoints).
    Prevents brute force and DDoS attacks.
    Adds X-RateLimit-Limit / X-RateLimit-Remaining headers (finding #16).
    Uses in-memory storage — Redis is used by DRF throttles for auth paths.
    """
    # Class-level storage (in-memory, worker-local)
    _requests = {}

    # Auth paths get their own stricter limit (5 req / 15 min)
    _AUTH_PATHS = (
        '/api/auth/token/',
        '/api/auth/register/',
        '/api/auth/google-login/',
        '/api/auth/token/refresh/',
    )
    AUTH_MAX_REQUESTS = 5
    AUTH_WINDOW_SECONDS = 900   # 15 minutes

    GLOBAL_MAX_REQUESTS = 200
    GLOBAL_WINDOW_SECONDS = 3600  # 1 hour

    # IPs that bypass rate limiting (loopback used during automated tests)
    _BYPASS_IPS = frozenset()   # empty in prod; populated in test settings

    def __init__(self, get_response):
        self.get_response = get_response

    @classmethod
    def reset(cls):
        """Clear all counters — call in test setUp to ensure isolation."""
        cls._requests.clear()

    def __call__(self, request):
        # Skip rate limiting for health check and whitelisted IPs
        if request.path == '/api/health/':
            return self.get_response(request)

        ip = self.get_client_ip(request)

        if ip in self._BYPASS_IPS:
            return self.get_response(request)

        current_time = time.time()

        is_auth = any(request.path.startswith(p) for p in self._AUTH_PATHS)
        max_req = self.AUTH_MAX_REQUESTS if is_auth else self.GLOBAL_MAX_REQUESTS
        window = self.AUTH_WINDOW_SECONDS if is_auth else self.GLOBAL_WINDOW_SECONDS
        cache_key = f"{ip}:{'auth' if is_auth else 'global'}"

        # Clean up old entries
        self._cleanup_old_entries(current_time)

        if cache_key not in self._requests:
            self._requests[cache_key] = {'count': 0, 'start_time': current_time}

        request_data = self._requests[cache_key]
        elapsed_time = current_time - request_data['start_time']

        if elapsed_time > window:
            request_data = {'count': 1, 'start_time': current_time}
            self._requests[cache_key] = request_data
        else:
            request_data['count'] += 1

        remaining = max(0, max_req - request_data['count'])

        if request_data['count'] > max_req:
            logger.warning(
                f"[SECURITY] Rate limit exceeded for IP: {ip} path: {request.path}"
            )
            response = JsonResponse({
                'error': 'Too many requests',
                'message': 'Rate limit exceeded. Please try again later.',
                'retry_after': int(window - elapsed_time),
            }, status=429)
            response['X-RateLimit-Limit'] = str(max_req)
            response['X-RateLimit-Remaining'] = '0'
            response['Retry-After'] = str(int(window - elapsed_time))
            return response

        response = self.get_response(request)
        response['X-RateLimit-Limit'] = str(max_req)
        response['X-RateLimit-Remaining'] = str(remaining)
        return response

    def _cleanup_old_entries(self, current_time):
        """Remove entries older than the longest window."""
        max_window = max(self.AUTH_WINDOW_SECONDS, self.GLOBAL_WINDOW_SECONDS)
        to_remove = [
            key for key, data in list(self._requests.items())
            if current_time - data['start_time'] > max_window
        ]
        for key in to_remove:
            self._requests.pop(key, None)

    def get_client_ip(self, request):
        """Get real client IP, honouring the first hop in X-Forwarded-For."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take only the first address (leftmost = real client)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
