from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
import traceback
import re
import html
from .models import ContactMessage
from .serializers import ContactMessageSerializer
from .ai_service import analyze_product_from_text

# Custom throttle class for stricter rate limiting
class AnalysisRateThrottle(AnonRateThrottle):
    rate = '50/hour'  # 50 analysis requests per hour

@api_view(['POST'])
@throttle_classes([AnalysisRateThrottle])
def analyze_text(request):
    """
    Analyze product from manually entered ingredient text
    SECURITY: Input validation, sanitization, length limits
    """
    text = request.data.get('text', '')
    
    # Security Check 1: Empty input
    if not text or not text.strip():
        return Response(
            {
                'success': False,
                'error': 'NO_TEXT',
                'message': 'No ingredient text provided',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Security Check 2: Length limits (prevent DoS)
    MAX_INPUT_LENGTH = 5000  # 5000 characters max
    if len(text) > MAX_INPUT_LENGTH:
        return Response(
            {
                'success': False,
                'error': 'INPUT_TOO_LONG',
                'message': f'Input text too long. Maximum {MAX_INPUT_LENGTH} characters allowed.',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Security Check 3: Minimum length (prevent spam)
    MIN_INPUT_LENGTH = 3
    if len(text.strip()) < MIN_INPUT_LENGTH:
        return Response(
            {
                'success': False,
                'error': 'INPUT_TOO_SHORT',
                'message': 'Please enter at least a few characters.',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Security Check 4: Detect and block SQL injection patterns
    sql_injection_patterns = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(--|\#|\/\*|\*\/)",  # SQL comments
        r"(\bEXEC\b|\bEXECUTE\b)",
        r"(\bxp_cmdshell\b)",
    ]
    
    text_upper = text.upper()
    for pattern in sql_injection_patterns:
        if re.search(pattern, text_upper, re.IGNORECASE):
            return Response(
                {
                    'success': False,
                    'error': 'INVALID_INPUT',
                    'message': 'Invalid input detected. Please enter only food ingredients.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Security Check 5: Detect script injection (XSS)
    xss_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',  # onclick, onload, etc.
        r'<iframe',
        r'<embed',
        r'<object',
    ]
    
    for pattern in xss_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return Response(
                {
                    'success': False,
                    'error': 'INVALID_INPUT',
                    'message': 'Invalid characters detected. Please enter plain text ingredients only.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Security Check 6: Excessive special characters (potential attack)
    special_char_count = len(re.findall(r'[<>{}[\]\\|`~]', text))
    if special_char_count > 10:
        return Response(
            {
                'success': False,
                'error': 'INVALID_INPUT',
                'message': 'Too many special characters. Please enter plain ingredient text.',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Security Check 7: Sanitize HTML entities
    sanitized_text = html.unescape(text)
    
    # Security Check 8: Line count limit (prevent abuse)
    MAX_LINES = 100
    line_count = len(sanitized_text.split('\n'))
    if line_count > MAX_LINES:
        return Response(
            {
                'success': False,
                'error': 'TOO_MANY_LINES',
                'message': f'Too many lines. Maximum {MAX_LINES} lines allowed.',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Log analysis attempt (for audit trail)
        print(f"[SECURITY] Analyzing text (length: {len(sanitized_text)}, lines: {line_count})")
        
        # Analyze ingredients
        analysis_result = analyze_product_from_text(sanitized_text.strip())
        
        # If analysis failed
        if not analysis_result.get('success', True):
            return Response(analysis_result, status=status.HTTP_200_OK)
        
        # Add metadata about manual entry
        analysis_result['input_method'] = 'manual'
        
        # Return successful analysis
        return Response(analysis_result, status=status.HTTP_200_OK)
    
    except Exception as e:
        # Log error without exposing internal details
        print(f"[SECURITY] Analysis error: {type(e).__name__}")
        print(traceback.format_exc())
        
        # Return generic error message (don't expose internals)
        return Response(
            {
                'success': False,
                'error': 'ANALYSIS_FAILED',
                'message': 'An error occurred during analysis. Please try again.',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Custom throttle for contact form (stricter to prevent spam)
class ContactRateThrottle(AnonRateThrottle):
    rate = '5/hour'  # Only 5 contact submissions per hour

@api_view(['POST'])
@throttle_classes([ContactRateThrottle])
def contact_submit(request):
    """
    Handle contact form submission
    SECURITY: Rate limited, validated inputs
    """
    # Security: Validate request has required fields
    required_fields = ['name', 'email', 'message']
    for field in required_fields:
        if field not in request.data or not request.data[field].strip():
            return Response({
                'success': False,
                'errors': {field: [f'{field.capitalize()} is required.']}
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Security: Length limits
    if len(request.data.get('name', '')) > 100:
        return Response({
            'success': False,
            'errors': {'name': ['Name too long (max 100 characters).']}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(request.data.get('message', '')) > 2000:
        return Response({
            'success': False,
            'errors': {'message': ['Message too long (max 2000 characters).']}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Security: Email validation (basic regex)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, request.data.get('email', '')):
        return Response({
            'success': False,
            'errors': {'email': ['Invalid email format.']}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Security: Sanitize inputs
    sanitized_data = {
        'name': html.escape(request.data['name'].strip()),
        'email': request.data['email'].strip().lower(),
        'message': html.escape(request.data['message'].strip())
    }
    
    serializer = ContactMessageSerializer(data=sanitized_data)
    if serializer.is_valid():
        serializer.save()
        
        # Send email using lightweight smtplib in a non-daemon thread
        # Django's send_mail + SMTP backend causes OOM on Render free tier
        # because torch/easyocr already consume most of the 512MB RAM
        def send_lightweight_email():
            import smtplib
            from email.mime.text import MIMEText
            
            try:
                from django.conf import settings
                
                to_email = getattr(settings, 'CONTACT_EMAIL_RECIPIENT', '') or getattr(settings, 'EMAIL_HOST_USER', '')
                from_email = getattr(settings, 'EMAIL_HOST_USER', '')
                password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
                host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
                port = int(getattr(settings, 'EMAIL_PORT', 587))
                
                if not from_email or not password or not to_email:
                    print(f"[EMAIL] Skipping - missing credentials (from={bool(from_email)}, pass={bool(password)}, to={bool(to_email)})")
                    return
                
                body = f"""New contact message from Ingrexa:\n\nFrom: {sanitized_data['name']}\nEmail: {sanitized_data['email']}\n\nMessage:\n{sanitized_data['message']}\n\n---\nSent from Ingrexa Contact Form"""
                
                msg = MIMEText(body)
                msg['Subject'] = f"New Contact Message from {sanitized_data['name']}"
                msg['From'] = from_email
                msg['To'] = to_email
                
                print(f"[EMAIL] Connecting to {host}:{port}...")
                with smtplib.SMTP(host, port, timeout=10) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(from_email, password)
                    server.sendmail(from_email, to_email, msg.as_string())
                
                print(f"[EMAIL] Sent successfully to {to_email}")
            except Exception as e:
                print(f"[EMAIL ERROR] {type(e).__name__}: {str(e)}")
        
        # Use non-daemon thread so it can survive after response is sent
        import threading
        email_thread = threading.Thread(target=send_lightweight_email)
        email_thread.daemon = False
        email_thread.start()
        
        print(f"[SECURITY] Contact form submitted: {sanitized_data['email']}")
        return Response({
            'success': True,
            'message': 'Message sent successfully!'
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def health_check(request):
    """
    Simple health check endpoint
    """
    return Response({
        'status': 'healthy',
        'services': {
            'text_analyzer': True
        }
    })
