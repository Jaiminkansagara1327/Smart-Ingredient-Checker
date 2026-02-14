"""
OpenFoodFacts API integration service
Searches for food products globally and retrieves ingredient lists.
Indian products are prioritized and Indian brands are correctly identified.
"""
import requests
from typing import Dict, Any, List, Optional


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


def search_products(query: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """
    Search OpenFoodFacts for products matching the query.
    Searches the GLOBAL database (Indian + European + American + all countries)
    but sorts results so Indian products appear first.
    
    Args:
        query: Search term (product name like "Maggi", "Nutella", "Oreo", etc.)
        page: Page number for pagination
        page_size: Number of results per page
    
    Returns:
        Dictionary with success status and list of products
    """
    if not query or not query.strip():
        return {"success": False, "error": "Empty search query"}
    
    try:
        # Search the GLOBAL database (no country filter)
        params = {
            "search_terms": query.strip(),
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page": page,
            "page_size": 50,  # Fetch more — many will be filtered as junk
            "fields": "code,product_name,brands,image_front_small_url,ingredients_text,categories,nova_group,nutriscore_grade,countries_tags",
        }
        
        response = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        products = _parse_search_results(data)
        
        # Sort: Indian products first, then the rest
        products.sort(key=lambda p: (0 if p.get("is_indian") else 1))
        
        # Limit to a reasonable number
        products = products[:page_size]
        
        return {
            "success": True,
            "count": len(products),
            "products": products,
        }
    
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


def _is_quality_product(name: str, brand: str, ingredients_text: str = "") -> bool:
    """
    Check if a product entry looks like a real, quality entry in English.
    Filters out junk/spam/test entries and non-English products from OpenFoodFacts.
    
    Returns True if the product looks legitimate and is in English.
    """
    import re
    
    # Reject very short names
    if len(name) < 3:
        return False
    
    # ---- ENGLISH LANGUAGE CHECK ----
    # Reject names with non-Latin characters (Chinese, Arabic, Korean, Cyrillic, Thai, etc.)
    # Allow basic ASCII + common accented chars (é, ñ, ü) that appear in English product names
    ascii_chars = sum(1 for c in name if ord(c) < 128)
    if ascii_chars / max(len(name), 1) < 0.90:  # Less than 90% ASCII = non-English
        return False
    
    # Reject ingredients that are mostly non-English
    if ingredients_text:
        ing_ascii = sum(1 for c in ingredients_text if ord(c) < 128)
        if ing_ascii / max(len(ingredients_text), 1) < 0.85:
            return False
    
    # Reject names that are all uppercase gibberish (e.g. "SDHK GRN SLD")
    words = name.split()
    
    # If the name has too many very short words (abbreviation soup), it's junk
    # e.g. "Bty crk sdnly grain sld sd dsh kit hrvst" — most words are <4 chars
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
        # If name is very short or has no vowels, it's probably junk
        vowel_count = sum(1 for c in name.lower() if c in 'aeiou')
        if vowel_count < len(name) * 0.15:  # Less than 15% vowels = gibberish
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
        
        # Extract ingredients text — try English first, then generic
        ingredients_text = (
            product.get("ingredients_text_en")
            or product.get("ingredients_text")
            or ""
        ).strip()
        
        if not ingredients_text:
            return {
                "success": False,
                "error": "NO_INGREDIENTS",
                "message": "This product exists in the database but no ingredient list is available. Try typing the ingredients manually.",
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


def _parse_search_results(data: dict) -> List[Dict[str, Any]]:
    """Parse OpenFoodFacts search response into clean product list.
    Only includes products that have ingredient data (so every result is analyzable).
    Filters out junk/spam/test entries with garbage names.
    Tags each product with country info for sorting (Indian products first).
    Uses both countries_tags AND known Indian brand detection for accuracy.
    """
    products = []
    
    for item in data.get("products", []):
        product_name = (item.get("product_name") or "").strip()
        ingredients_text = (item.get("ingredients_text") or "").strip()
        brand = (item.get("brands") or "Unknown").strip()
        
        # Skip products without a name or without ingredients
        if not product_name or not ingredients_text:
            continue
        
        # Skip junk/spam/test products with garbage names
        if not _is_quality_product(product_name, brand, ingredients_text):
            continue
        
        # Detect if this is an Indian product:
        # 1. Check countries_tags for India
        # 2. Check if brand is a known Indian brand (catches exports like Haldiram in USA)
        countries_tags = item.get("countries_tags") or []
        tagged_as_india = any("india" in tag.lower() for tag in countries_tags)
        brand_is_indian = _is_known_indian_brand(brand) or _is_known_indian_brand(product_name)
        
        is_indian = tagged_as_india or brand_is_indian
        
        # Determine country label for display
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
            # Extract country name from tag like "en:spain" -> "Spain"
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
    
    return products

