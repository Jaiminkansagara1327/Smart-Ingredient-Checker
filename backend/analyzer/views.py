from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from drf_spectacular.utils import extend_schema
import traceback
import re
import html
import os
from .models import AnalysisRecord, ContactMessage, Product, ProductFavorite, SearchEvent
from .serializers import ContactMessageSerializer, AnalysisRecordSerializer, ProductFavoriteSerializer
from .ai_service import analyze_product_from_text
from .openfoodfacts_service import search_products as off_search, get_product_details as off_get_product, find_healthier_alternatives as off_find_alternatives

# ── Celery / Redis helpers ────────────────────────────────────────────────────
try:
    from celery.result import AsyncResult
    from .tasks import analyze_ingredients_task, send_contact_email_task
    CELERY_AVAILABLE = True
except Exception:
    CELERY_AVAILABLE = False
    AsyncResult = None


class AuthenticatedOnlyUserRateThrottle(UserRateThrottle):
    """
    Throttle authenticated users only.

    This keeps anonymous requests covered by the dedicated `AnonRateThrottle`
    scope without double-throttling them via the user scope.
    """

    def get_cache_key(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return None
        return super().get_cache_key(request, view)

# Analysis throttles for anonymous vs authenticated users
class AnalysisAnonRateThrottle(AnonRateThrottle):
    rate = '200/hour'  # 200 analysis requests per hour for anonymous users


class AnalysisUserRateThrottle(AuthenticatedOnlyUserRateThrottle):
    rate = '2000/hour'  # 10x higher for authenticated users


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "")

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AnalysisAnonRateThrottle, AnalysisUserRateThrottle])
def analyze_text(request):
    """
    Analyze product from manually entered ingredient text
    SECURITY: Input validation, sanitization, length limits
    """
    text = request.data.get('text', '')
    user_goal = request.data.get('user_goal', 'Regular')
    food_type = request.data.get('food_type', 'Solid')
    
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
        print(f"[SECURITY] Analyzing text (length: {len(sanitized_text)}, lines: {line_count})")

        if CELERY_AVAILABLE:
            # ── ASYNC path: dispatch to Celery worker ─────────────────────
            task = analyze_ingredients_task.apply_async(
                kwargs=dict(
                    text=sanitized_text.strip(),
                    macros={},
                    food_type=food_type,
                    user_goal=user_goal,
                    user_id=request.user.pk if request.user and request.user.is_authenticated else None,
                    input_method="manual",
                ),
                queue="analysis",
            )
            print(f"[CELERY] analyze_text dispatched → task_id={task.id}")
            return Response(
                {
                    "success": True,
                    "async": True,
                    "task_id": task.id,
                    "message": "Analysis started. Poll /api/task/<task_id>/ for results.",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        else:
            # ── SYNC fallback (no Redis / dev mode) ───────────────────────
            analysis_result = analyze_product_from_text(
                text=sanitized_text.strip(),
                macros={},
                food_type=food_type,
                user_goal=user_goal,
            )
            if not analysis_result.get('success', True):
                return Response(analysis_result, status=status.HTTP_200_OK)

            analysis_result['input_method'] = 'manual'
            analysis_result['raw_ingredients_text'] = sanitized_text.strip()

            if request.user and request.user.is_authenticated:
                try:
                    product_data = analysis_result.get("product", {}) or {}
                    analysis_for_storage = dict(analysis_result)
                    analysis_for_storage.pop("raw_ingredients_text", None)
                    AnalysisRecord.objects.create(
                        user=request.user,
                        input_method=AnalysisRecord.INPUT_TEXT,
                        input_text_preview=sanitized_text.strip()[:400],
                        product_name=product_data.get("name", ""),
                        product_brand=product_data.get("brand", ""),
                        user_goal=user_goal,
                        food_type=food_type,
                        confidence=analysis_result.get("confidence"),
                        score=analysis_result.get("score"),
                        nova_group=analysis_result.get("nova_group"),
                        nutriscore_grade=product_data.get("nutriscore_grade", "") or "",
                        analysis_json=analysis_for_storage,
                    )
                except Exception as e:
                    print(f"[AUDIT] Could not save AnalysisRecord: {type(e).__name__}")

            return Response(analysis_result, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"[SECURITY] Analysis error: {type(e).__name__}")
        print(traceback.format_exc())
        return Response(
            {
                'success': False,
                'error': 'ANALYSIS_FAILED',
                'message': 'An error occurred during analysis. Please try again.',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Contact throttles for anonymous vs authenticated users
class ContactAnonRateThrottle(AnonRateThrottle):
    rate = '5/hour'  # Only 5 contact submissions per hour for anonymous users


class ContactUserRateThrottle(AuthenticatedOnlyUserRateThrottle):
    rate = '20/hour'  # higher limit for authenticated users

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ContactAnonRateThrottle, ContactUserRateThrottle])
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

        # ── Send email: async via Celery if available, sync fallback ──────
        if CELERY_AVAILABLE:
            send_contact_email_task.apply_async(
                kwargs=dict(
                    name=sanitized_data['name'],
                    email=sanitized_data['email'],
                    message=sanitized_data['message'],
                ),
                queue="email",
            )
            print(f"[CELERY] Contact email task dispatched for {sanitized_data['email']}", flush=True)
        else:
            from_email = os.environ.get('EMAIL_HOST_USER', '')
            to_email = os.environ.get('CONTACT_EMAIL_RECIPIENT', from_email)
            subject = f"New Contact Message from {sanitized_data['name']}"
            body = (
                f"New contact message from Ingrexa:\n\n"
                f"From: {sanitized_data['name']}\n"
                f"Email: {sanitized_data['email']}\n\n"
                f"Message:\n{sanitized_data['message']}\n\n"
                f"---\nSent from Ingrexa Contact Form"
            )
            email_sent = False
            # Primary: SMTP
            try:
                from django.core.mail import send_mail
                send_mail(subject=subject, message=body, from_email=from_email,
                          recipient_list=[to_email], fail_silently=False)
                email_sent = True
                print(f"[EMAIL] SMTP sent to {to_email}", flush=True)
            except Exception as smtp_err:
                print(f"[EMAIL] SMTP failed: {smtp_err}. Trying Resend...", flush=True)
            # Fallback: Resend
            if not email_sent:
                try:
                    import requests as http_requests
                    resend_api_key = os.environ.get('RESEND_API_KEY', '')
                    if resend_api_key:
                        resp = http_requests.post(
                            'https://api.resend.com/emails',
                            headers={'Authorization': f'Bearer {resend_api_key}',
                                     'Content-Type': 'application/json'},
                            json={'from': 'Ingrexa Contact <onboarding@resend.dev>',
                                  'to': [to_email], 'subject': subject, 'text': body},
                            timeout=10,
                        )
                        print(f"[EMAIL] Resend response: {resp.status_code}", flush=True)
                    else:
                        print("[EMAIL] No Resend API key. Message saved to DB only.", flush=True)
                except Exception as resend_err:
                    print(f"[EMAIL] Resend also failed: {resend_err}", flush=True)

        print(f"[SECURITY] Contact form submitted: {sanitized_data['email']}", flush=True)
        return Response({
            'success': True,
            'message': 'Message sent successfully!'
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# ========================================
#  OpenFoodFacts Product Search & Analyze
# ========================================

class SearchAnonRateThrottle(AnonRateThrottle):
    rate = '3000/hour'  # 3000 search requests per hour to support instant autocomplete


class SearchUserRateThrottle(AuthenticatedOnlyUserRateThrottle):
    rate = '10000/hour'  # higher limit for authenticated users


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([SearchAnonRateThrottle, SearchUserRateThrottle])
def search_product(request):
    """
    Search local database for products by name or brand.
    Query params: ?q=<search_term>&page=1
    """
    query = request.query_params.get('q', '').strip()
    page = request.query_params.get('page', '1')
    local_only_str = request.query_params.get('local_only', 'false').lower()
    local_only = local_only_str == 'true'
    
    if not query:
        return Response(
            {'success': False, 'error': 'NO_QUERY', 'message': 'Please enter a search term.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Length limit
    if len(query) > 200:
        return Response(
            {'success': False, 'error': 'QUERY_TOO_LONG', 'message': 'Search query too long.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        page_num = max(1, int(page))
    except ValueError:
        page_num = 1
    
    print(f"[SEARCH] Searching database for: '{query}' (page {page_num})")
    result = off_search(query, page=page_num, page_size=10, local_only=local_only)

    # Save search event for authenticated + anonymous users.
    if result.get("success"):
        try:
            SearchEvent.objects.create(
                user=request.user if request.user and request.user.is_authenticated else None,
                query=query[:200],
                local_only=local_only,
                ip_address=get_client_ip(request)[:64],
                user_agent=get_user_agent(request)[:512],
            )
        except Exception as e:
            print(f"[AUDIT] Could not save SearchEvent: {type(e).__name__}")

    return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AnalysisAnonRateThrottle, AnalysisUserRateThrottle])
def analyze_product(request):
    """
    Fetch a product from OpenFoodFacts by barcode and analyze its ingredients.
    Body: { "barcode": "8901234567890" }
    Optionally accepts { "ingredients_text": "..." } if already available.
    """
    barcode = request.data.get('barcode', '').strip()
    supplied_ingredients = request.data.get('ingredients_text', '').strip()
    user_goal = request.data.get('user_goal', 'Regular')
    frontend_meta = request.data.get('product_meta', None)
    
    # User might define it, otherwise OpenFoodFacts tags determines it
    food_type = request.data.get('food_type', 'Solid')
    
    if not barcode and not supplied_ingredients:
        return Response(
            {'success': False, 'error': 'NO_BARCODE', 'message': 'Please provide a product barcode.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        product_info = frontend_meta
        ingredients_text = supplied_ingredients
        
        # If we have a barcode but no product info, fetch from OFF
        if barcode and not product_info:
            print(f"[PRODUCT] Fetching product details for barcode: {barcode}")
            product_result = off_get_product(barcode)
            
            if not product_result.get('success'):
                return Response(product_result, status=status.HTTP_200_OK)
            
            if not ingredients_text:
                ingredients_text = product_result.get('ingredients_text', '')
            product_info = product_result.get('product', {})
            
            # Map OFF categories to Food Type if the user hasn't explicitly set one
            if food_type == 'Solid' and product_info.get('categories_tags'):
                cat_tags = [c.lower() for c in product_info['categories_tags']]
                if any('beverage' in c or 'drink' in c or 'juice' in c or 'liquid' in c for c in cat_tags):
                    food_type = 'Liquid'
                elif any('cheese' in c or 'spread' in c or 'sauce' in c or 'paste' in c or 'yogurt' in c for c in cat_tags):
                    food_type = 'Semi-solid'
        
        if not ingredients_text:
            return Response({
                'success': False,
                'error': 'NO_INGREDIENTS',
                'message': 'No ingredient list found for this product. Try typing them manually.',
            }, status=status.HTTP_200_OK)
        
        # Analyze using the existing pipeline, passing OFF nutriments
        print(f"[PRODUCT] Analyzing ingredients (length: {len(ingredients_text)}) for goal: {user_goal} ({food_type})")

        macros = product_info.get('nutriments', {}) if product_info else {}

        if CELERY_AVAILABLE:
            # ── ASYNC path ────────────────────────────────────────────────
            task = analyze_ingredients_task.apply_async(
                kwargs=dict(
                    text=ingredients_text,
                    macros=macros,
                    food_type=food_type,
                    user_goal=user_goal,
                    user_id=request.user.pk if request.user and request.user.is_authenticated else None,
                    input_method='openfoodfacts' if not barcode else 'barcode',
                    barcode=barcode,
                    product_info=product_info,
                ),
                queue="analysis",
            )
            print(f"[CELERY] analyze_product dispatched → task_id={task.id}")
            return Response(
                {
                    "success": True,
                    "async": True,
                    "task_id": task.id,
                    "message": "Analysis started. Poll /api/task/<task_id>/ for results.",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        else:
            # ── SYNC fallback ─────────────────────────────────────────────
            analysis_result = analyze_product_from_text(
                text=ingredients_text,
                macros=macros,
                food_type=food_type,
                user_goal=user_goal,
            )
            analysis_result['input_method'] = 'openfoodfacts'
            analysis_result['raw_ingredients_text'] = ingredients_text

            if product_info:
                analysis_result['product_info'] = product_info
                if 'product' in analysis_result:
                    analysis_result['product']['name'] = product_info.get('name', analysis_result['product'].get('name', 'Unknown'))
                    analysis_result['product']['brand'] = product_info.get('brand', 'Unknown')
                    analysis_result['product']['image_url'] = product_info.get('image_url', '')
                    analysis_result['product']['nutriscore_grade'] = product_info.get('nutriscore_grade', '')
                analysis_result['_product_meta'] = {
                    'name': product_info.get('name', ''),
                    'brand': product_info.get('brand', ''),
                    'image_url': product_info.get('image_url', ''),
                    'categories': product_info.get('categories', ''),
                    'nutriscore_grade': product_info.get('nutriscore_grade', ''),
                    'barcode': barcode,
                    'nutriments': product_info.get('nutriments', None),
                }

            if request.user and request.user.is_authenticated:
                try:
                    product_data = analysis_result.get("product", {}) or {}
                    analysis_for_storage = dict(analysis_result)
                    analysis_for_storage.pop("raw_ingredients_text", None)
                    AnalysisRecord.objects.create(
                        user=request.user,
                        input_method=AnalysisRecord.INPUT_BARCODE if barcode else AnalysisRecord.INPUT_TEXT,
                        input_text_preview=ingredients_text.strip()[:400],
                        product_name=product_data.get("name", ""),
                        product_brand=product_data.get("brand", ""),
                        user_goal=user_goal,
                        food_type=food_type,
                        confidence=analysis_result.get("confidence"),
                        score=analysis_result.get("score"),
                        nova_group=analysis_result.get("nova_group"),
                        nutriscore_grade=product_data.get("nutriscore_grade", "") or "",
                        analysis_json=analysis_for_storage,
                    )
                except Exception as e:
                    print(f"[AUDIT] Could not save AnalysisRecord: {type(e).__name__}")

            return Response(analysis_result, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"[PRODUCT] Analysis error: {type(e).__name__}")
        print(traceback.format_exc())
        return Response(
            {'success': False, 'error': 'ANALYSIS_FAILED', 'message': 'An error occurred during analysis. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Task Status Polling Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
@extend_schema(tags=["Analysis"], summary="Poll an async analysis task by task_id")
def task_status(request, task_id: str):
    """
    GET /api/task/<task_id>/

    Returns the current status of a Celery task dispatched by
    analyze_text or analyze_product.

    Response shapes
    ---------------
    Pending  : { "state": "PENDING",  "status": "queued" }
    Running  : { "state": "STARTED",  "status": "processing" }
    Success  : { "state": "SUCCESS",  "status": "done", "result": { ...analysis... } }
    Failure  : { "state": "FAILURE",  "status": "error", "error": "..." }
    Retry    : { "state": "RETRY",    "status": "retrying" }
    """
    if not CELERY_AVAILABLE or AsyncResult is None:
        return Response(
            {'error': 'Async tasks are not available (Celery/Redis not configured).'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # Validate task_id (alphanumeric + hyphens only — Celery UUIDs)
    if not re.fullmatch(r'[a-f0-9\-]{36}', task_id):
        return Response(
            {'error': 'INVALID_TASK_ID', 'message': 'Invalid task ID format.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = AsyncResult(task_id)
    state = result.state  # PENDING | STARTED | RETRY | SUCCESS | FAILURE

    if state == 'SUCCESS':
        return Response({
            'state': state,
            'status': 'done',
            'result': result.result,   # The full analysis_result dict
        }, status=status.HTTP_200_OK)

    elif state == 'FAILURE':
        # Don't expose raw internal exception to the client
        return Response({
            'state': state,
            'status': 'error',
            'error': 'Analysis failed. Please try again.',
        }, status=status.HTTP_200_OK)

    elif state in ('STARTED', 'RETRY'):
        return Response({
            'state': state,
            'status': 'processing',
        }, status=status.HTTP_200_OK)

    else:  # PENDING (or unknown)
        return Response({
            'state': state,
            'status': 'queued',
        }, status=status.HTTP_200_OK)


@api_view(['GET', 'HEAD'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint
    """
    return Response({
        'status': 'healthy',
        'services': {
            'text_analyzer': True,
            'product_search': True
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([SearchAnonRateThrottle, SearchUserRateThrottle])
def get_alternatives(request):
    """
    Find healthier alternatives for a product.
    Query params: ?category=<category>&nutriscore=<grade>&name=<product_name>
    """
    category = request.query_params.get('category', '').strip()
    nutriscore = request.query_params.get('nutriscore', '').strip()
    product_name = request.query_params.get('name', '').strip()
    
    if not category:
        return Response(
            {'success': False, 'error': 'NO_CATEGORY', 'message': 'Category is required.', 'alternatives': []},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    print(f"[ALTERNATIVES] Finding alternatives for category='{category}', nutriscore='{nutriscore}'")
    result = off_find_alternatives(category, nutriscore, product_name)
    
    return Response(result, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
@extend_schema(tags=["Support"], summary="Support/donation links (free access)")
def support(request):
    """
    Public endpoint for "support the creator" links (no billing required).
    """

    message = os.getenv(
        "DONATION_MESSAGE",
        "If you find Ingrexa helpful, consider supporting the creator.",
    )

    buy_me_a_coffee_url = os.getenv("DONATION_BUY_ME_A_COFFEE_URL", "").strip()
    upi_url = os.getenv("DONATION_UPI_URL", "").strip()

    links = {}
    if buy_me_a_coffee_url:
        links["buy_me_a_coffee_url"] = buy_me_a_coffee_url
    if upi_url:
        links["upi_url"] = upi_url

    return Response(
        {"success": True, "message": message, "links": links},
        status=status.HTTP_200_OK,
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@extend_schema(tags=["User Data"], summary="Favorites (GET list, POST toggle/add)")
def favorites(request):
    """
    GET: list user's favorite products.
    POST: toggle favorite by `product_barcode` (or `barcode`).
    """

    if request.method == "GET":
        qs = ProductFavorite.objects.filter(user=request.user).select_related("product").order_by("-created_at")
        return Response(
            {"success": True, "items": ProductFavoriteSerializer(qs, many=True).data},
            status=status.HTTP_200_OK,
        )

    barcode = request.data.get("product_barcode", "") or request.data.get("barcode", "")
    barcode = barcode.strip()
    if not barcode:
        return Response(
            {"success": False, "error": "NO_PRODUCT_BARCODE", "message": "Provide product_barcode."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    product = Product.objects.filter(barcode=barcode).first()
    if not product:
        return Response(
            {"success": False, "error": "PRODUCT_NOT_FOUND", "message": "Product not found in local DB."},
            status=status.HTTP_404_NOT_FOUND,
        )

    existing = ProductFavorite.objects.filter(user=request.user, product=product).first()
    if existing:
        existing.delete()
        return Response(
            {"success": True, "status": "removed", "product_barcode": barcode},
            status=status.HTTP_200_OK,
        )

    ProductFavorite.objects.create(user=request.user, product=product)
    return Response(
        {"success": True, "status": "added", "product_barcode": barcode},
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@extend_schema(tags=["User Data"], summary="Analysis history for the authenticated user")
def analysis_history(request):
    """
    GET: list recent analyses for the authenticated user.
    Query params: ?limit=20 (max 50)
    """

    limit_str = request.query_params.get("limit", "20")
    try:
        limit = int(limit_str)
    except ValueError:
        limit = 20

    limit = max(1, min(limit, 50))

    base_qs = AnalysisRecord.objects.filter(user=request.user).order_by("-created_at")
    qs = base_qs[:limit]
    return Response(
        {"success": True, "count": base_qs.count(), "items": AnalysisRecordSerializer(qs, many=True).data},
        status=status.HTTP_200_OK,
    )


# ========================================
#  Razorpay Integration (Full API)
# ========================================
import razorpay

@api_view(['POST'])
@permission_classes([AllowAny])
@extend_schema(tags=["Finances"], summary="Create a new Razorpay Order")
def create_razorpay_order(request):
    """
    Step 1: Backend creates an Order ID.
    Returns: { 'id': 'order_XXX', 'amount': 10000, 'currency': 'INR', 'key_id': '...' }
    """
    try:
        # Get amount from request, default to 100 INR if not provided
        # Razorpay expects amount in PAISA (100 INR = 10000 Paisa)
        amount_in_rupees = int(request.data.get('amount', 49))  # Default to 49 INR
        amount_in_paisa = amount_in_rupees * 100

        client = razorpay.Client(
            auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
        )

        order_data = {
            'amount': amount_in_paisa,
            'currency': 'INR',
            'payment_capture': 1  # 1 = auto capture, 0 = manual
        }

        order = client.order.create(data=order_data)

        # Return order details plus the public KEY_ID for the frontend
        return Response({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key_id': os.getenv("RAZORPAY_KEY_ID")
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"[RAZORPAY] Order creation failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to create payment order.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@extend_schema(tags=["Finances"], summary="Verify a Razorpay Payment")
def verify_razorpay_payment(request):
    """
    Step 2: Backend verifies the signature sent by frontend after payment.
    Ensures the payment wasn't tampered with.
    """
    try:
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        client = razorpay.Client(
            auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
        )

        # Verify signature using SDK
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        # This will raise a SignatureVerificationError if signature is invalid
        client.utility.verify_payment_signature(params_dict)

        print(f"[RAZORPAY] Payment verified successfully: {razorpay_payment_id}")
        return Response({
            'success': True,
            'message': 'Payment verified successfully.'
        }, status=status.HTTP_200_OK)

    except razorpay.errors.SignatureVerificationError:
        print("[RAZORPAY] Signature verification failed!")
        return Response({
            'success': False,
            'message': 'Invalid payment signature.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"[RAZORPAY] Verification Error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error during verification.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@extend_schema(tags=["Finances"], summary="Handle Razorpay Webhooks (Success/Failed events)")
def razorpay_webhook(request):
    """
    Step 3: Razorpay Server calls this endpoint directly to confirm payment.
    This provides 'redundant' security in case the user's browser closes.
    """
    try:
        # Get raw data and signature from headers
        webhook_body = request.body.decode('utf-8')
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")

        client = razorpay.Client(
            auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
        )

        # Verify Webhook Signature
        client.utility.verify_webhook_signature(
            webhook_body,
            webhook_signature,
            webhook_secret
        )

        # Process the event
        event_data = json.loads(webhook_body)
        event_type = event_data.get('event')

        print(f"[RAZORPAY WEBHOOK] Received event: {event_type}")

        if event_type == 'payment.captured':
            payment_id = event_data['payload']['payment']['entity']['id']
            amount = event_data['payload']['payment']['entity']['amount']
            print(f"[RAZORPAY WEBHOOK] Payment Successful! ID: {payment_id}, Amount: {amount/100} INR")
            # Here you could update your database or send an automated Thank You email
            
        elif event_type == 'payment.failed':
            print(f"[RAZORPAY WEBHOOK] Payment Failed.")

        return Response({'status': 'ok'}, status=status.HTTP_200_OK)

    except razorpay.errors.SignatureVerificationError:
        print("[RAZORPAY WEBHOOK] Invalid Webhook Signature!")
        return Response({'status': 'invalid signature'}, status=400)
    except Exception as e:
        print(f"[RAZORPAY WEBHOOK] Error: {str(e)}")
        return Response({'status': 'error'}, status=500)
