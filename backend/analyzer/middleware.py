"""
Custom Security Middleware for Ingrexa
Provides additional security layers beyond Django's built-in protections
"""
import logging
from django.http import JsonResponse
import time

logger = logging.getLogger('django.security')


class SecurityHeadersMiddleware:
    """
    Add additional security headers to all responses
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'same-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Remove server information leakage
        if 'Server' in response:
            try:
                response['Server'] = ''
            except (KeyError, TypeError):
                pass
        if 'X-Powered-By' in response:
            try:
                response['X-Powered-By'] = ''
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
    IP-based rate limiting (global across all endpoints)
    Prevents brute force and DDoS attacks
    Uses in-memory storage for simplicity
    """
    # Class-level storage (in-memory)
    _requests = {}
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_requests = 200  # Max requests per window
        self.window_seconds = 3600  # 1 hour window
    
    def __call__(self, request):
        # Skip rate limiting for health check
        if request.path == '/api/health/':
            return self.get_response(request)
        
        ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Clean up old entries
        self._cleanup_old_entries(current_time)
        
        # Get or create request data for this IP
        if ip not in self._requests:
            self._requests[ip] = {'count': 0, 'start_time': current_time}
        
        request_data = self._requests[ip]
        elapsed_time = current_time - request_data['start_time']
        
        # Reset if window expired
        if elapsed_time > self.window_seconds:
            request_data = {'count': 1, 'start_time': current_time}
            self._requests[ip] = request_data
        else:
            request_data['count'] += 1
        
        # Check if limit exceeded
        if request_data['count'] > self.max_requests:
            logger.warning(f"[SECURITY] Rate limit exceeded for IP: {ip}")
            return JsonResponse({
                'error': 'Too many requests',
                'message': 'You have exceeded the maximum number of requests. Please try again later.'
            }, status=429)
        
        return self.get_response(request)
    
    def _cleanup_old_entries(self, current_time):
        """Remove entries older than the window"""
        to_remove = []
        for ip, data in self._requests.items():
            if current_time - data['start_time'] > self.window_seconds:
                to_remove.append(ip)
        for ip in to_remove:
            self._requests.pop(ip, None)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
