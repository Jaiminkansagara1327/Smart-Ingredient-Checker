"""
OpenFoodFacts API integration service
Searches for food products globally and retrieves ingredient lists.
Indian products are prioritized and Indian brands are correctly identified.
"""
import re
import json
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from typing import Dict, Any, List, Optional
from functools import lru_cache


# OpenFoodFacts API base URLs
SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product"

# User agent as required by OpenFoodFacts API guidelines
HEADERS = {
    "User-Agent": "Ingrexa/1.0 (https://ingrexa.com; contact@ingrexa.com)"
}

# Persistent HTTP session with automatic retries
# Handles stale connections and intermittent network issues
_retry_strategy = Retry(
    total=2,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"],
)
_adapter = HTTPAdapter(max_retries=_retry_strategy, pool_maxsize=5)
_session = requests.Session()
_session.headers.update(HEADERS)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)

# =====================================================
# Known Indian brands — used to correctly identify
# Indian products even when sold/scanned abroad.
# OpenFoodFacts tags products by "sold in" country,
# not brand origin, so Haldiram sold in USA shows as USA.
# This list fixes that.
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
    "nature fresh", "saffola",
    # Pickles & Condiments
    "mother's recipe", "priya", "bedekar",
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
    # Check exact match
    if brand_lower in KNOWN_INDIAN_BRANDS:
        return True
    # Check if any known brand is a substring (e.g. "Haldiram's Snacks Pvt Ltd" contains "haldiram")
    for known in KNOWN_INDIAN_BRANDS:
        if known in brand_lower:
            return True
    return False


# --- SEARCH RESULT CACHE ---
# Cache search results in-memory to avoid hitting OpenFoodFacts on every keystroke.
# Key: "query|page", Value: (timestamp, result_dict)
# Entries expire after 10 minutes.
_search_cache: Dict[str, tuple] = {}
_CACHE_TTL = 1800  # 30 minutes — longer cache for faster repeat searches
_CACHE_MAX_SIZE = 500  # Max cached queries


def _get_cached_search(cache_key: str) -> Optional[Dict]:
    """Return cached search result if fresh, else None."""
    if cache_key in _search_cache:
        timestamp, result = _search_cache[cache_key]
        if time.time() - timestamp < _CACHE_TTL:
            return result
        else:
            del _search_cache[cache_key]
    return None


def _set_search_cache(cache_key: str, result: Dict):
    """Store a search result in cache. Evicts oldest if full."""
    if len(_search_cache) >= _CACHE_MAX_SIZE:
        # Evict oldest entry
        oldest_key = min(_search_cache, key=lambda k: _search_cache[k][0])
        del _search_cache[oldest_key]
    _search_cache[cache_key] = (time.time(), result)


# =====================================================
# LOCAL PRODUCT DATABASE — instant search results
# Pre-built JSON file with popular products.
# Loaded once at startup, searched in-memory (<1ms).
# =====================================================
_LOCAL_DB_PATH = os.path.join(os.path.dirname(__file__), "local_products.json")
_local_products: List[Dict] = []

def _load_local_db():
    """Load pre-built local product database on startup."""
    global _local_products
    if not os.path.exists(_LOCAL_DB_PATH):
        print("[LOCAL DB] No local_products.json found — skipping local search")
        return
    try:
        with open(_LOCAL_DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)
        _local_products = db.get("products", [])
        print(f"[LOCAL DB] Loaded {len(_local_products)} products from local database")
    except Exception as e:
        print(f"[LOCAL DB] Failed to load: {e}")
        _local_products = []

# Load on module import
_load_local_db()


def _search_local_db(query: str, limit: int = 10) -> List[Dict]:
    """
    Search the local product database. Uses simple case-insensitive matching.
    Returns products sorted by relevance (exact name match > brand match > partial).
    Instant — no network calls.
    """
    if not _local_products or not query:
        return []
    
    q = query.lower().strip()
    q_words = q.split()
    results = []
    
    for product in _local_products:
        name_lower = product.get("name", "").lower()
        brand_lower = product.get("brand", "").lower()
        combined = f"{name_lower} {brand_lower}"
        
        # Score: higher = better match
        score = 0
        
        # Exact name match
        if q == name_lower:
            score = 100
        # Name starts with query
        elif name_lower.startswith(q):
            score = 80
        # All query words appear in name+brand
        elif all(w in combined for w in q_words):
            score = 60
        # Any query word in name
        elif any(w in name_lower for w in q_words):
            score = 40
        # Any query word in brand
        elif any(w in brand_lower for w in q_words):
            score = 20
        else:
            continue
        
        results.append((score, product))
    
    # Sort by score (descending)
    results.sort(key=lambda x: -x[0])
    return [r[1] for r in results[:limit]]


def _format_local_product(product: Dict) -> Dict:
    """Convert a local DB product to the same format as API search results."""
    # Detect country
    countries_tags = product.get("countries_tags", [])
    tagged_as_india = any("india" in tag.lower() for tag in countries_tags)
    brand_is_indian = _is_known_indian_brand(product.get("brand", ""))
    is_indian = tagged_as_india or brand_is_indian
    
    if is_indian:
        country = "India"
    elif any("united-states" in t.lower() or "usa" in t.lower() for t in countries_tags):
        country = "USA"
    elif any("united-kingdom" in t.lower() for t in countries_tags):
        country = "UK"
    elif countries_tags:
        country = countries_tags[0].split(":")[-1].replace("-", " ").title()
    else:
        country = ""
    
    # Build nutriments from raw data
    nutriments = None
    if product.get("nutriments_raw"):
        # Build a fake product dict for _extract_nutriments
        fake_product = {
            "nutriments": product["nutriments_raw"],
            "serving_size": product.get("serving_size", ""),
            "quantity": product.get("quantity", ""),
            "categories": product.get("categories", ""),
        }
        nutriments = _extract_nutriments(fake_product)
    
    return {
        "barcode": product.get("barcode", ""),
        "name": product.get("name", ""),
        "brand": product.get("brand", "Unknown"),
        "image_url": product.get("image_url", ""),
        "has_ingredients": bool(product.get("ingredients_text")),
        "ingredients_text": product.get("ingredients_text", ""),
        "categories": product.get("categories", ""),
        "nova_group": product.get("nova_group"),
        "nutriscore_grade": product.get("nutriscore_grade"),
        "nutriments": nutriments,
        "is_indian": is_indian,
        "country": country,
        "_source": "local",
    }


def search_products(query: str, page: int = 1, page_size: int = 10, local_only: bool = False) -> Dict[str, Any]:
    """
    Search for products. Checks local DB first for instant results,
    then falls back to OpenFoodFacts API.
    
    Args:
        query: Search term (product name like "Maggi", "Nutella", "Oreo", etc.)
        page: Page number for pagination
        page_size: Number of results per page
    
    Returns:
        Dictionary with success status and list of products
    """
    if not query or not query.strip():
        return {"success": False, "error": "Empty search query"}
    
    # Check in-memory cache first
    cache_key = f"{query.strip().lower()}|{page}|{local_only}"
    cached = _get_cached_search(cache_key)
    if cached:
        print(f"[OFF] Cache hit for '{query}' (page {page})")
        return cached
    
    # --- STEP 1: Search local database (instant) ---
    local_results = []
    if page == 1:  # Only use local DB for page 1
        local_matches = _search_local_db(query, limit=page_size)
        local_results = [_format_local_product(p) for p in local_matches]
        if local_results:
            print(f"[LOCAL DB] Found {len(local_results)} local results for '{query}'")
    
    # If we have ANY local results, return them immediately
    # and skip the slow API call to keep search feeling "instant"
    if len(local_results) > 0:
        local_results.sort(key=lambda p: (0 if p.get("is_indian") else 1))
        result = {
            "success": True,
            "count": len(local_results),
            "products": local_results[:page_size],
            "source": "local",
        }
        _set_search_cache(cache_key, result)
        return result
    
    # --- STEP 2: Search OpenFoodFacts API (slow fallback) ---
    # Only fallback to OpenFoodFacts for longer, more specific queries 
    # to avoid 3-5 second delays on autocomplete keystrokes (like typing 2-3 chars)
    if local_only or (len(query.strip()) < 4 and page == 1):
        if local_only:
            print(f"[SEARCH] local_only=True requested, skipping slow OFF API fallback for: '{query}'")
        else:
            print(f"[SEARCH] Skipping slow OFF API fallback for short autocomplete query: '{query}'")
            
        return {
            "success": True,
            "count": 0,
            "products": [],
            "source": "local",
        }
    
    print(f"[SEARCH] Searching OpenFoodFacts for: '{query}' (page {page})")
    try:
        params = {
            "search_terms": query.strip(),
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page": page,
            "page_size": 20,
            "fields": "code,product_name,brands,image_front_small_url,categories,nova_group,nutriscore_grade,countries_tags,ingredients_text,ingredients_text_en,nutriments,serving_size,quantity",
        }
        
        response = _session.get(SEARCH_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Parse results
        api_products = _parse_search_results(data, require_ingredients=False)
        
        # Merge: local results first, then API results (deduplicate by barcode)
        seen_barcodes = {p["barcode"] for p in local_results if p.get("barcode")}
        merged = list(local_results)
        for p in api_products:
            if p.get("barcode") and p["barcode"] not in seen_barcodes:
                merged.append(p)
                seen_barcodes.add(p["barcode"])
        
        # Sort: Indian products first
        merged.sort(key=lambda p: (0 if p.get("is_indian") else 1))
        merged = merged[:page_size]
        
        result = {
            "success": True,
            "count": len(merged),
            "products": merged,
        }
        
        _set_search_cache(cache_key, result)
        return result
    
    except requests.Timeout:
        # If API times out but we have local results, return those
        if local_results:
            print(f"[SEARCH] API timeout, returning {len(local_results)} local results")
            result = {
                "success": True,
                "count": len(local_results),
                "products": local_results[:page_size],
                "source": "local_fallback",
            }
            return result
        return {
            "success": False,
            "error": "SEARCH_TIMEOUT",
            "message": "Search timed out. Please try again.",
        }
    except requests.RequestException as e:
        print(f"[OFF] Search error: {type(e).__name__}: {e}")
        # If API fails but we have local results, return those
        if local_results:
            print(f"[SEARCH] API error, returning {len(local_results)} local results")
            return {
                "success": True,
                "count": len(local_results),
                "products": local_results[:page_size],
                "source": "local_fallback",
            }
        return {
            "success": False,
            "error": "SEARCH_FAILED",
            "message": "Could not search products. Please try again later.",
        }


def _is_english_text(text: str) -> bool:
    """Check if a text string appears to be in English (mostly ASCII)."""
    if not text:
        return False
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    return ascii_chars / max(len(text), 1) >= 0.85


def _get_english_ingredients(item: dict) -> str:
    """
    Extract the best English ingredients text from an OpenFoodFacts item.
    Prefers ingredients_text_en, falls back to generic only if it looks English.
    """
    # Prefer the explicit English field
    en_text = (item.get("ingredients_text_en") or "").strip()
    generic_text = (item.get("ingredients_text") or "").strip()
    
    if en_text and _is_english_text(en_text):
        return en_text
    
    if generic_text and _is_english_text(generic_text):
        return generic_text
    
    # Both are non-English
    return ""


# --- Nutriment Extraction ---
# Ordered mapping: (OpenFoodFacts key suffix, display label, unit)
_NUTRIENT_MAP = [
    ("energy-kcal",    "Energy",             "kcal"),
    ("energy-kj",      "Energy",             "kJ"),
    ("proteins",       "Protein",            "g"),
    ("carbohydrates",  "Carbohydrates",      "g"),
    ("sugars",         "Total Sugars",       "g"),
    ("added-sugars",   "Added Sugars",       "g"),
    ("fat",            "Total Fat",          "g"),
    ("saturated-fat",  "Saturated Fat",      "g"),
    ("trans-fat",      "Trans Fat",          "g"),
    ("monounsaturated-fat", "Monounsaturated Fat", "g"),
    ("polyunsaturated-fat", "Polyunsaturated Fat", "g"),
    ("cholesterol",    "Cholesterol",        "mg"),
    ("fiber",          "Dietary Fiber",      "g"),
    ("salt",           "Salt",               "g"),
    ("sodium",         "Sodium",             "mg"),
    ("calcium",        "Calcium",            "mg"),
    ("iron",           "Iron",               "mg"),
    ("potassium",      "Potassium",          "mg"),
    ("vitamin-a",      "Vitamin A",          "µg"),
    ("vitamin-c",      "Vitamin C",          "mg"),
    ("vitamin-d",      "Vitamin D",          "µg"),
]


def _extract_nutriments(product: dict) -> Optional[Dict]:
    """
    Extract per-100g nutrition data from an OpenFoodFacts product.
    Only includes nutrients that have actual values — dynamic, not hardcoded.
    Returns None if no nutritional data exists.
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


def _is_liquid_product(product: dict) -> bool:
    """Detect if a product is a liquid based on quantity, serving_size, or categories."""
    indicators = [
        product.get("quantity", ""),
        product.get("serving_size", ""),
    ]
    for text in indicators:
        if text and re.search(r'\d+\s*(ml|cl|l|fl\.?\s*oz)\b', text.lower()):
            return True
    
    # Check categories — split into individual items for exact matching
    raw_categories = (product.get("categories") or "").lower()
    category_items = [c.strip() for c in raw_categories.split(",")]
    liquid_cats = {
        "beverages", "drinks", "juices", "sodas", "waters",
        "soft drinks", "energy drinks", "fruit juices", "dairy drinks",
        "carbonated drinks", "iced teas", "smoothies",
    }
    for item in category_items:
        if item in liquid_cats:
            return True
    
    return False


def _is_quality_product(name: str, brand: str, ingredients_text: str = "") -> bool:
    """
    Check if a product entry looks like a real, quality entry in English.
    Filters out junk/spam/test entries and non-English products from OpenFoodFacts.
    
    Returns True if the product looks legitimate and is in English.
    """
    
    
    # Reject very short names
    if len(name) < 3:
        return False
    
    # ---- ENGLISH LANGUAGE CHECK ----
    # Reject names with non-Latin characters (Chinese, Arabic, Korean, Cyrillic, Thai, etc.)
    if not _is_english_text(name):
        return False
    
    # Reject names that are all uppercase gibberish (e.g. "SDHK GRN SLD")
    words = name.split()
    
    # If the name has too many very short words (abbreviation soup), it's junk
    if len(words) >= 4:
        short_words = sum(1 for w in words if len(w) <= 3)
        if short_words / len(words) > 0.6:
            return False
    
    # Reject names with excessive consonant clusters (no real word has 5+ consonants in a row)
    consonant_cluster = re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', name.lower())
    if consonant_cluster:
        return False
    
    # Reject entries where brand is Unknown AND name looks like gibberish
    if brand.lower() in ("unknown", ""):
        vowel_count = sum(1 for c in name.lower() if c in 'aeiou')
        if vowel_count < len(name) * 0.15:
            return False
    
    # Reject test/placeholder entries
    test_patterns = re.compile(
        r'\b(test|sample|example|placeholder|todo|xxx|zzz|abc|asdf|qwerty)\b',
        re.IGNORECASE
    )
    if test_patterns.search(name):
        return False
    
    return True


def get_product_details(barcode: str) -> Dict[str, Any]:
    """
    Fetch full product details from OpenFoodFacts by barcode.
    
    Args:
        barcode: Product barcode (EAN/UPC)
    
    Returns:
        Dictionary with product info and ingredient text
    """
    if not barcode or not barcode.strip():
        return {"success": False, "error": "No barcode provided"}
    
    try:
        url = f"{PRODUCT_URL}/{barcode.strip()}"
        params = {
            "fields": "code,product_name,brands,image_front_small_url,image_front_url,ingredients_text,ingredients_text_en,categories,nova_group,nutriscore_grade,countries_tags,quantity,nutriments,serving_size"
        }
        
        response = _session.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != 1:
            return {
                "success": False,
                "error": "PRODUCT_NOT_FOUND",
                "message": "Product not found in the database.",
            }
        
        product = data.get("product", {})
        
        # Extract English ingredients — prefer explicit English field
        ingredients_text = _get_english_ingredients(product)
        
        if not ingredients_text:
            return {
                "success": False,
                "error": "NO_INGREDIENTS",
                "message": "English ingredient list is not available for this product. Try typing the ingredients manually.",
            }
        
        nutriments = _extract_nutriments(product)
        
        return {
            "success": True,
            "product": {
                "barcode": product.get("code", barcode),
                "name": product.get("product_name", "Unknown Product"),
                "brand": product.get("brands", "Unknown Brand"),
                "image_url": product.get("image_front_small_url", ""),
                "categories": product.get("categories", ""),
                "quantity": product.get("quantity", ""),
                "nova_group": product.get("nova_group"),
                "nutriscore_grade": product.get("nutriscore_grade"),
                "nutriments": nutriments,
            },
            "ingredients_text": ingredients_text,
        }
    
    except requests.Timeout:
        print(f"[OFF] Product fetch TIMEOUT for barcode: {barcode}")
        return {
            "success": False,
            "error": "FETCH_TIMEOUT",
            "message": "Product data is taking too long to load. Please try again.",
        }
    except requests.RequestException as e:
        print(f"[OFF] Product fetch error for barcode {barcode}: {type(e).__name__}: {e}")
        return {
            "success": False,
            "error": "FETCH_FAILED",
            "message": "Could not fetch product details. Please try again later.",
        }


def _normalize_product_name(name: str) -> str:
    """
    Aggressively normalize a product name for deduplication.
    Catches: spelling variants, quantity suffixes, punctuation differences, case.
    
    Examples:
        "Amul Pasteurized Butter"  -> "amul pasteurized butter"
        "Amul Pasteurised Butter"  -> "amul pasteurised butter"  (caught by fuzzy match)
        "Parle-G Biscuits 200g"   -> "parle g biscuits"
        "PARLE - G"               -> "parle g"
    """
    n = name.lower().strip()
    # Remove quantity/weight suffixes: 500g, 1kg, 200ml, 1.5L, 100 g, etc.
    n = re.sub(r'\b\d+(\.\d+)?\s*(g|gm|gms|gram|grams|kg|kgs|ml|l|ltr|litre|litres|liter|liters|oz|lb|lbs|cl)\b', '', n, flags=re.IGNORECASE)
    # Remove all non-alphanumeric characters (hyphens, commas, dots, etc.)
    n = re.sub(r'[^a-z0-9\s]', '', n)
    # Collapse multiple spaces
    n = re.sub(r'\s+', ' ', n).strip()
    return n


def _is_duplicate(new_name: str, existing_names: list) -> int:
    """
    Check if new_name is a duplicate of any existing product using fuzzy matching.
    Returns the index of the duplicate in existing_names, or -1 if not a duplicate.
    
    Uses SequenceMatcher for similarity — threshold is 0.80 (80% similar = duplicate).
    """
    from difflib import SequenceMatcher
    
    for idx, existing in enumerate(existing_names):
        # Exact match
        if new_name == existing:
            return idx
        # Fuzzy match — 80% similarity catches spelling variants
        ratio = SequenceMatcher(None, new_name, existing).ratio()
        if ratio >= 0.80:
            return idx
    
    return -1


def _parse_search_results(data: dict, require_ingredients: bool = True) -> List[Dict[str, Any]]:
    """Parse OpenFoodFacts search response into clean product list.
    Only includes products that have English ingredient data.
    Deduplicates using fuzzy name matching (80% similarity threshold).
    Tags each product with country info for sorting (Indian products first).
    """
    products = []
    normalized_names = []  # parallel list of normalized names for fuzzy matching
    
    for item in data.get("products", []):
        product_name = (item.get("product_name") or "").strip()
        brand = (item.get("brands") or "Unknown").strip()
        
        # Skip products without a name
        if not product_name:
            continue
        
        # Get English ingredients only (if present)
        ingredients_text = _get_english_ingredients(item)
        if require_ingredients and not ingredients_text:
            continue
        
        # Skip junk/spam/test products (lenient check if ingredients missing)
        if not _is_quality_product(product_name, brand, ingredients_text):
            continue
        
        # --- FUZZY DEDUPLICATION ---
        norm_name = _normalize_product_name(product_name)
        if not norm_name:
            continue
        
        dup_idx = _is_duplicate(norm_name, normalized_names)
        
        if dup_idx >= 0:
            # This is a duplicate — keep the better entry
            existing = products[dup_idx]
            existing_len = len(existing.get("ingredients_text", ""))
            new_is_better = (
                len(ingredients_text) > existing_len
                or (not existing.get("image_url") and item.get("image_front_small_url"))
            )
            if new_is_better:
                products[dup_idx]["ingredients_text"] = ingredients_text
                products[dup_idx]["barcode"] = item.get("code", "")
                if item.get("image_front_small_url"):
                    products[dup_idx]["image_url"] = item["image_front_small_url"]
                if brand and brand != "Unknown":
                    products[dup_idx]["brand"] = brand
            continue
        
        # --- NEW UNIQUE PRODUCT ---
        # Detect if this is an Indian product
        countries_tags = item.get("countries_tags") or []
        tagged_as_india = any("india" in tag.lower() for tag in countries_tags)
        brand_is_indian = _is_known_indian_brand(brand) or _is_known_indian_brand(product_name)
        is_indian = tagged_as_india or brand_is_indian
        
        # Determine country label
        if is_indian:
            country = "India"
        elif any("united-states" in tag.lower() or "usa" in tag.lower() for tag in countries_tags):
            country = "USA"
        elif any("united-kingdom" in tag.lower() for tag in countries_tags):
            country = "UK"
        elif any("france" in tag.lower() for tag in countries_tags):
            country = "France"
        elif any("germany" in tag.lower() for tag in countries_tags):
            country = "Germany"
        elif countries_tags:
            raw = countries_tags[0].split(":")[-1].replace("-", " ").title()
            country = raw
        else:
            country = ""
        
        products.append({
            "barcode": item.get("code", ""),
            "name": product_name,
            "brand": brand,
            "image_url": item.get("image_front_small_url", ""),
            "has_ingredients": True,
            "ingredients_text": ingredients_text,
            "categories": (item.get("categories") or "").strip(),
            "nova_group": item.get("nova_group"),
            "nutriscore_grade": item.get("nutriscore_grade"),
            "nutriments": _extract_nutriments(item),
            "is_indian": is_indian,
            "country": country,
        })
        normalized_names.append(norm_name)
    
    return products


# =====================================================
# HEALTHIER ALTERNATIVES
# =====================================================
NUTRISCORE_ORDER = ['a', 'b', 'c', 'd', 'e']


def find_healthier_alternatives(
    category: str,
    current_nutriscore: str = '',
    current_product_name: str = '',
    limit: int = 4
) -> Dict[str, Any]:
    """
    Find healthier alternatives in the same category.
    Searches OpenFoodFacts for products with a better Nutri-Score.
    """
    if not category:
        return {"success": False, "error": "No category provided", "alternatives": []}
    
    # Check cache
    cache_key = f"alt|{category.lower().strip()}|{current_nutriscore}"
    cached = _get_cached_search(cache_key)
    if cached:
        print(f"[OFF] Alternatives cache hit for '{category}'")
        return cached
    
    # Use the last category tag (most specific in OpenFoodFacts)
    primary_category = category.split(',')[-1].strip()
    
    # Determine what nutriscore grades are "better"
    current_grade = current_nutriscore.lower().strip() if current_nutriscore else 'e'
    if current_grade not in NUTRISCORE_ORDER:
        current_grade = 'e'
    
    current_idx = NUTRISCORE_ORDER.index(current_grade)
    if current_idx == 0:
        result = {"success": True, "alternatives": [], "message": "Already the best Nutri-Score!"}
        _set_search_cache(cache_key, result)
        return result
    
    try:
        # First attempt: Search for Indian products in this category
        params_india = {
            "tagtype_0": "categories",
            "tag_contains_0": "contains",
            "tag_0": primary_category,
            "tagtype_1": "countries",
            "tag_contains_1": "contains",
            "tag_1": "India",
            "action": "process",
            "json": 1,
            "page": 1,
            "page_size": 15,
            "sort_by": "nutriscore_score",
            "fields": "code,product_name,brands,image_front_small_url,nutriscore_grade,nova_group,categories,countries_tags",
        }
        
        response = _session.get(SEARCH_URL, params=params_india, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        products_to_process = data.get("products", [])
        
        # Fallback: If not enough Indian products, do a broader global search
        if len(products_to_process) < 4:
            params_global = {
                "tagtype_0": "categories",
                "tag_contains_0": "contains",
                "tag_0": primary_category,
                "action": "process",
                "json": 1,
                "page": 1,
                "page_size": 15,
                "sort_by": "nutriscore_score",
                "fields": "code,product_name,brands,image_front_small_url,nutriscore_grade,nova_group,categories,countries_tags",
            }
            res_global = _session.get(SEARCH_URL, params=params_global, timeout=15)
            res_global.raise_for_status()
            products_to_process.extend(res_global.json().get("products", []))
        alternatives = []
        seen_names = set()
        current_name_lower = current_product_name.lower().strip() if current_product_name else ''
        
        for item in products_to_process:
            product_name = (item.get("product_name") or "").strip()
            brand = (item.get("brands") or "Unknown").strip()
            grade = (item.get("nutriscore_grade") or "").lower()
            
            if not product_name or not grade:
                continue
            if current_name_lower and product_name.lower().strip() == current_name_lower:
                continue
            if grade not in NUTRISCORE_ORDER:
                continue
            if NUTRISCORE_ORDER.index(grade) >= current_idx:
                continue
            if not _is_english_text(product_name):
                continue
            
            norm = _normalize_product_name(product_name)
            if norm in seen_names:
                continue
            seen_names.add(norm)
            
            countries_tags = item.get("countries_tags") or []
            is_indian = any("india" in t.lower() for t in countries_tags) or _is_known_indian_brand(brand)
            
            alternatives.append({
                "barcode": item.get("code", ""),
                "name": product_name,
                "brand": brand,
                "image_url": item.get("image_front_small_url", ""),
                "nutriscore_grade": grade,
                "nova_group": item.get("nova_group"),
                "has_ingredients": True,  # Assume present for display purposes
                "ingredients_text": "",   # Don't need text for suggestion card
                "is_indian": is_indian,
            })
            
            if len(alternatives) >= limit:
                break
        
        alternatives.sort(key=lambda p: (
            0 if p.get("is_indian") else 1,
            NUTRISCORE_ORDER.index(p.get("nutriscore_grade", "e"))
        ))
        
        result = {
            "success": True,
            "count": len(alternatives),
            "alternatives": alternatives,
            "searched_category": primary_category,
        }
        _set_search_cache(cache_key, result)
        return result
    
    except requests.Timeout:
        return {"success": False, "error": "TIMEOUT", "alternatives": []}
    except requests.RequestException as e:
        print(f"[OFF] Alternatives error: {type(e).__name__}: {e}")
        return {"success": False, "error": str(e), "alternatives": []}
