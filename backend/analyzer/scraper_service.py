"""
URL Scraping Service for extracting product information from web pages
Supports various e-commerce platforms and product pages
"""
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time


class ProductScraper:
    """Scrapes product information from URLs"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.timeout = 10
    
    def scrape_url(self, url):
        """
        Main method to scrape product information from URL
        
        Returns:
            dict with keys: success, product_name, brand, ingredients, image_url, error
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    'success': False,
                    'error': 'INVALID_URL',
                    'message': 'Please provide a valid URL with http:// or https://'
                }
            
            # Fetch the page
            print(f"Fetching URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Detect platform and use appropriate scraper
            domain = parsed.netloc.lower()
            
            if 'amazon' in domain:
                return self._scrape_amazon(soup, url)
            elif 'walmart' in domain:
                return self._scrape_walmart(soup, url)
            elif 'target' in domain:
                return self._scrape_target(soup, url)
            elif 'instacart' in domain:
                return self._scrape_instacart(soup, url)
            else:
                # Generic scraper for other sites
                return self._scrape_generic(soup, url)
        
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'TIMEOUT',
                'message': 'The request timed out. The website may be slow or unavailable.'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': 'REQUEST_FAILED',
                'message': f'Failed to fetch the URL: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'SCRAPING_FAILED',
                'message': f'An error occurred while scraping: {str(e)}'
            }
    
    def _scrape_amazon(self, soup, url):
        """Scrape Amazon product pages"""
        result = {
            'success': False,
            'product_name': None,
            'brand': None,
            'ingredients': None,
            'image_url': None,
        }
        
        # Product name
        title_elem = soup.find('span', {'id': 'productTitle'})
        if title_elem:
            result['product_name'] = title_elem.get_text(strip=True)
        
        # Brand
        brand_elem = soup.find('a', {'id': 'bylineInfo'}) or soup.find('span', {'class': 'a-size-base po-break-word'})
        if brand_elem:
            result['brand'] = brand_elem.get_text(strip=True).replace('Brand: ', '').replace('Visit the ', '').replace(' Store', '')
        
        # Ingredients - Amazon has various formats
        ingredients_patterns = [
            soup.find('div', {'id': 'ingredients'}),
            soup.find('div', {'id': 'important-information'}),
            soup.find('div', string=re.compile('Ingredients', re.I)),
        ]
        
        for elem in ingredients_patterns:
            if elem:
                # Look for ingredients in the element or its siblings
                text = elem.get_text(strip=True)
                ingredients = self._extract_ingredients_from_text(text)
                if ingredients:
                    result['ingredients'] = ingredients
                    break
        
        # Image
        img_elem = soup.find('img', {'id': 'landingImage'}) or soup.find('img', {'class': 'a-dynamic-image'})
        if img_elem and img_elem.get('src'):
            result['image_url'] = img_elem['src']
        
        result['success'] = bool(result['ingredients'])
        if not result['success']:
            result['error'] = 'NO_INGREDIENTS_FOUND'
            result['message'] = 'Could not find ingredient information on this Amazon page.'
        
        return result
    
    def _scrape_walmart(self, soup, url):
        """Scrape Walmart product pages"""
        result = {
            'success': False,
            'product_name': None,
            'brand': None,
            'ingredients': None,
            'image_url': None,
        }
        
        # Product name
        title_elem = soup.find('h1', {'itemprop': 'name'})
        if title_elem:
            result['product_name'] = title_elem.get_text(strip=True)
        
        # Ingredients
        ingredients_elem = soup.find(string=re.compile('Ingredients', re.I))
        if ingredients_elem:
            parent = ingredients_elem.find_parent()
            if parent:
                text = parent.get_text(strip=True)
                result['ingredients'] = self._extract_ingredients_from_text(text)
        
        result['success'] = bool(result['ingredients'])
        if not result['success']:
            result['error'] = 'NO_INGREDIENTS_FOUND'
            result['message'] = 'Could not find ingredient information on this Walmart page.'
        
        return result
    
    def _scrape_target(self, soup, url):
        """Scrape Target product pages"""
        result = {
            'success': False,
            'product_name': None,
            'brand': None,
            'ingredients': None,
            'image_url': None,
        }
        
        # Product name
        title_elem = soup.find('h1', {'data-test': 'product-title'})
        if title_elem:
            result['product_name'] = title_elem.get_text(strip=True)
        
        # Ingredients
        ingredients_elem = soup.find(string=re.compile('Ingredients', re.I))
        if ingredients_elem:
            parent = ingredients_elem.find_parent()
            if parent:
                text = parent.get_text(strip=True)
                result['ingredients'] = self._extract_ingredients_from_text(text)
        
        result['success'] = bool(result['ingredients'])
        if not result['success']:
            result['error'] = 'NO_INGREDIENTS_FOUND'
            result['message'] = 'Could not find ingredient information on this Target page.'
        
        return result
    
    def _scrape_instacart(self, soup, url):
        """Scrape Instacart product pages"""
        result = {
            'success': False,
            'product_name': None,
            'brand': None,
            'ingredients': None,
            'image_url': None,
        }
        
        # Product name
        title_elem = soup.find('h1')
        if title_elem:
            result['product_name'] = title_elem.get_text(strip=True)
        
        # Ingredients
        ingredients_elem = soup.find(string=re.compile('Ingredients', re.I))
        if ingredients_elem:
            parent = ingredients_elem.find_parent()
            if parent:
                text = parent.get_text(strip=True)
                result['ingredients'] = self._extract_ingredients_from_text(text)
        
        result['success'] = bool(result['ingredients'])
        if not result['success']:
            result['error'] = 'NO_INGREDIENTS_FOUND'
            result['message'] = 'Could not find ingredient information on this Instacart page.'
        
        return result
    
    def _scrape_generic(self, soup, url):
        """Generic scraper for unknown sites"""
        result = {
            'success': False,
            'product_name': None,
            'brand': None,
            'ingredients': None,
            'image_url': None,
        }
        
        # Try to find product name
        og_title = soup.find('meta', {'property': 'og:title'})
        if og_title:
            result['product_name'] = og_title.get('content', '').strip()
        else:
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                result['product_name'] = title_elem.get_text(strip=True)
        
        # Try to find product image
        og_image = soup.find('meta', {'property': 'og:image'})
        if og_image:
            result['image_url'] = og_image.get('content', '').strip()
        else:
            # Fallback for image
            img_elem = soup.find('img', {'class': re.compile(r'product|main|primary', re.I)})
            if img_elem and img_elem.get('src'):
                result['image_url'] = img_elem['src']
        
        # Look for ingredients anywhere on the page
        # Search for common patterns in IDs or Classes
        potential_containers = soup.find_all(['div', 'span', 'section', 'p', 'li'], 
            id=re.compile(r'ingredient|nutrition|label|product-info', re.I))
        potential_containers += soup.find_all(['div', 'span', 'section', 'p', 'li'], 
            class_=re.compile(r'ingredient|nutrition|label|product-info', re.I))
        
        for container in potential_containers:
            text = container.get_text(strip=True, separator=' ')
            ingredients = self._extract_ingredients_from_text(text)
            if ingredients and len(ingredients) > 15:
                result['ingredients'] = ingredients
                result['success'] = True
                return result

        # Fallback keyword search
        ingredients_keywords = ['ingredients', 'ingredient list', 'contains', 'composition', 'what\'s inside']
        
        for keyword in ingredients_keywords:
            # Find elements containing the keyword
            elements = soup.find_all(string=re.compile(keyword, re.I))
            
            for elem in elements:
                parent = elem.find_parent()
                if parent:
                    # Get text from parent and siblings
                    text = parent.get_text(strip=True)
                    
                    # Also check next siblings
                    next_elem = parent.find_next_sibling()
                    if next_elem:
                        text += ' ' + next_elem.get_text(strip=True)
                    
                    ingredients = self._extract_ingredients_from_text(text)
                    if ingredients and len(ingredients) > 20:  # Reasonable length
                        result['ingredients'] = ingredients
                        result['success'] = True
                        return result
        
        # If still no ingredients found
        if not result['success']:
            result['error'] = 'NO_INGREDIENTS_FOUND'
            result['message'] = 'Could not find ingredient information on this page. The site may not be supported or the page structure is unusual.'
        
        return result
    
    def _extract_ingredients_from_text(self, text):
        """Extract ingredient list from text"""
        if not text:
            return None
        
        # Common patterns to find ingredients
        patterns = [
            r'Ingredients?:?\s*(.+?)(?:\.|$|Nutrition|Allergen|Contains|Directions|Storage)',
            r'Ingredient List:?\s*(.+?)(?:\.|$|Nutrition|Allergen|Contains)',
            r'Contains:?\s*(.+?)(?:\.|$|Nutrition|Allergen|Directions)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                ingredients = match.group(1).strip()
                # Clean up
                ingredients = re.sub(r'\s+', ' ', ingredients)  # Remove extra whitespace
                ingredients = ingredients.strip('.,;: ')
                
                # Validate it looks like ingredients (has commas or multiple words)
                if ',' in ingredients or len(ingredients.split()) > 3:
                    return ingredients
        
        return None


def scrape_product_url(url):
    """
    Main function to scrape product information from URL
    
    Args:
        url: Product page URL
    
    Returns:
        dict with scraping results
    """
    scraper = ProductScraper()
    return scraper.scrape_url(url)
