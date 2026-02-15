"""
OpenFoodFacts API integration service
Searches for food products globally and retrieves ingredient lists.
Indian products are prioritized and Indian brands are correctly identified.
"""
import re
import requests
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
_CACHE_TTL = 600  # 10 minutes in seconds
_CACHE_MAX_SIZE = 200  # Max cached queries


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


def search_products(query: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """
    Search OpenFoodFacts for products matching the query.
    Results are cached in-memory for 10 minutes for instant repeat lookups.
    
    Args:
        query: Search term (product name like "Maggi", "Nutella", "Oreo", etc.)
        page: Page number for pagination
        page_size: Number of results per page
    
    Returns:
        Dictionary with success status and list of products
    """
    if not query or not query.strip():
        return {"success": False, "error": "Empty search query"}
    
    # Check cache first
    cache_key = f"{query.strip().lower()}|{page}"
    cached = _get_cached_search(cache_key)
    if cached:
        print(f"[OFF] Cache hit for '{query}' (page {page})")
        return cached
    
    try:
        # Search the GLOBAL database (no country filter)
        params = {
            "search_terms": query.strip(),
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page": page,
            "page_size": 50,  # Fetch more — many will be filtered as junk
            "fields": "code,product_name,brands,image_front_small_url,ingredients_text,ingredients_text_en,categories,nova_group,nutriscore_grade,countries_tags",
        }
        
        response = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=7)
        response.raise_for_status()
        data = response.json()
        
        products = _parse_search_results(data)
        
        # Sort: Indian products first, then the rest
        products.sort(key=lambda p: (0 if p.get("is_indian") else 1))
        
        # Limit to a reasonable number
        products = products[:page_size]
        
        result = {
            "success": True,
            "count": len(products),
            "products": products,
        }
        
        # Cache the result for future lookups
        _set_search_cache(cache_key, result)
        
        return result
    
    except requests.Timeout:
        return {
            "success": False,
            "error": "SEARCH_TIMEOUT",
            "message": "OpenFoodFacts search timed out. Please try again.",
        }
    except requests.RequestException as e:
        print(f"[OFF] Search error: {type(e).__name__}: {e}")
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
            "fields": "code,product_name,brands,image_front_small_url,image_front_url,ingredients_text,ingredients_text_en,categories,nova_group,nutriscore_grade,countries_tags,quantity"
        }
        
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
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
            },
            "ingredients_text": ingredients_text,
        }
    
    except requests.Timeout:
        return {
            "success": False,
            "error": "FETCH_TIMEOUT",
            "message": "Could not fetch product details. Please try again.",
        }
    except requests.RequestException as e:
        print(f"[OFF] Product fetch error: {type(e).__name__}: {e}")
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


def _parse_search_results(data: dict) -> List[Dict[str, Any]]:
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
        
        # Get English ingredients only
        ingredients_text = _get_english_ingredients(item)
        if not ingredients_text:
            continue
        
        # Skip junk/spam/test products
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
            "is_indian": is_indian,
            "country": country,
        })
        normalized_names.append(norm_name)
    
    return products
