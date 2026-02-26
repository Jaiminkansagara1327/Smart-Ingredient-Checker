"""
AI-powered ingredient analysis service
Uses OpenAI GPT to analyze ingredient lists and provide health insights
Combined with scientific scoring based on NOVA/Nutri-Score methodology
"""
import os
import json
import re
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
    
    def analyze_ingredients(self, ingredient_text: str, confidence: float, macros: Dict = None, food_type: str = 'Solid', user_goal: str = 'Regular') -> Dict[str, Any]:
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
                return self._analyze_with_ai(ingredient_text, confidence, macros or {}, food_type, user_goal)
            except Exception as e:
                print(f"AI analysis error: {e}")
                # Fall back to rule-based analysis
        
        # Use rule-based analysis as fallback
        return self._analyze_with_rules(ingredient_text, confidence, macros or {}, food_type, user_goal)
    
    def _analyze_with_ai(self, ingredient_text: str, confidence: float, macros: Dict, food_type: str, user_goal: str) -> Dict[str, Any]:
        """Use OpenAI GPT to analyze ingredients"""
        
        prompt = f"""You are a food safety expert providing honest, comprehensive ingredient analysis. Be direct and specific about health impacts.

Ingredient List (may be in any language):
{ingredient_text}

MANDATORY INSTRUCTION: If the ingredients or product information above are not in English, you MUST translate them accurately into English before performing the analysis. Every single field in your response (product name, category, verdict, suitability, role, explanation, ingredients array, and flags) MUST be in English.

Provide a JSON response with the following structure:
{{
    "product": {{
        "name": "Guessed Product Name",
        "category": "Food Category",
        "food_type": "Solid | Liquid | Semi-solid"
    }},
    "verdict": "Clear, honest summary (1-2 sentences)",
    "suitability": {{
        "goodFor": "Who is this good for?",
        "cautionFor": "Who should be careful?",
        "avoidFor": "Who should avoid this?"
    }},
    "ingredient_details": [
        {{
            "name": "Ingredient Name", 
            "role": "Role", 
            "explanation": "Provide a comprehensive, balanced layman's explanation. (e.g. 'Used to [purpose/benefit] and generally [safety status]. However, in excess it can [potential risks]. Not a health food but [conclusion/necessity].')"
        }}
    ],
    "ingredients": ["Flattened list of ingredients. If an ingredient has sub-components in brackets like 'Cookie Pieces (Flour, Sugar)', split them into separate items: ['Cookie Pieces', 'Flour', 'Sugar']."],
    "flags": [
        {{"icon": "⚠️", "text": "Flag content"}}
    ]
}}
"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a food safety expert. If you receive non-English ingredient lists or product names, you must translate them perfectly into English first. All your responses MUST be in English only, regardless of the input language."},
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

        # Extract food type (Solid, Liquid, Semi-solid)
        ai_food_type = analysis.get('product', {}).get('food_type', 'Solid')
        final_food_type = food_type if food_type != 'Solid' else ai_food_type

        # Use our scientific scorer with exact macros if provided, otherwise AI text fallback
        score_data = self.scorer.calculate_score(ingredients_list, macros, final_food_type, user_goal)
        
        # Build ingredient breakdown with AI explanations
        ingredient_breakdown = []
        ai_ingredients = analysis.get('ingredient_details', [])
        
        if not ai_ingredients:
             # Fallback if AI didn't provide details properly
             for ing in ingredients_list:
                 ingredient_breakdown.append({
                     "name": ing,
                     "role": "Ingredient",
                     "risk": "🟢",
                     "description": "Natural or minimally processed ingredient."
                 })
        else:
            for item in ai_ingredients:
                name = item.get('name', 'Unknown')
                ing_lower = name.lower()
                
                # Determine risk level 🟢 = low concern, 🟡 = moderate, 🔴 = high caution
                if any(bad in ing_lower for bad in ['artificial', 'refined', 'hydrogenated', 'high fructose', 'msg', 'tartrazine', 'aspartame']):
                    risk = "🔴"
                elif any(mod in ing_lower for mod in ['sugar', 'salt', 'preservative', 'color', 'flavor', 'modified', 'gum', 'emulsifier']):
                    risk = "🟡"
                else:
                    risk = "🟢"
                    
                ingredient_breakdown.append({
                    "name": name,
                    "role": item.get('role', 'Ingredient'),
                    "risk": risk,
                    "description": item.get('explanation', 'A common food ingredient.')
                })

        # Final structured response
        return {
            'success': True,
            'confidence': confidence,
            'method': 'ai+scientific_scorer',
            'score': score_data['score'],
            'nova_group': score_data['nova_group'],
            'food_type': final_food_type,
            'details': score_data.get('details', {}),
            'overview': {
                "processing_level": "Highly processed" if score_data['nova_group'] == 4 else "Moderately processed" if score_data['nova_group'] == 3 else "Minimally processed",
                "ingredient_count": len(ingredients_list),
                "additives_present": "Yes" if any(self.scorer.ADDITIVE_CONCERNS.get(ing.lower()) for ing in ingredients_list) else "No"
            },
            'frequency_verdict': analysis.get('verdict', ""),
            'key_signals': {
                "added_sugar": "Yes" if any(s in ingredient_text.lower() for s in self.scorer.ADDED_SUGARS) else "No",
                "refined_flour_starch": "Yes" if any(r in ingredient_text.lower() for r in self.scorer.REFINED_CARBS) else "No",
                "artificial_colors": "Yes" if "color" in ingredient_text.lower() or "colour" in ingredient_text.lower() else "No",
                "preservatives": "Yes" if "preservative" in ingredient_text.lower() else "No",
                "artificial_flavors": "Yes" if "flavor" in ingredient_text.lower() or "flavour" in ingredient_text.lower() else "No"
            },
            'ingredient_breakdown': ingredient_breakdown,
            'limit_groups': [analysis.get('suitability', {}).get('avoidFor', "")] if analysis.get('suitability', {}).get('avoidFor') else [],
            'bottom_line': analysis.get('verdict', ""),
            'transparency_note': "AI-assisted analysis. Always verify with actual packaging.",
            'product': analysis.get('product', {}),
            'ingredients': ingredients_list,
            'score_breakdown': score_data['score_breakdown']
        }

    def _analyze_with_rules(self, ingredient_text: str, confidence: float, macros: Dict, food_type: str, user_goal: str) -> Dict[str, Any]:
        """
        Factual, neutral, frequency-based ingredient analysis.
        Generates exactly 7 sections as per new guidelines.
        """
        from .additive_service import identify_additives
        
        # Parse ingredients
        ingredients_list = self._extract_ingredients_from_text(ingredient_text)
        
        # Simple heuristic fallback if food_type is still default Solid
        if food_type == 'Solid' and ingredients_list:
            first_ing_lower = ingredients_list[0].lower()
            if any(liq in first_ing_lower for liq in ['water', 'milk', 'juice', 'puree', 'coffee', 'tea', 'beverage']):
                food_type = 'Liquid'
            elif any(semi in first_ing_lower for semi in ['cream', 'oil', 'butter', 'cheese', 'yogurt', 'spread']):
                food_type = 'Semi-solid'
        
        # Use scientific scorer (Fallback/Legacy mode for text without macros)
        score_data = self.scorer.calculate_score(ingredients_list, macros, food_type, user_goal)
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
        if score < 3.0 or nova_group == 4:
            frequency_verdict = "❌ Not suitable for daily consumption"
        elif score < 6.0 or nova_group == 3:
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
        # Analyze each ingredient with role, risk level, and layman's description
        ingredient_breakdown = []
        
        # Dictionary of common ingredients and their layman's descriptions (Detailed & Balanced)
        LAYMAN_DESCRIPTIONS = {
            'maltodextrin': "A highly processed carbohydrate used as a filler or thickener. While it helps with food texture and shelf life, it has a very high glycemic index, meaning it spikes blood sugar faster than table sugar. Frequent consumption can lead to weight gain and is problematic for diabetics.",
            'palm oil': "A vegetable fat widely used for its cheap cost and semi-solid texture. It is high in saturated fats, which can raise 'bad' LDL cholesterol and contribute to heart disease if eaten in large amounts. It is often preferred by manufacturers because it is incredibly shelf-stable and doesn't spoil easily.",
            'sugar': "A common sweetener used to enhance taste and provide quick energy. While safe in small amounts, modern packaged foods often contain excessive 'hidden' sugars. High intake is a primary driver of obesity, type 2 diabetes, and tooth decay. It offers 'empty calories' with no nutritional value.",
            'monosodium glutamate': "A flavor enhancer (MSG) that provides a savory 'umami' taste. Most food safety authorities consider it safe in moderation. However, some people are sensitive to it and may experience temporary headaches, sweating, or heart palpitations (often called 'MSG Symptom Complex').",
            'ins 621': "This is the code for Monosodium Glutamate (MSG). It is used to intensify the savory flavor of savory snacks and noodles. While it makes food taste much better, it is a marker of ultra-processed food and should be limited by those sensitive to additives.",
            'corn starch': "A refined starch used to thicken sauces or provide a crunchy texture to fried foods. It is a source of refined carbohydrates that digest quickly, causing rapid spikes in blood sugar. It lacks fiber and essential nutrients, providing mostly 'fast' energy.",
            'soy lecithin': "An emulsifier derived from soybeans that prevents water and oil from separating. It is generally considered safe and is even sold as a health supplement for brain health. In processed food, it is used in tiny amounts primarily for texture and to keep chocolate or spreads smooth.",
            'xanthan gum': "A powerful thickener and stabilizer created by fermenting sugar. It's used to give 'body' to sauces and gluten-free breads. It is generally safe, but in very large amounts, it can act as a laxative or cause bloating in people with sensitive digestion.",
            'guar gum': "A natural fiber extracted from guar beans. It is used to thicken and stabilize food textures. It is considered safe and can even have a prebiotic effect (feeding good gut bacteria), though excessive amounts might cause mild gas or bloating.",
            'hydrogenated vegetable oil': "A liquid oil that has been chemically turned into a solid fat. This process creates 'Trans Fats,' which are considered the most harmful type of fat because they raise bad cholesterol and lower good cholesterol, significantly increasing heart disease risk. Most health experts recommend avoiding this entirely.",
            'high fructose corn syrup': "A highly refined liquid sweetener made from corn. It is cheaper and sweeter than regular sugar. Research suggests that the body processes HFCS differently, potentially leading more quickly to liver fat, metabolic issues, and a higher risk of obesity compared to natural sweeteners.",
            'aspartame': "An artificial, zero-calorie sweetener often used in 'Diet' or 'Zero' drinks. While approved for use, it remains controversial; some studies suggest it may alter gut bacterial balance or affect appetite regulation. Not recommended as a 'healthier' long-term alternative to water.",
            'sodium benzoate': "A common preservative (E211) used to prevent the growth of bacteria and mold, especially in acidic drinks. While safe in small doses, when combined with Vitamin C, it can form benzene (a known carcinogen). Some studies also link it to increased hyperactivity in sensitive children.",
            'potassium sorbate': "A widely used preservative (E202) that prevents mold and yeast growth in everything from cheese to wine. It is one of the most thoroughly tested and safest preservatives available, with very low risk of side effects for the vast majority of people.",
            'citric acid': "A natural acid (E330) found in lemons and limes, used in food to control acidity and provide a sour tang. It acts as a mild preservative and helps prevent spoilage. While safe, excessive amounts in drinks can erode tooth enamel over time due to its acidity.",
            'maida': "This is ultra-refined wheat flour where the healthy bran and germ have been removed, leaving only the starchy endosperm. It has a very high glycemic index and contains almost no fiber, meaning it digests very quickly and can lead to rapid weight gain and insulin resistance.",
            'refined wheat flour': "Wheat flour that has been 'cleaned' of its fiber and nutrients. It provides mostly empty calories and quick energy. Unlike whole wheat, it doesn't keep you full for long and is a staple of highly processed, low-nutritive foods.",
            'ins 330': "This is the European code for Citric Acid. It is an acidity regulator used to balance pH and add a tart flavor. It is generally safe and naturally occurring in fruits, though it is often produced commercially through fermentation for use in packaged foods.",
            'acidity regulator': "Ingredients like citric acid or lactic acid used to control the pH level of food. They prevent bacteria from growing and help maintain a consistent flavor and color. They are necessary for food safety and generally safe, but should be consumed in moderation to protect tooth enamel.",
            'color': "Artificial dyes used to make food look more vibrant and appealing. While approved, some (like Tartrazine or Sunset Yellow) are linked to allergic reactions and hyperactivity in children. They serve no nutritional purpose and are strictly for visual marketing.",
            'flavour': "A mix of synthetic chemicals designed to mimic natural tastes like 'strawberry' or 'masala.' They make food highly palatable (and sometimes addictive), often masking the lack of real ingredients. They are safe for consumption but are a hallmark of ultra-processed food.",
            'ins 500': "This is Sodium Bicarbonate, commonly known as Baking Soda. It is used as a leavening agent to help dough or batter rise. It is generally safe, but contributes to the overall sodium (salt) content of the food.",
            'emulsifier': "Chemicals like lecithin or mono-diglycerides that help mix oil and water together so they don't separate. They are common in chocolates, ice creams, and breads to create a smooth, consistent texture. Generally safe, but some studies are investigating their long-term impact on gut lining health.",
        }

        for ing in ingredients_list:
            ing_lower = ing.lower()
            
            description = LAYMAN_DESCRIPTIONS.get(ing_lower)
            
            # If no direct match, check for partial matches or keywords
            if not description:
                if any(x in ing_lower for x in ['sugar', 'sucrose', 'glucose', 'syrup', 'fructose']):
                    description = LAYMAN_DESCRIPTIONS['sugar']
                elif any(x in ing_lower for x in ['oil', 'fat', 'vegetable fat']):
                    if 'palm' in ing_lower:
                        description = LAYMAN_DESCRIPTIONS['palm oil']
                    elif 'hydrogenated' in ing_lower:
                        description = LAYMAN_DESCRIPTIONS['hydrogenated vegetable oil']
                    else:
                        description = "Added fat used to improve texture and extend shelf life. This particular fat should be checked for its saturated fat content, as high intake can impact heart health."
                elif any(x in ing_lower for x in ['ins 330', 'e330', 'citric acid']):
                    description = LAYMAN_DESCRIPTIONS['citric acid']
                elif 'acidity regulator' in ing_lower:
                    description = LAYMAN_DESCRIPTIONS['acidity regulator']
                elif any(x in ing_lower for x in ['ins', 'e-']):
                    description = "A food additive (like a preservative, color, or stabilizer) used to keep food safe, colorful, or consistent. While safety-tested, they are markers of factory-made food and should be consumed in moderation."
                elif any(x in ing_lower for x in ['starch', 'flour', 'maida']):
                    if 'maida' in ing_lower:
                        description = LAYMAN_DESCRIPTIONS['maida']
                    else:
                        description = LAYMAN_DESCRIPTIONS['refined wheat flour']
                elif 'preservative' in ing_lower:
                    description = "A chemical added to prevent food from spoiling due to bacteria or mold. While essential for keeping packaged food safe for long periods, fresh foods without these additives are generally better for long-term health."
                else:
                    description = "A common ingredient used in modern food production for texture, flavor stability, or shelf-life. Like most processed food components, it is best consumed as part of a balanced diet rather than as a staple."

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
            if any(bad in ing_lower for bad in ['artificial', 'refined', 'hydrogenated', 'high fructose', 'msg', 'tartrazine', 'aspartame']):
                risk = "🔴"
            elif any(mod in ing_lower for mod in ['sugar', 'salt', 'preservative', 'color', 'flavor', 'modified', 'gum', 'emulsifier']):
                risk = "🟡"
            else:
                risk = "🟢"
            
            ingredient_breakdown.append({
                "name": ing,
                "role": role,
                "risk": risk,
                "description": description
            })
        
        # --- SECTION 5: Who Should Limit This ---
        limit_groups = []
        
        if has_added_sugar or nova_group >= 3:
            limit_groups.append("Children")
        
        if has_added_sugar:
            limit_groups.append("Diabetics")
        
        if nova_group == 4 or score < 4.0:
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
            'details': score_data.get('details', {}),
            'score_breakdown': score_data.get('score_breakdown', []),
            
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
                'nova_group': nova_group,
                'food_type': food_type
            },
            'ingredients': ingredients_list,
            'verdict': frequency_verdict,  # For backward compatibility
            'food_type': food_type
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
            
            # Check for delimiters at ALL levels (flattened)
            else:
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
                
                if is_delimiter:
                    item = "".join(current).strip()
                    if item:
                        ingredients.append(item)
                    current = []
                    i += skip_len - 1
                else:
                    current.append(char)
            i += 1
            
        item = "".join(current).strip()
        if item:
            ingredients.append(item)
            
        # 4. Post-processing & Cleaning
        final_list = []
        seen = set()
        
        # Clean and finalize
        for raw in ingredients:
            # Aggressive cleanup of leftover brackets and symbols
            clean = raw.replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('{', '').replace('}', '')
            clean = re.sub(r'[*•·—]', '', clean).strip()
            
            # Skip noise
            if not clean or len(clean) < 2: continue
            if clean in {'and', '&', 'contains', 'contains 2% or less', 'less than 2%'}: continue
            
            # Remove leading numbers/percents 
            clean = re.sub(r'^\d+(\.\d+)?%?\s*', '', clean).strip()
            
            # Remove "contains 2% or less of"
            clean = re.sub(r'^(contains|added|natural|artificial|permitted|organic)\s+', '', clean)
            
            if clean and clean not in seen:
                final_list.append(clean)
                seen.add(clean)
                
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


def analyze_product_from_text(text: str, macros: Dict = None, food_type: str = 'Solid', user_goal: str = 'Regular') -> Dict[str, Any]:
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
    analysis = analyzer.analyze_ingredients(text, 100.0, macros, food_type, user_goal)
    
    analysis['raw_ingredients'] = text
    return analysis
