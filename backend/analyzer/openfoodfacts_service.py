"""
Product Search Service — Database-Only Mode
============================================
All product lookups now query the local Supabase PostgreSQL database.
No external API calls are made during user searches.

Helper utilities (_is_known_indian_brand, _extract_nutriments, etc.) are
preserved here because they are used by:
  - analyzer/management/commands/import_products.py
  - analyzer/build_local_db.py
"""
import re
import time
from typing import Dict, Any, List, Optional
from django.db.models import Q, Case, When, IntegerField, Value
from .models import Product


# =====================================================
# Known Indian brands — used during import to tag
# is_indian=True on products.
# =====================================================
KNOWN_INDIAN_BRANDS = {
    # Snacks & Sweets
    "haldiram", "haldiram's", "bikano", "balaji", "bikanervala",
    "prataap snacks", "yellow diamond", "lays india", "kurkure",
    "uncle chipps", "garden", "chitale",
    # Dairy
    "amul", "mother dairy", "nandini", "verka", "milma",
    "parag milk", "gowardhan", "chitale dairy",
    # Biscuits & Bakery
    "britannia", "parle", "parle-g", "sunfeast", "priyagold",
    "anmol", "unibic", "karachi bakery", "monginis",
    # Spices & Masala
    "mdh", "everest", "catch", "badshah", "eastern",
    "aachi", "sakthi masala", "priya", "mothers recipe",
    # Ready-to-eat & Instant
    "mtr", "gits", "kohinoor", "kitchens of india",
    "ching's", "chings", "maiyas", "id fresh", "saffola",
    "maggi india", "yippee", "top ramen",
    # Beverages
    "paper boat", "frooti", "maaza", "appy fizz",
    "bisleri", "dabur", "real fruit", "tropicana india",
    "tata tea", "brooke bond", "wagh bakri", "society tea",
    "bru", "nescafe india", "leo coffee",
    # Health & Organic
    "patanjali", "organic tattva", "24 mantra",
    "pro nature", "conscious food", "truweight",
    "yoga bar", "ritebite", "open secret",
    # Cooking essentials
    "fortune", "dhara", "sundrop", "gemini",
    "tata sampann", "tata salt", "aashirvaad", "pillsbury india",
    "nature fresh",
    # Pickles & Condiments
    "mother's recipe", "bedekar",
    "kissan", "maggi sauce", "ching's sauce",
    "tops", "nilons", "smith & jones",
    # Sweets & Chocolate
    "cadbury india", "5 star", "dairy milk",
    "amul chocolate", "lotte india", "pulse candy",
    # Others
    "itc", "hindustan unilever", "nestle india",
    "godrej", "tata consumer", "marico",
    "emami", "wipro consumer",
}


def _is_known_indian_brand(brand_str: str) -> bool:
    """Check if a brand string matches any known Indian brand."""
    if not brand_str:
        return False
    brand_lower = brand_str.lower().strip()
    if brand_lower in KNOWN_INDIAN_BRANDS:
        return True
    for known in KNOWN_INDIAN_BRANDS:
        if known in brand_lower:
            return True
    return False


# ─── In-memory cache for DB search results ───────────────────────────────────
_search_cache: Dict[str, tuple] = {}
_CACHE_TTL = 1800   # 30 minutes
_CACHE_MAX_SIZE = 500


def _get_cached_search(cache_key: str) -> Optional[Dict]:
    if cache_key in _search_cache:
        timestamp, result = _search_cache[cache_key]
        if time.time() - timestamp < _CACHE_TTL:
            return result
        _search_cache.pop(cache_key, None)
    return None


def _set_search_cache(cache_key: str, result: Dict):
    if len(_search_cache) >= _CACHE_MAX_SIZE:
        oldest = min(_search_cache, key=lambda k: _search_cache[k][0])
        _search_cache.pop(oldest, None)
    _search_cache[cache_key] = (time.time(), result)


# ─── Text helpers (kept for import script & build_local_db) ──────────────────

def _is_english_text(text: str) -> bool:
    """Check if text is mostly Latin/ASCII (i.e., English)."""
    if not text:
        return False
    total = len(text)
    non_latin = sum(1 for c in text if ord(c) > 255)
    return (non_latin / total) <= 0.1


# ─── Nutriment extraction (kept for import script) ───────────────────────────

_NUTRIENT_MAP = [
    ("energy-kcal",         "Energy",               "kcal"),
    ("energy-kj",           "Energy",               "kJ"),
    ("proteins",            "Protein",              "g"),
    ("carbohydrates",       "Carbohydrates",        "g"),
    ("sugars",              "Total Sugars",         "g"),
    ("added-sugars",        "Added Sugars",         "g"),
    ("fat",                 "Total Fat",            "g"),
    ("saturated-fat",       "Saturated Fat",        "g"),
    ("trans-fat",           "Trans Fat",            "g"),
    ("monounsaturated-fat", "Monounsaturated Fat",  "g"),
    ("polyunsaturated-fat", "Polyunsaturated Fat",  "g"),
    ("cholesterol",         "Cholesterol",          "mg"),
    ("fiber",               "Dietary Fiber",        "g"),
    ("salt",                "Salt",                 "g"),
    ("sodium",              "Sodium",               "mg"),
    ("calcium",             "Calcium",              "mg"),
    ("iron",                "Iron",                 "mg"),
    ("potassium",           "Potassium",            "mg"),
    ("vitamin-a",           "Vitamin A",            "µg"),
    ("vitamin-c",           "Vitamin C",            "mg"),
    ("vitamin-d",           "Vitamin D",            "µg"),
]


def _is_liquid_product(product: dict) -> bool:
    for text in [product.get("quantity", ""), product.get("serving_size", "")]:
        if text and re.search(r'\d+\s*(ml|cl|l|fl\.?\s*oz)\b', text.lower()):
            return True
    raw_categories = (product.get("categories") or "").lower()
    category_items = [c.strip() for c in raw_categories.split(",")]
    liquid_cats = {
        "beverages", "drinks", "juices", "sodas", "waters",
        "soft drinks", "energy drinks", "fruit juices", "dairy drinks",
        "carbonated drinks", "iced teas", "smoothies",
    }
    return any(item in liquid_cats for item in category_items)


def _extract_nutriments(product: dict) -> Optional[Dict]:
    """
    Extract per-100g nutrition data from a product dict.
    'product' must have a 'nutriments' key with OpenFoodFacts-style raw data.
    Returns None if no data found.
    """
    raw = product.get("nutriments", {})
    if not raw:
        return None
    rows = []
    seen_labels = set()
    for off_key, label, unit in _NUTRIENT_MAP:
        val = raw.get(f"{off_key}_100g")
        if val is not None:
            if label in seen_labels:
                continue
            seen_labels.add(label)
            rows.append({"label": label, "value": round(val, 2), "unit": unit})
    if not rows:
        return None
    return {
        "rows": rows,
        "serving_size": product.get("serving_size", ""),
        "is_liquid": _is_liquid_product(product),
    }


def _is_quality_product(name: str, brand: str, ingredients_text: str = "") -> bool:
    if not name or len(name) < 3:
        return False
    if not _is_english_text(name):
        return False
    if re.match(r'^[0-9\-\s]+$', name):
        return False
    words = name.split()
    vowel_count = sum(1 for c in name.lower() if c in 'aeiou')
    if vowel_count < len(name.replace(' ', '')) * 0.15:
        return False
    if len(words) >= 4:
        short_words = sum(1 for w in words if len(w) <= 3)
        if short_words / len(words) > 0.7:
            return False
    if re.search(r'[bcdfghjklmnpqrstvwxyz]{6,}', name.lower()):
        return False
    test_re = re.compile(
        r'\b(test|sample|example|placeholder|todo|xxx|zzz|abc|asdf|qwerty|barcode)\b',
        re.IGNORECASE
    )
    if test_re.search(name) or test_re.search(brand):
        return False
    return True


def _normalize_product_name(name: str) -> str:
    n = name.lower().strip()
    n = re.sub(
        r'\b\d+(\.\d+)?\s*(g|gm|gms|gram|grams|kg|kgs|ml|l|ltr|litre|litres|liter|liters|oz|lb|lbs|cl)\b',
        '', n, flags=re.IGNORECASE
    )
    n = re.sub(r'[^a-z0-9\s]', '', n)
    n = re.sub(r'\s+', ' ', n).strip()
    return n


# =============================================================================
# DATABASE-ONLY SEARCH
# =============================================================================

def _product_to_dict(product) -> Dict:
    """Convert a Product ORM object to the API response format."""
    return {
        "barcode": product.barcode,
        "name": product.name,
        "brand": product.brand,
        "image_url": product.image_url,
        "image_url_thumbnail": product.image_url,
        "has_ingredients": bool(product.ingredients_text and len(product.ingredients_text) > 10),
        "ingredients_text": product.ingredients_text,
        "categories": product.categories,
        "nova_group": product.nova_group,
        "nutriscore_grade": product.nutriscore_grade,
        "nutriments": product.nutriments,
        "is_indian": product.is_indian,
        "is_verified": product.is_verified,
        "country": product.country,
        "_source": "db",
    }


def search_products(query: str, page: int = 1, page_size: int = 10, local_only: bool = False) -> Dict[str, Any]:
    """
    Search for products in the local Supabase database ONLY.
    No external API calls are ever made.

    Returns:
        {success, count, products, source}  — or not_in_db=True if nothing found.
    """
    if not query or not query.strip():
        return {"success": False, "error": "Empty search query"}

    cache_key = f"db|{query.strip().lower()}|{page}"
    cached = _get_cached_search(cache_key)
    if cached:
        return cached

    q = query.strip()

    # Build relevance-ordered queryset
    # Priority: exact name match > name starts with > name contains > brand contains
    qs = Product.objects.annotate(
        relevance=Case(
            When(name__iexact=q, then=Value(100)),
            When(name__istartswith=q, then=Value(80)),
            When(name__icontains=q, then=Value(60)),
            When(brand__icontains=q, then=Value(30)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).filter(
        Q(name__icontains=q) | Q(brand__icontains=q)
    ).order_by(
        '-is_verified',   # verified products first
        '-is_indian',     # Indian products next
        '-relevance',     # then by text relevance
        'name',
    )

    offset = (page - 1) * page_size
    products = list(qs[offset: offset + page_size])

    if not products:
        result = {
            "success": True,
            "count": 0,
            "products": [],
            "not_in_db": True,
            "message": "This product is not in our database yet.",
            "source": "db",
        }
        _set_search_cache(cache_key, result)
        return result

    result = {
        "success": True,
        "count": len(products),
        "products": [_product_to_dict(p) for p in products],
        "not_in_db": False,
        "source": "db",
    }
    _set_search_cache(cache_key, result)
    return result


def get_product_details(barcode: str) -> Dict[str, Any]:
    """
    Fetch full product details from the local database by barcode.
    No external API calls.
    """
    if not barcode or not barcode.strip():
        return {"success": False, "error": "No barcode provided"}

    try:
        product = Product.objects.get(barcode=barcode.strip())
    except Product.DoesNotExist:
        return {
            "success": False,
            "error": "PRODUCT_NOT_FOUND",
            "message": "This product is not in our database yet.",
            "not_in_db": True,
        }

    if not product.ingredients_text or len(product.ingredients_text) < 10:
        return {
            "success": False,
            "error": "NO_INGREDIENTS",
            "message": "Ingredient list is not available for this product. Try typing them manually.",
            "not_in_db": False,
        }

    return {
        "success": True,
        "product": {
            "barcode": product.barcode,
            "name": product.name,
            "brand": product.brand,
            "image_url": product.image_url,
            "categories": product.categories,
            "quantity": product.quantity,
            "nova_group": product.nova_group,
            "nutriscore_grade": product.nutriscore_grade,
            "nutriments": product.nutriments,
            "is_verified": product.is_verified,
            "country": product.country,
        },
        "ingredients_text": product.ingredients_text,
        "_source": "db",
    }


# =============================================================================
# HEALTHIER ALTERNATIVES — DB-based
# =============================================================================

NUTRISCORE_ORDER: List[str] = ['a', 'b', 'c', 'd', 'e']


def find_healthier_alternatives(
    category: str,
    current_nutriscore: str = '',
    current_product_name: str = '',
    limit: int = 4,
) -> Dict[str, Any]:
    """
    Find healthier alternatives in the same category from the database.
    Returns products with a better Nutri-Score in the same category.
    """
    if not category:
        return {"success": False, "error": "No category provided", "alternatives": []}

    cache_key = f"alt_db|{category.lower().strip()}|{current_nutriscore}"
    cached = _get_cached_search(cache_key)
    if cached:
        return cached

    current_grade = (current_nutriscore or 'e').lower().strip()
    if current_grade not in NUTRISCORE_ORDER:
        current_grade = 'e'

    current_idx = NUTRISCORE_ORDER.index(current_grade)
    if current_idx == 0:
        result = {"success": True, "alternatives": [], "message": "Already the best Nutri-Score!"}
        _set_search_cache(cache_key, result)
        return result

    # Slice to get better grades, using cast to int to ensure correct indexing
    # Get all grades better than the current one
    better_grades: List[str] = NUTRISCORE_ORDER[0:current_idx]

    # Search by category keyword, filter to better grades
    primary_category = category.split(',')[-1].strip()
    qs = Product.objects.filter(
        categories__icontains=primary_category,
        nutriscore_grade__in=better_grades,
    ).order_by('-is_verified', '-is_indian', 'nutriscore_grade')

    if current_product_name:
        qs = qs.exclude(name__iexact=current_product_name)

    alternatives = []
    for p in qs[:limit * 3]:  # fetch extra to allow duplicates filtering
        if len(alternatives) >= limit:
            break
        alternatives.append({
            "barcode": p.barcode,
            "name": p.name,
            "brand": p.brand,
            "image_url": p.image_url,
            "nutriscore_grade": p.nutriscore_grade,
            "nova_group": p.nova_group,
            "has_ingredients": bool(p.ingredients_text),
            "ingredients_text": "",
            "is_indian": p.is_indian,
            "_source": "db",
        })

    result = {
        "success": True,
        "count": len(alternatives),
        "alternatives": alternatives,
        "searched_category": primary_category,
        "_source": "db",
    }
    _set_search_cache(cache_key, result)
    return result
