import requests

def search_product_by_name(product_name):
    """
    Search for a product on Open Food Facts by name
    Returns refined product data if found
    """
    if not product_name or product_name == "Unknown Product":
        return None
        
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={product_name}&search_simple=1&action=process&json=1"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['products']:
                # Return the most relevant product
                product = data['products'][0]
                result_name = product.get('product_name', '').lower()
                
                # Simple verification: only accept if the search term is at least partly in the result
                if product_name.lower() in result_name or any(part in result_name for part in product_name.lower().split()):
                    return {
                        'name': product.get('product_name', product_name),
                        'brand': product.get('brands', 'Unknown'),
                        'nutriscore': product.get('nutriscore_grade', 'unknown'),
                        'nova_group': product.get('nova_group', 'unknown'),
                        'image': product.get('image_url', None),
                        'ingredients_text': product.get('ingredients_text', None)
                    }
    except Exception as e:
        print(f"Open Food Facts API error: {e}")
    
    return None
