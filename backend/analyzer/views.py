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
        # Log analysis attempt (for audit trail)
        print(f"[SECURITY] Analyzing text (length: {len(sanitized_text)}, lines: {line_count})")
        
        # Analyze ingredients
        # Text-only implies no specific macros are available yet
        analysis_result = analyze_product_from_text(
            text=sanitized_text.strip(),
            macros={}, 
            food_type=food_type, 
            user_goal=user_goal
        )
        
        # If analysis failed
        if not analysis_result.get('success', True):
            return Response(analysis_result, status=status.HTTP_200_OK)
        
        # Add metadata about manual entry
        analysis_result['input_method'] = 'manual'
        analysis_result['raw_ingredients_text'] = sanitized_text.strip()

        # Save to authenticated users' analysis history (SaaS feature).
        if request.user and request.user.is_authenticated:
            try:
                product_data = analysis_result.get("product", {}) or {}
                analysis_for_storage = dict(analysis_result)
                # Avoid storing the full ingredient text in the JSON history.
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
        
        # Send email via Resend HTTP API (synchronously)
        # Render blocks SMTP ports AND kills background threads
        import requests as http_requests
        
        try:
            resend_api_key = os.environ.get('RESEND_API_KEY', '')
            to_email = os.environ.get('CONTACT_EMAIL_RECIPIENT', 'se.jaimin91@gmail.com')
            
            print(f"[EMAIL] Starting Resend send to {to_email}, key present: {bool(resend_api_key)}", flush=True)
            
            if not resend_api_key:
                print("[EMAIL] Skipping - RESEND_API_KEY not set", flush=True)
            else:
                email_response = http_requests.post(
                    'https://api.resend.com/emails',
                    headers={
                        'Authorization': f'Bearer {resend_api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'from': 'Ingrexa Contact <onboarding@resend.dev>',
                        'to': [to_email],
                        'subject': f"New Contact Message from {sanitized_data['name']}",
                        'text': f"New contact message from Ingrexa:\n\nFrom: {sanitized_data['name']}\nEmail: {sanitized_data['email']}\n\nMessage:\n{sanitized_data['message']}\n\n---\nSent from Ingrexa Contact Form"
                    },
                    timeout=10
                )
                
                print(f"[EMAIL] Resend response: {email_response.status_code} - {email_response.text}", flush=True)
        except Exception as e:
            print(f"[EMAIL ERROR] {type(e).__name__}: {str(e)}", flush=True)
        
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
    
    # User might define it, otherwise OpenFoodFacts tags determines it
    food_type = request.data.get('food_type', 'Solid')
    
    if not barcode and not supplied_ingredients:
        return Response(
            {'success': False, 'error': 'NO_BARCODE', 'message': 'Please provide a product barcode.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        product_info = None
        ingredients_text = supplied_ingredients
        
        # If we have a barcode and no pre-supplied ingredients, fetch from OFF
        if barcode and not ingredients_text:
            print(f"[PRODUCT] Fetching product details for barcode: {barcode}")
            product_result = off_get_product(barcode)
            
            if not product_result.get('success'):
                return Response(product_result, status=status.HTTP_200_OK)
            
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
        
        # Extract macros if available from OpenFoodFacts
        macros = product_info.get('nutriments', {}) if product_info else {}
        
        analysis_result = analyze_product_from_text(
            text=ingredients_text,
            macros=macros,
            food_type=food_type,
            user_goal=user_goal
        )
        
        # Enrich with product metadata from OpenFoodFacts
        analysis_result['input_method'] = 'openfoodfacts'
        analysis_result['raw_ingredients_text'] = ingredients_text
        
        if product_info:
            analysis_result['product_info'] = product_info
            # Override generic product name with real one
            if 'product' in analysis_result:
                analysis_result['product']['name'] = product_info.get('name', analysis_result['product'].get('name', 'Unknown'))
                analysis_result['product']['brand'] = product_info.get('brand', 'Unknown')

        # Save to authenticated users' analysis history (SaaS feature).
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
