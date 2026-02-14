"""
AI-powered ingredient analysis service
Uses OpenAI GPT to analyze ingredient lists and provide health insights
Combined with scientific scoring based on NOVA/Nutri-Score methodology
"""
import os
import json
from typing import Dict, Any, Optional
from .ingredient_scorer import IngredientScorer

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class IngredientAnalyzer:
    """Analyzes ingredient lists and provides health insights"""
    
    def __init__(self):
        self.openai_client = None
        self.scorer = IngredientScorer()  # Our scientific scorer
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    self.openai_client = OpenAI(api_key=api_key)
                except Exception as e:
                    print(f"Warning: Could not initialize OpenAI client: {e}")
                    print("Falling back to rule-based analysis")
                    self.openai_client = None
    
    def analyze_ingredients(self, ingredient_text: str, confidence: float) -> Dict[str, Any]:
        """
        Analyze ingredient text and return structured health insights
        
        Args:
            ingredient_text: Raw ingredient text
            confidence: Confidence score (0-100)
        
        Returns:
            Dictionary with analysis results
        """
        # Try AI analysis if available
        if self.openai_client:
            try:
                return self._analyze_with_ai(ingredient_text, confidence)
            except Exception as e:
                print(f"AI analysis error: {e}")
                # Fall back to rule-based analysis
        
        # Use rule-based analysis as fallback
        return self._analyze_with_rules(ingredient_text, confidence)
    
    def _analyze_with_ai(self, ingredient_text: str, confidence: float) -> Dict[str, Any]:
        """Use OpenAI GPT to analyze ingredients"""
        
        prompt = f"""You are a food safety expert providing honest, comprehensive ingredient analysis. Be direct and specific about health impacts.

Ingredient List:
{ingredient_text}

Provide a JSON response with the following structure:
{{
    "product": {{
        "name": "Guessed Product Name",
        "category": "Food Category"
    }},
    "verdict": "Clear, honest summary (1-2 sentences)",
    "suitability": {{
        "goodFor": "Who is this good for?",
        "cautionFor": "Who should be careful?",
        "avoidFor": "Who should avoid this?"
    }},
    "ingredients": ["Clean list of ingredients (array of strings)"],
    "flags": [
        {{"icon": "⚠️", "text": "Flag content"}}
    ]
}}
"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a food safety expert providing honest, comprehensive ingredient analysis. Be direct and specific about health impacts."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        # Extract ingredients list from AI response
        ingredients_list = analysis.get('ingredients', [])
        if not ingredients_list:
             ingredients_list = self._extract_ingredients_from_text(ingredient_text)

        # Use our scientific scorer for the actual score
        score_data = self.scorer.calculate_score(ingredients_list)
        
        # Override AI's score with our calculated score
        analysis['score'] = score_data['score']
        analysis['score_breakdown'] = score_data['score_breakdown']
        analysis['nova_group'] = score_data['nova_group']
        analysis['whole_food_percentage'] = score_data['whole_food_ratio']
        
        analysis['success'] = True
        analysis['confidence'] = confidence
        analysis['method'] = 'ai+scientific_scorer'
        
        return analysis

    def _analyze_with_rules(self, ingredient_text: str, confidence: float) -> Dict[str, Any]:
        """
        Factual, neutral, frequency-based ingredient analysis.
        Generates exactly 7 sections as per new guidelines.
        """
        from .additive_service import identify_additives
        
        # Parse ingredients
        ingredients_list = self._extract_ingredients_from_text(ingredient_text)
        
        # Use scientific scorer
        score_data = self.scorer.calculate_score(ingredients_list)
        score = score_data['score']
        nova_group = score_data['nova_group']
        
        # Detect additives
        additives = identify_additives(ingredient_text.lower())
        
        # --- SECTION 1: Product Overview ---
        processing_level = "Highly processed" if nova_group == 4 else \
                          "Moderately processed" if nova_group == 3 else \
                          "Minimally processed"
        
        ingredient_count = len(ingredients_list)
        has_additives = len(additives) > 0
        
        overview = {
            "processing_level": processing_level,
            "ingredient_count": ingredient_count,
            "additives_present": "Yes" if has_additives else "No"
        }
        
        # --- SECTION 2: Frequency Verdict ---
        # Based on score and processing
        if score < 30 or nova_group == 4:
            frequency_verdict = "❌ Not suitable for daily consumption"
        elif score < 60 or nova_group == 3:
            frequency_verdict = "⚠️ Okay occasionally"
        else:
            frequency_verdict = "✅ Fine for regular use"
        
        # --- SECTION 3: Key Signals ---
        text_lower = ingredient_text.lower()
        
        # Detect added sugar
        sugar_keywords = ['sugar', 'glucose', 'fructose', 'syrup', 'sweetener', 'sucrose', 'maltose']
        has_added_sugar = any(s in text_lower for s in sugar_keywords)
        
        # Detect refined flour/starch
        refined_keywords = ['refined', 'maida', 'starch', 'corn starch', 'modified starch']
        has_refined = any(r in text_lower for r in refined_keywords)
        
        # Detect artificial colors
        color_keywords = ['color', 'colour', 'tartrazine', 'sunset yellow', 'carmoisine']
        has_artificial_colors = any(c in text_lower for c in color_keywords)
        
        # Count preservatives
        preservative_keywords = ['preservative', 'sodium benzoate', 'potassium sorbate', 'citric acid', 'acetic acid']
        preservative_count = sum(1 for p in preservative_keywords if p in text_lower)
        
        # Detect artificial flavors
        flavor_keywords = ['artificial flavor', 'artificial flavour', 'nature identical', 'flavouring']
        has_artificial_flavors = any(f in text_lower for f in flavor_keywords)
        
        key_signals = {
            "added_sugar": "Yes" if has_added_sugar else "No",
            "refined_flour_starch": "Yes" if has_refined else "No",
            "artificial_colors": "Yes" if has_artificial_colors else "No",
            "preservatives": f"Yes ({preservative_count})" if preservative_count > 0 else "No",
            "artificial_flavors": "Yes" if has_artificial_flavors else "No"
        }
        
        # --- SECTION 4: Ingredient Breakdown ---
        # Analyze each ingredient with role and risk level
        ingredient_breakdown = []
        
        for ing in ingredients_list:
            ing_lower = ing.lower()
            
            # Determine role (one word)
            if any(s in ing_lower for s in ['wheat', 'rice', 'oat', 'potato', 'corn']):
                role = "Base"
            elif any(s in ing_lower for s in ['oil', 'fat', 'ghee', 'butter']):
                role = "Fat"
            elif any(s in ing_lower for s in sugar_keywords):
                role = "Sweetener"
            elif any(s in ing_lower for s in ['salt', 'sodium']):
                role = "Seasoning"
            elif any(s in ing_lower for s in preservative_keywords):
                role = "Preservative"
            elif any(s in ing_lower for s in color_keywords):
                role = "Color"
            elif any(s in ing_lower for s in flavor_keywords):
                role = "Flavor"
            elif 'emulsifier' in ing_lower:
                role = "Emulsifier"
            elif 'stabilizer' in ing_lower or 'thickener' in ing_lower:
                role = "Stabilizer"
            else:
                role = "Ingredient"
            
            # Determine risk level
            # 🟢 = low concern, 🟡 = moderate, 🔴 = high caution
            if any(bad in ing_lower for bad in ['artificial', 'refined', 'hydrogenated', 'high fructose', 'msg', 'tartrazine']):
                risk = "🔴"
            elif any(mod in ing_lower for mod in ['sugar', 'salt', 'preservative', 'color', 'flavor', 'modified']):
                risk = "🟡"
            else:
                risk = "🟢"
            
            ingredient_breakdown.append({
                "name": ing,
                "role": role,
                "risk": risk
            })
        
        # --- SECTION 5: Who Should Limit This ---
        limit_groups = []
        
        if has_added_sugar or nova_group >= 3:
            limit_groups.append("Children")
        
        if has_added_sugar:
            limit_groups.append("Diabetics")
        
        if nova_group == 4 or score < 40:
            limit_groups.append("People eating packaged food daily")
        
        # --- SECTION 6: Bottom Line ---
        # 2 sentences max
        sentence1 = f"This is a {processing_level.lower()} packaged food."
        
        if "❌" in frequency_verdict:
            sentence2 = "Not recommended for regular consumption."
        elif "⚠️" in frequency_verdict:
            sentence2 = "It's okay occasionally, but not a good everyday habit."
        else:
            sentence2 = "Suitable for regular use based on ingredients."
        
        bottom_line = f"{sentence1} {sentence2}"
        
        # --- SECTION 7: Transparency Note ---
        transparency_note = "Analysis is based only on the ingredient list, not quantities or manufacturing quality."
        
        # Return structured data
        return {
            'success': True,
            'confidence': confidence,
            'method': 'factual_analysis',
            'score': score,
            'nova_group': nova_group,
            
            # New structured sections
            'overview': overview,
            'frequency_verdict': frequency_verdict,
            'key_signals': key_signals,
            'ingredient_breakdown': ingredient_breakdown,
            'limit_groups': limit_groups,
            'bottom_line': bottom_line,
            'transparency_note': transparency_note,
            
            # Legacy fields for compatibility
            'product': {
                'name': 'Analyzed Product',
                'brand': 'Unknown',
                'category': 'Packaged Food',
                'nova_group': nova_group
            },
            'ingredients': ingredients_list,
            'verdict': frequency_verdict  # For backward compatibility
        }
    
    def _extract_ingredients_from_text(self, text: str) -> list:
        """
        Extract individual ingredients from text using robust parsing.
        Handles:
        - Parentheses nesting (keeping inner text together)
        - Lowercase conversion
        - varied delimiters (comma, newline, semicolon, bullets)
        - Contextual delimiters ('and', '&', 'contains')
        - cleaning (removing 'permitted', 'added', etc.)
        """
        if not text:
            return []
            
        # 1. Lowercase everything as requested
        text = text.lower()
            
        # 2. Pre-processing
        # Normalize newlines
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove common start prefixes
        prefixes = ['ingredients:', 'contains:', 'ingredients', 'contains']
        start_index = 0
        for prefix in prefixes:
            if text.startswith(prefix):
                 start_index = len(prefix)
                 while start_index < len(text) and not text[start_index].isalnum():
                     start_index += 1
                 break
        processed_text = text[start_index:]
        
        # 3. Tokenization state machine
        ingredients = []
        current = []
        depth = 0
        
        # Delimiters
        hard_delimiters = {',', ';', '\n', '|', '•', '·', '—'}
        
        i = 0
        n = len(processed_text)
        
        while i < n:
            char = processed_text[i]
            
            # Parenthesis tracking
            if char in '([{' :
                depth += 1
                current.append(char)
            elif char in ')]}':
                if depth > 0:
                    depth -= 1
                current.append(char)
            
            # Check for delimiters at top level
            elif depth == 0:
                is_delimiter = False
                skip_len = 1
                
                if char in hard_delimiters:
                    is_delimiter = True
                
                elif char == '&':
                     is_delimiter = True
                     
                # Word-based separators
                elif char == ' ':
                    remaining = n - i
                    # Check for " and "
                    if remaining > 5 and processed_text[i:i+5] == ' and ':
                        is_delimiter = True
                        skip_len = 5
                    # Check for " contains "
                    elif remaining > 10 and processed_text[i:i+10] == ' contains ':
                        is_delimiter = True
                        skip_len = 10
                    # Check for " like "
                    elif remaining > 6 and processed_text[i:i+6] == ' like ':
                         is_delimiter = True
                         skip_len = 6
                
                if is_delimiter:
                    item = "".join(current).strip()
                    if item:
                        ingredients.append(item)
                    current = []
                    i += skip_len - 1
                else:
                    current.append(char)
            else:
                current.append(char)
            i += 1
            
        item = "".join(current).strip()
        if item:
            ingredients.append(item)
            
        # 4. Post-processing & Cleaning
        final_list = []
        seen = set()
        
        # filler words to remove
        filler_words = {'permitted', 'added'}
        
        for ing in ingredients:
            # Clean punctuation
            ing = ing.strip('•·-—*#: .')
            
            # Remove filler words
            words = ing.split()
            clean_words = [w for w in words if w not in filler_words]
            ing = " ".join(clean_words)
            
            if len(ing) < 2:
                continue
            
            if ing not in seen:
                final_list.append(ing)
                seen.add(ing)
                
        return final_list


def _detect_ingredients(text: str) -> bool:
    """Check if extracted text likely contains ingredient information"""
    if not text or len(text.strip()) < 3:
        return False
    
    # Expanded keywords: superfoods, herbs, spices, Ayurvedic ingredients
    ingredient_keywords = [
        'ingredient', 'contains', 'wheat', 'flour', 'sugar', 'salt',
        'oil', 'water', 'milk', 'egg', 'soy', 'preservative',
        'oats', 'quinoa', 'rice', 'almond', 'walnut', 'turmeric',
        'cinnamon', 'ginger', 'garlic', 'moringa', 'spirulina',
        'amla', 'licorice', 'cacao', 'honey', 'lemon', 'tomato'
    ]
    
    text_lower = text.lower()
    keyword_matches = sum(1 for keyword in ingredient_keywords if keyword in text_lower)
    comma_count = text_lower.count(',')
    newline_count = text_lower.count('\n')
    
    # Lenient: 1+ keyword OR 2+ commas OR 2+ newlines
    return keyword_matches >= 1 or comma_count >= 2 or newline_count >= 2


# Singleton analyzer instance — avoids re-initializing OpenAI client on every request
_analyzer_instance = None

def _get_analyzer():
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = IngredientAnalyzer()
    return _analyzer_instance


def analyze_product_from_text(text: str) -> Dict[str, Any]:
    """
    Main entry point for analyzing ingredients from text string
    """
    analyzer = _get_analyzer()
    
    # Check if text looks like ingredients
    if not _detect_ingredients(text):
         return {
            'success': False,
            'error': 'NO_INGREDIENTS_DETECTED',
            'message': 'The text provided does not appear to be a valid ingredient list.',
            'suggestions': [
                'Please enter a comma-separated list of ingredients',
                'Ensure you are entering food ingredients, not random text'
            ],
            'confidence': 0.0,
        }
    
    # Analyze ingredients (AI or Rules)
    # Using 100% confidence for manual text entry
    analysis = analyzer.analyze_ingredients(text, 100.0)
    
    analysis['raw_ingredients'] = text
    return analysis
