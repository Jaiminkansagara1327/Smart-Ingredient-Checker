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
            ingredient_text: Raw ingredient text from OCR
            confidence: OCR confidence score (0-100)
        
        Returns:
            Dictionary with analysis results
        """
        # If confidence is too low, return low-confidence response
        if confidence < 40:
            return self._low_confidence_response(ingredient_text, confidence)
        
        # Try AI analysis if available
        if self.openai_client:
            try:
                return self._analyze_with_ai(ingredient_text, confidence)
            except Exception as e:
                print(f"AI analysis error: {e}")
                # Fall back to rule-based analysis
        
        # Use rule-based analysis as fallback
        return self._analyze_with_rules(ingredient_text, confidence)
    
    def _low_confidence_response(self, text: str, confidence: float) -> Dict[str, Any]:
        """Return response for low-confidence OCR results"""
        return {
            'success': False,
            'confidence': confidence,
            'error': 'LOW_CONFIDENCE',
            'message': 'Unable to clearly read the ingredients from this image.',
            'suggestions': [
                'Ensure the ingredient list is clearly visible and in focus',
                'Make sure there is good lighting on the label',
                'Try to capture the image straight-on (not at an angle)',
                'Ensure the text is not blurry or too small',
            ],
            'partial_text': text[:200] if text else None,
        }
    
    def _analyze_with_ai(self, ingredient_text: str, confidence: float) -> Dict[str, Any]:
        """Use OpenAI GPT to analyze ingredients"""
        
        prompt = f"""You are a food safety and nutrition expert with expertise in ingredient analysis, food science, and public health. Analyze the following ingredient list and provide a comprehensive, honest, and actionable health assessment.

Ingredient List:
{ingredient_text}

OCR Confidence: {confidence}%

Please provide your analysis in the following JSON format:
{{
    "is_valid_ingredient_list": <boolean - true ONLY if this is actually a food ingredient list. False if it's random text, sentences, conversations, or anything that's NOT ingredients>,
    "validation_message": "If is_valid_ingredient_list is false, explain what's wrong (e.g., 'This appears to be random text, not food ingredients', 'This looks like a conversation or description, not an ingredient list'). Otherwise leave empty.",
    "product": {{
        "name": "Detected product name or 'Food Product'",
        "brand": "Detected brand or 'Unknown Brand'",
        "category": "Specific food category (e.g., 'Sauce', 'Snack', 'Beverage')"
    }},
    "verdict": "A clear, HONEST, and direct 2-4 sentence verdict about this product's healthiness. Don't sugarcoat - if it's unhealthy, say so plainly. Mention specific concerns.",
    "score": <number 1-100, where 100 is healthiest. BE STRICT and use the SCORING RULES below>,
    "suitability": {{
        "goodFor": "Be specific about demographics/conditions (e.g., 'Active adults seeking quick energy', 'Those without dietary restrictions')",
        "cautionFor": "List specific groups with clear reasons (e.g., 'Diabetics (high sugar content)', 'Those watching sodium intake')",
        "avoidFor": "Be direct about who should not consume this (e.g., 'Children under 5 (artificial additives)', 'Those with wheat allergies')"
    }},
    "ingredientGroups": [
        {{
            "title": "Main Ingredients",
            "description": "A comma-separated list of the first 5-7 ingredients ONLY. Do not use full sentences or conversational lead-ins (e.g., 'It contains...', 'Ingredients include...').",
            "note": "Health impact: [Specific impact on health, nutrition, or concerns]"
        }},
        {{
            "title": "Additives & Preservatives",
            "description": "A comma-separated list of all artificial colors, flavors, and preservatives ONLY. If none found, say 'None detected'.",
            "note": "Why they're used and any health concerns"
        }},
        {{
            "title": "Sugars & Sweeteners" (only if relevant),
            "description": "A comma-separated list of all forms of sugar/sweeteners found ONLY.",
            "note": "Total impact on blood sugar and health"
        }},
        {{
            "title": "Notable Concerns" (only if any exist),
            "description": "A comma-separated list of problematic ingredients or combinations ONLY.",
            "note": "Specific health risks or reasons for concern"
        }}
    ],
    "flags": [
        {{"icon": "🚩", "text": "High in added sugars"}},
        {{"icon": "⚠️", "text": "Contains artificial colors"}},
        {{"icon": "🧂", "text": "High sodium content"}},
        {{"icon": "🌱", "text": "Contains whole grains"}} (use positive flags too!)
    ],
    "ingredients": ["Clean, properly formatted list of ALL detected ingredients as separate strings"],
    "confidence_note": "Any concerns about OCR quality, missing information, or analysis limitations"
}}

CRITICAL - INPUT VALIDATION (MUST BE FIRST CHECK):
- **YOU MUST REJECT** any input that is NOT a food ingredient list. Be EXTREMELY STRICT.
- **ALL-OR-NOTHING RULE**: Even ONE non-food word/phrase means REJECT. Do not be lenient.

- Set `is_valid_ingredient_list` to **FALSE** for:
  ❌ **Mixed content** - REJECT if it contains ANY mix of real ingredients + random text (e.g., "Flour, Sugar, I am a student, Eggs")
  ❌ **Conversational/biographical text** (e.g., "I am a student", "I work on...", "My name is...", "Computer Science")
  ❌ **Complete sentences** with subjects and verbs about people, places, or events
  ❌ **Job titles/roles** (e.g., "developer", "engineer", "student", "backend", "full-stack")
  ❌ **Technical terms non-food** (e.g., "API", "authentication", "backend systems", "handling")
  ❌ **Random words** without context (e.g., "hello world", "test test", "lorem ipsum")
  ❌ **Numbers only** (e.g., "123456", "1 2 3 4 5")
  ❌ **Personal information** (names, addresses, job descriptions, hobbies, interests)
  ❌ **Questions or commands** (e.g., "How are you?", "Please analyze this")
  ❌ **Generic text snippets** that don't relate to food at all
  
- Set `is_valid_ingredient_list` to **TRUE** ONLY if:
  ✅ **EVERY SINGLE WORD** is either:
     - A recognizable food ingredient name (e.g., "Flour", "Water", "Sugar", "Eggs", "Milk")
     - A chemical/additive name found in food (e.g., "E471", "Sodium Benzoate", "Ascorbic Acid", "INS 471")
     - A common food descriptor (e.g., "Wheat", "Organic", "Refined", "Whole")
     - Punctuation or formatting (commas, parentheses, percentages for ingredients like "8%")
  ✅ It follows typical ingredient list patterns (comma-separated or line-separated food items)
  ✅ **100% of the content is food-related** - NO exceptions

- **IMPORTANT**: If you see words like "student", "developer", "work", "interested", "building", "handling", "backend", "API", "authentication" - these are NOT food terms. REJECT immediately.
- When in doubt, **REJECT IT**. Better to reject borderline cases than analyze non-food text.
- If rejecting, provide a clear `validation_message` explaining why (e.g., "This contains personal/biographical information mixed with ingredient names, not a pure ingredient list").

IMPORTANT GUIDELINES:
- **EXTRACT ALL INGREDIENTS** into the `ingredients` array. If the input is a single block of text or separated by line breaks without commas, identify and extract the individual ingredients yourself.
- **NO SENTENCES** in the "description" fields of `ingredientGroups`. Use comma-separated lists only.
- **NO LaTeX or Markdown math mode**. Never use `\\(`, `\\)`, `\\[`, `\\]`, or escape percentages like `\\%`. Use plain text like "8%" or "8 percent".
- **NO ASTERISKS or FOOTNOTES**. Never use symbols like `*` or `†`.
- **NO REDUNDANT DESCRIPTORS**. Do not use words like "Permitted", "Added", "Contains", or "Or" within the ingredient names themselves. Just the name.

**NEW BALANCED SCORING SYSTEM (1-100 Scale)**:

**STEP 1: Categorize the Product**
Analyze the ingredient list and determine the primary category:

A. **WHOLE FOODS / MINIMALLY PROCESSED** - Base Score: 85-100
   - Recognizable whole ingredients (fruits, vegetables, grains, legumes, nuts, seeds)
   - Simple processing (grinding, cooking, fermenting)
   - Minimal or no additives
   - Examples: "Oats, Almonds, Honey" or "Tomatoes, Olive Oil, Garlic, Basil, Salt"
   
B. **PROCESSED BUT ACCEPTABLE** - Base Score: 60-84
   - Combination of whole foods + some processing
   - Limited additives (mostly natural preservatives, emulsifiers from natural sources)
   - May contain some added sugar/salt but in moderation
   - Examples: "Whole Wheat Flour, Water, Yeast, Salt, Olive Oil" or "Milk, Sugar, Cocoa, Vanilla Extract"

C. **HEAVILY PROCESSED** - Base Score: 30-59
   - Many refined ingredients and additives
   - Multiple artificial colors, flavors, or preservatives
   - High in added sugars, sodium, or unhealthy fats
   - Examples: "Enriched Flour, HFCS, Hydrogenated Oils, Artificial Flavors, Colors"

D. **ULTRA-PROCESSED JUNK** - Base Score: 0-29
   - Primarily artificial/synthetic ingredients
   - Long list of unrecognizable chemicals
   - Multiple harmful ingredients (trans fats, excessive sodium, artificial sweeteners)
   - Examples: Products with 20+ ingredients, mostly E-numbers and chemicals

**STEP 2: Adjust Score Based on Specific Factors**

**POSITIVE ADJUSTMENTS (Add points):**
- Organic/Whole grain ingredients: +5 to +10 points
- High fiber content indicated: +5 points  
- Healthy fats (olive oil, avocado, nuts): +5 points
- Natural preservatives only (vinegar, lemon juice, salt): +5 points
- Short ingredient list (5 or fewer whole foods): +10 points
- No added sugars: +5 points
- Low/no sodium: +5 points

**NEGATIVE ADJUSTMENTS (Deduct points):**
- **Artificial additives**: -3 points EACH (colors, flavors, preservatives like BHA/BHT)
- **High Fructose Corn Syrup or Aspartame**: -15 points
- **Excessive added sugar** (sugar in top 3 ingredients): -10 points
- **Hydrogenated/Trans fats**: -20 points
- **Palm oil or highly refined oils**: -8 points
- **Excessive sodium** (sodium in top 3): -10 points
- **Nitrates/Nitrites**: -10 points
- **Multiple E-numbers** (3+): -5 points per additional E-number after 3

**STEP 3: Final Score Range Guidelines**
- **90-100**: Exceptionally healthy - whole foods, minimal processing
- **75-89**: Healthy - good ingredients with minor processing
- **60-74**: Acceptable - moderately processed but not harmful
- **40-59**: Concerning - heavily processed, limit consumption
- **20-39**: Unhealthy - ultra-processed, avoid regularly
- **0-19**: Harmful - primarily artificial, do not consume

**CRITICAL RULES:**
1. **DO NOT** penalize products just for having more than 3-4 ingredients if they're all natural/whole foods
2. **DO** give high scores (85-95) to products like "Whole Wheat Flour, Water, Salt, Yeast" 
3. **DO** give high scores (80-90) to simple natural products like "Oats, Almonds, Honey, Cinnamon"
4. **BE FAIR**: Distinguish between "many ingredients because it's a complex recipe" vs "many ingredients because it's ultra-processed"
5. Natural ingredients like fruits, vegetables, grains, legumes, nuts, dairy, eggs, meat should NEVER lower the score
6. Processing methods matter: "Crushed Tomatoes" is fine, "Tomato Flavoring (Artificial)" is not
- Look for: artificial additives, high fructose corn syrup, excessive sodium, trans fats, artificial colors/flavors.
- Give credit for: whole food ingredients, minimal processing, natural preservatives, beneficial nutrients.
- Be specific in suitability recommendations - use medical/dietary conditions when relevant.
"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a food safety expert providing honest, comprehensive ingredient analysis. Be direct and specific about health impacts."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent, factual responses
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        # Extract ingredients list from AI response
        ingredients_list = analysis.get('ingredients', [])
        
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
        """Enhanced rule-based ingredient analysis"""
        from .additive_service import identify_additives, get_processing_score
        
        text_lower = ingredient_text.lower()
        additives = identify_additives(text_lower)
        processing = get_processing_score(text_lower)
        
        # Calculate Score
        # Extract ingredients and use scientific scorer
        ingredients_list = self._extract_ingredients_from_text(ingredient_text)
        score_data = self.scorer.calculate_score(ingredients_list)
        score = score_data["score"]  # Use 0-100 scale
        
        flags = []
        for a in additives:
            if a['risk'] == "Avoid":
                score -= 2
                flags.append({"icon": "🚫", "text": a['name']})
            elif a['risk'] == "Caution":
                score -= 1
                flags.append({"icon": "⚠️", "text": a['name']})
        
        if "sugar" in text_lower or "syrup" in text_lower:
            score -= 1
            flags.append({"icon": "🧂", "text": "High Sugar/Sweeteners"})
            
        if "organic" in text_lower:
            score += 1
            flags.append({"icon": "🌱", "text": "Organic"})

        
        # Create professional verdict
        if score >= 8:
            verdict = f"This product is {processing}. It contains mostly natural ingredients and is a healthy choice for your diet."
        elif score >= 5:
            verdict = f"This product is {processing}. It contains some concerning additives and should be consumed in moderation."
        else:
            verdict = f"This product is {processing}. It has high levels of additives or heavy processing. Consider a more natural alternative."

        # Map additives to ingredient groups
        ingredient_groups = [
            {
                "title": "Processing Level",
                "description": processing,
                "note": "Based on the complexity and type of ingredients found."
            }
        ]
        
        if additives:
            ingredient_groups.append({
                "title": "Detected Additives",
                "description": ", ".join([a['name'] for a in additives]),
                "note": "Specifically checked against food safety databases."
            })

        return {
            'success': True,
            'confidence': confidence,
            'method': 'rules_v2',
            'product': {
                'name': 'Detected Product',
                'brand': 'Unknown',
                'category': 'Packaged Food',
            },
            'verdict': verdict,
            'score': round(score),
            'suitability': {
                'goodFor': 'General fitness, balanced diets',
                'cautionFor': 'Sensitive individuals, children',
                'avoidFor': 'Those avoiding processed additives',
            },
            'ingredientGroups': ingredient_groups,
            'flags': flags,
            'confidence_note': f"Rule-based analysis (v2) based on {confidence:.0f}% confidence.",
        }



    def _extract_ingredients_from_text(self, text: str) -> list:
        """Extract individual ingredients from text"""
        if ',' in text:
            return [i.strip() for i in text.split(',') if i.strip()]
        return [i.strip() for i in text.split('\n') if i.strip()]

def analyze_product_from_ocr(ocr_result) -> Dict[str, Any]:
    """
    Hybrid analysis: Database Search + AI/Rule Analysis
    """
    from .off_service import search_product_by_name
    analyzer = IngredientAnalyzer()
    
    # Check if ingredients were detected
    if not ocr_result.has_ingredients:
        return {
            'success': False,
            'error': 'NO_INGREDIENTS_DETECTED',
            'message': 'No ingredient information detected in the image.',
            'suggestions': [
                'Make sure you are photographing the ingredient list section',
                'Ensure the ingredients text is clearly visible',
                'Try zooming in on the ingredient label',
            ],
            'extracted_text': ocr_result.text[:200] if ocr_result.text else None,
            'confidence': ocr_result.confidence,
            'quality_score': ocr_result.quality_score,
        }
    
    # 1. Try to find product in real scientific database
    # Only try to guess if the source isn't manual entry (where user should provide name)
    db_product = None
    if ocr_result.method != 'manual_entry':
        # Extract a potential name from the first few words of OCR
        # But ignore common start ingredients like "Water", "Sugar", etc.
        potential_name = ocr_result.text.split(',')[0].strip()[:50].lower()
        ignore_common = ['water', 'sugar', 'salt', 'milk', 'wheat', 'flour']
        
        if potential_name and not any(common in potential_name for common in ignore_common):
            db_product = search_product_by_name(potential_name)
    
    # 2. Analyze ingredients (AI or Rules)
    analysis = analyzer.analyze_ingredients(
        ocr_result.text,
        ocr_result.quality_score
    )
    
    # 3. Merge Database data with Analysis
    if db_product:
        analysis['product']['name'] = db_product['name']
        analysis['product']['brand'] = db_product['brand']
        analysis['product']['database_match'] = True
        analysis['product']['nutriscore'] = db_product['nutriscore']
        analysis['product']['nova_group'] = db_product['nova_group']
        if db_product['image']:
            analysis['product_image_url'] = db_product['image']
    
    # Add OCR metadata
    analysis['ocr_metadata'] = {
        'method': ocr_result.method,
        'confidence': ocr_result.confidence,
        'quality_score': ocr_result.quality_score,
        'text_length': len(ocr_result.text),
    }
    
    analysis['raw_ingredients'] = ocr_result.text
    return analysis
