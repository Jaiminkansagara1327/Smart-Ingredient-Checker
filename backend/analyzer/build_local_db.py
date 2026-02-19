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

# Popular search terms — massive coverage for instant results
POPULAR_QUERIES = [
    # ===== DAIRY =====
    "Amul Butter", "Amul Cheese", "Amul Milk", "Amul Ghee", "Amul Paneer",
    "Amul Lassi", "Amul Buttermilk", "Amul Chocolate", "Amul Ice Cream",
    "Amul Cream", "Amul Yogurt", "Amul Curd",
    "Mother Dairy", "Mother Dairy Milk", "Mother Dairy Curd",
    "Britannia Cheese", "Britannia Milk",
    "Nestle Milkmaid", "Nestle Milk", "Nestle Yogurt",
    "Nandini Milk", "Verka Milk", "Sudha Milk",
    "Gowardhan Ghee", "Patanjali Ghee", "Patanjali Cow Ghee",
    "Epigamia Yogurt", "Epigamia",
    "Go Cheese", "Govardhan Paneer",
    "Yakult",

    # ===== SNACKS & CHIPS =====
    "Kurkure", "Lays", "Lays Magic Masala", "Lays Classic Salted",
    "Haldiram", "Haldiram Bhujia", "Haldiram Namkeen", "Haldiram Aloo Bhujia",
    "Haldiram Mixture", "Haldiram Sev",
    "Balaji Wafers", "Balaji", "Balaji Namkeen",
    "Bingo", "Bingo Mad Angles", "Bingo Tedhe Medhe",
    "Pringles", "Doritos", "Uncle Chipps",
    "Too Yumm", "Act II Popcorn", "ACT II",
    "Garden Wafers", "Bikano", "Bikano Bhujia",
    "Cornitos", "Kettle Chips",
    "Cheetos", "Ruffles", "Fritos",

    # ===== BISCUITS & COOKIES =====
    "Britannia", "Britannia Good Day", "Britannia Marie Gold",
    "Britannia Bourbon", "Britannia Jim Jam", "Britannia NutriChoice",
    "Britannia 50-50", "Britannia Tiger", "Britannia Milk Bikis",
    "Parle-G", "Parle", "Parle Monaco", "Parle Krackjack", "Parle Hide and Seek",
    "Parle Magix", "Parle Fab",
    "Oreo", "Oreo Golden",
    "Dark Fantasy", "Dark Fantasy Choco Fills",
    "Good Day", "Good Day Butter",
    "McVities", "McVities Digestive",
    "Sunfeast", "Sunfeast Dark Fantasy", "Sunfeast Mom's Magic", "Sunfeast Bounce",
    "Unibic", "Unibic Cookies",
    "Priyagold", "Priyagold Butter Bite",

    # ===== NOODLES & INSTANT FOOD =====
    "Maggi", "Maggi Noodles", "Maggi Masala Noodles",
    "Maggi Hot Heads", "Maggi Pazzta",
    "Yippee", "Yippee Noodles", "Yippee Magic Masala",
    "Top Ramen", "Top Ramen Curry", "Top Ramen Smoodles",
    "Knorr", "Knorr Soupy Noodles", "Knorr Soup",
    "Nissin", "Nissin Cup Noodles",
    "Ching's", "Ching's Noodles", "Ching's Schezwan",
    "Wai Wai", "Wai Wai Noodles",
    "MTR", "MTR Ready to Eat", "MTR Masala",
    "Saffola Oats", "Saffola Masala Oats",
    "Cup Noodles",

    # ===== BEVERAGES - SOFT DRINKS =====
    "Coca Cola", "Coca Cola Zero", "Diet Coke",
    "Pepsi", "Pepsi Black", "Pepsi Max",
    "Sprite", "Sprite Zero",
    "Fanta", "Fanta Orange",
    "Thumbs Up", "Thums Up",
    "Limca", "Mirinda", "Mirinda Orange",
    "Mountain Dew", "7Up", "7 Up",
    "Schweppes", "Tonic Water",
    "Sting Energy", "Sting",

    # ===== BEVERAGES - JUICES & DRINKS =====
    "Maaza", "Frooti", "Appy Fizz", "Appy",
    "Tropicana", "Tropicana Orange", "Tropicana Apple",
    "Real Juice", "Real Fruit Juice", "Real Active",
    "Paper Boat", "Paper Boat Aam Panna",
    "B Natural", "B Natural Juice",
    "Raw Pressery", "Raw Pressery Juice",
    "Minute Maid", "Minute Maid Orange",
    "Tang", "Tang Orange",
    "Rasna", "Rooh Afza",
    "Glucon-D", "Glucon D",
    "Electral", "ORS",
    "Coconut Water", "Tender Coconut",

    # ===== BEVERAGES - ENERGY & SPORTS =====
    "Red Bull", "Red Bull Sugar Free",
    "Monster Energy", "Monster",
    "Gatorade", "Gatorade Sports Drink",
    "Sting Energy Drink",

    # ===== TEA & COFFEE =====
    "Tata Tea", "Tata Tea Premium", "Tata Tea Gold",
    "Brooke Bond", "Brooke Bond Red Label", "Brooke Bond Taj Mahal",
    "Wagh Bakri", "Wagh Bakri Tea",
    "Society Tea",
    "Nescafe", "Nescafe Classic", "Nescafe Gold",
    "Bru Coffee", "Bru Instant Coffee",
    "Continental Coffee", "Davidoff Coffee",
    "Green Tea", "Lipton Green Tea", "Tetley Green Tea",
    "Lipton", "Tetley",

    # ===== CHOCOLATE & CONFECTIONERY =====
    "Cadbury", "Cadbury Dairy Milk", "Cadbury Dairy Milk Silk",
    "Cadbury 5 Star", "Cadbury Perk", "Cadbury Gems",
    "Cadbury Celebrations", "Cadbury Fruit and Nut",
    "Cadbury Bournville", "Cadbury Temptations",
    "5 Star", "Perk", "Gems",
    "KitKat", "Kit Kat",
    "Ferrero Rocher", "Ferrero",
    "Munch", "Munch Nuts",
    "Snickers", "Mars", "Twix", "Bounty", "Milky Way",
    "M&M", "M&Ms",
    "Toblerone", "Lindt", "Lindt Lindor",
    "Hershey", "Hersheys",
    "Kinder Joy", "Kinder Bueno", "Kinder",
    "Tic Tac", "Mentos", "Mentos Gum",
    "Chupa Chups", "Alpenliebe",
    "Center Fresh", "Center Fruit",
    "Eclairs", "Melody",
    "Nestle Milkybar", "Milkybar",
    "Amul Dark Chocolate",

    # ===== SPREADS, SAUCES & CONDIMENTS =====
    "Nutella", "Nutella Hazelnut",
    "Kissan Ketchup", "Kissan Jam", "Kissan Mixed Fruit Jam",
    "Maggi Sauce", "Maggi Hot and Sweet", "Maggi Pichkoo",
    "Veeba", "Veeba Mayonnaise", "Veeba Ketchup",
    "Heinz", "Heinz Ketchup", "Heinz Mayonnaise",
    "Del Monte", "Del Monte Ketchup", "Del Monte Pasta Sauce",
    "Ching's Schezwan Chutney",
    "Funfoods", "Funfoods Mayonnaise", "Dr. Oetker Funfoods",
    "Peanut Butter", "Pintola Peanut Butter", "MyFitness Peanut Butter",
    "Sundrop Peanut Butter",
    "Honey", "Dabur Honey", "Patanjali Honey", "Saffola Honey",

    # ===== CEREALS & BREAKFAST =====
    "Kelloggs", "Kelloggs Chocos", "Kelloggs Corn Flakes",
    "Kelloggs Muesli", "Kelloggs Oats", "Kelloggs All Bran",
    "Kelloggs Special K", "Kelloggs Crunchy Granola",
    "Chocos", "Corn Flakes",
    "Oats", "Quaker Oats", "Saffola Oats",
    "Muesli", "Yoga Bar Muesli",
    "Bagrry's", "Bagrry's Muesli", "Bagrry's Oats",
    "Granola", "Granola Bar",
    "Yoga Bar", "RiteBite Max Protein",
    "True Elements",

    # ===== HEALTH & NUTRITION DRINKS =====
    "Complan", "Complan Chocolate",
    "Horlicks", "Junior Horlicks", "Women's Horlicks",
    "Bournvita", "Cadbury Bournvita",
    "Protinex", "Protinex Original",
    "Ensure", "Ensure Diabetes Care",
    "Boost", "Boost Health Drink",
    "Pediasure",
    "Muscle Blaze", "MuscleBlaze Protein",
    "Optimum Nutrition", "ON Whey Protein",
    "Herbalife",
    "Protein Bar", "Yoga Bar Protein",

    # ===== INDIAN STAPLES & COOKING =====
    "Aashirvaad Atta", "Aashirvaad", "Aashirvaad Multigrain",
    "Pillsbury Atta", "Rajdhani Besan",
    "Fortune Oil", "Fortune Sunflower Oil", "Fortune Mustard Oil",
    "Fortune Rice Bran Oil",
    "Saffola", "Saffola Gold Oil", "Saffola Total Oil",
    "Tata Salt", "Tata Rock Salt",
    "Catch Salt", "Catch Sprinklers",
    "MDH Masala", "MDH Chana Masala", "MDH Garam Masala",
    "Everest Masala", "Everest Garam Masala", "Everest Biryani Masala",
    "Catch Masala",
    "Patanjali", "Patanjali Atta", "Patanjali Noodles", "Patanjali Dant Kanti",
    "Daawat Rice", "Daawat Basmati", "India Gate Basmati",
    "Kohinoor Basmati",
    "Tata Sampann", "Tata Sampann Dal",
    "Sundrop Oil", "Dhara Oil",

    # ===== ICE CREAM & FROZEN =====
    "Kwality Walls", "Kwality Walls Cornetto", "Cornetto",
    "Magnum", "Magnum Ice Cream",
    "Häagen-Dazs", "Haagen Dazs",
    "Baskin Robbins",
    "Naturals Ice Cream",
    "Ben and Jerry", "Ben Jerry",
    "McCain", "McCain French Fries", "McCain Nuggets",

    # ===== BREAD & BAKERY =====
    "Britannia Bread", "Harvest Gold",
    "Modern Bread",
    "English Oven",

    # ===== BABY FOOD =====
    "Cerelac", "Nestle Cerelac",
    "Gerber",
    "Lactogen", "Nestle Lactogen",
    "Nan Pro", "Nestle NAN",
    "Similac",

    # ===== INTERNATIONAL BRANDS =====
    "Barilla Pasta", "Barilla",
    "Philadelphia Cream Cheese",
    "Tabasco", "Sriracha",
    "Doritos Nacho",
    "Cheez-It", "Goldfish Crackers",
    "Nutri-Grain",
    "Pop-Tarts",
    "Nature Valley", "Nature Valley Granola",
    "Clif Bar",

    # ===== REGIONAL & SPECIALTY =====
    "Lijjat Papad", "Lijjat",
    "Bikaner", "Bikaneri Bhujia",
    "Chettinad Masala",
    "Ganesh Bhel",
    "Chhedas", "Chhedas Mixture",
    "Jabsons",
    "Smith & Jones",
    "Soya Chunks", "Nutrela Soya",
    "Maggi Bhuna Masala",
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
    """Build the local product database incrementally.
    Loads existing data, skips already-fetched queries, saves progress periodically.
    """
    session = requests.Session()
    
    # Load existing database if present
    all_products = {}
    fetched_queries = set()
    if os.path.exists(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
            for p in existing.get("products", []):
                all_products[p["barcode"]] = p
            fetched_queries = set(existing.get("fetched_queries", []))
            print(f"📦 Loaded existing database: {len(all_products)} products, {len(fetched_queries)} queries already done")
        except Exception as e:
            print(f"⚠ Could not load existing DB: {e}")
    
    # Filter to only new queries
    new_queries = [q for q in POPULAR_QUERIES if q.lower() not in fetched_queries]
    total = len(new_queries)
    
    if total == 0:
        print("✅ All queries already fetched! Nothing new to do.")
        return
    
    print(f"🔍 Fetching {total} new queries ({len(POPULAR_QUERIES) - total} already done)...\n")
    
    failed = 0
    for i, query in enumerate(new_queries, 1):
        print(f"  [{i}/{total}] Searching: {query}...", end=" ", flush=True)
        items = _fetch_search(query, session)
        added = 0
        for item in items:
            product = _clean_product(item)
            if product and product["barcode"] not in all_products:
                all_products[product["barcode"]] = product
                added += 1
        
        if items:
            fetched_queries.add(query.lower())
            print(f"→ {added} new products (total: {len(all_products)})")
        else:
            failed += 1
            print(f"→ SKIPPED (API error)")
        
        # Save progress every 5 queries
        if i % 5 == 0 or i == total:
            _save_db(all_products, fetched_queries)
        
        time.sleep(2)
    
    # Final save
    _save_db(all_products, fetched_queries)
    
    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"\n✅ Done! {len(all_products)} total products saved ({size_mb:.1f} MB)")
    if failed:
        print(f"⚠ {failed} queries failed — run the script again to retry them")


def _save_db(all_products, fetched_queries):
    """Save the current state to disk."""
    db = {
        "version": 1,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "product_count": len(all_products),
        "products": list(all_products.values()),
        "fetched_queries": list(fetched_queries),
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)


if __name__ == "__main__":
    build()
