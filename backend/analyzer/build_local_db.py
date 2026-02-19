"""
Build a local product database by fetching popular Indian products from OpenFoodFacts.
This pre-built cache makes searches instant for ~90% of common queries.

Run: python manage.py shell -c "from analyzer.build_local_db import build; build()"
  OR: python -c "from analyzer.build_local_db import build; build()"
"""
import json
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product"
HEADERS = {"User-Agent": "Ingrexa/1.0 (https://ingrexa.com; contact@ingrexa.com)"}
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "local_products.json")

# Popular Indian search terms — covers ~90% of typical user searches
POPULAR_QUERIES = [
    # Dairy
    "Amul Butter", "Amul Cheese", "Amul Milk", "Mother Dairy",
    "Britannia Cheese", "Nestle Milkmaid",
    # Snacks
    "Kurkure", "Lays", "Haldiram", "Balaji Wafers", "Bingo",
    "Pringles", "Doritos", "Uncle Chipps",
    # Biscuits
    "Britannia", "Parle-G", "Parle", "Oreo", "Dark Fantasy",
    "Good Day", "Hide and Seek", "Marie Gold", "Bourbon",
    # Noodles & Ready-to-eat
    "Maggi", "Yippee", "Top Ramen", "Knorr", "Nissin",
    # Beverages
    "Coca Cola", "Pepsi", "Sprite", "Fanta", "Thumbs Up",
    "Maaza", "Frooti", "Appy Fizz", "Mountain Dew",
    "Red Bull", "Monster Energy",
    "Tropicana", "Real Juice", "Paper Boat",
    # Tea & Coffee
    "Tata Tea", "Brooke Bond", "Nescafe", "Bru Coffee",
    # Chocolate & Candy
    "Cadbury", "Dairy Milk", "5 Star", "KitKat", "Ferrero Rocher",
    "Munch", "Snickers", "Gems",
    # Spreads & Sauces
    "Nutella", "Kissan Ketchup", "Maggi Sauce", "Veeba",
    # Cereals
    "Kelloggs", "Chocos", "Corn Flakes", "Oats", "Muesli",
    # Health & Nutrition
    "Complan", "Horlicks", "Bournvita", "Protinex",
    # Indian Staples
    "Aashirvaad Atta", "Fortune Oil", "Saffola", "Tata Salt",
    "MDH Masala", "Everest Masala", "Catch Masala",
    # Ice Cream
    "Kwality Walls", "Amul Ice Cream", "Magnum",
    # Others
    "Heinz", "Kinder Joy", "Tic Tac", "Mentos",
]


def _fetch_search(query, session):
    """Fetch search results for a query with retries."""
    params = {
        "search_terms": query.strip(),
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page": 1,
        "page_size": 10,
        "fields": "code,product_name,brands,image_front_small_url,categories,"
                  "nova_group,nutriscore_grade,countries_tags,"
                  "ingredients_text,ingredients_text_en,nutriments,serving_size,quantity",
    }
    for attempt in range(3):
        try:
            r = session.get(SEARCH_URL, params=params, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r.json().get("products", [])
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
                continue
            print(f"⚠ Failed: {type(e).__name__}")
            return []


def _is_english(text):
    if not text:
        return False
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    return ascii_chars / max(len(text), 1) >= 0.85


def _get_english_ingredients(item):
    en = (item.get("ingredients_text_en") or "").strip()
    generic = (item.get("ingredients_text") or "").strip()
    if en and _is_english(en):
        return en
    if generic and _is_english(generic):
        return generic
    return ""


def _clean_product(item):
    """Extract clean product data from an OFF item."""
    name = (item.get("product_name") or "").strip()
    brand = (item.get("brands") or "").strip()
    ingredients = _get_english_ingredients(item)

    if not name or len(name) < 3 or not _is_english(name):
        return None

    return {
        "barcode": item.get("code", ""),
        "name": name,
        "brand": brand or "Unknown",
        "image_url": item.get("image_front_small_url", ""),
        "ingredients_text": ingredients,
        "categories": (item.get("categories") or "").strip(),
        "nova_group": item.get("nova_group"),
        "nutriscore_grade": item.get("nutriscore_grade"),
        "nutriments_raw": item.get("nutriments"),
        "serving_size": item.get("serving_size", ""),
        "quantity": item.get("quantity", ""),
        "countries_tags": item.get("countries_tags", []),
    }


def build():
    """Build the local product database."""
    session = requests.Session()
    all_products = {}
    
    total = len(POPULAR_QUERIES)
    print(f"🔍 Fetching {total} popular product queries from OpenFoodFacts...")
    print(f"   This will take ~{total * 2} seconds\n")

    for i, query in enumerate(POPULAR_QUERIES, 1):
        print(f"  [{i}/{total}] Searching: {query}...", end=" ", flush=True)
        items = _fetch_search(query, session)
        added = 0
        for item in items:
            product = _clean_product(item)
            if product and product["barcode"] not in all_products:
                all_products[product["barcode"]] = product
                added += 1
        print(f"→ {added} new products (total: {len(all_products)})")
        time.sleep(2)  # Be nice to the API

    # Build search index: lowercase name + brand for matching
    db = {
        "version": 1,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "product_count": len(all_products),
        "products": list(all_products.values()),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)

    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"\n✅ Saved {len(all_products)} products to {OUTPUT_PATH}")
    print(f"   File size: {size_mb:.1f} MB")


if __name__ == "__main__":
    build()
