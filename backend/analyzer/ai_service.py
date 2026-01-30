"""
AI-powered ingredient analysis service
Uses OpenAI GPT to analyze ingredient lists and provide health insights
"""
import os
import json
from typing import Dict, Any, Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class IngredientAnalyzer:
    """Analyzes ingredient lists and provides health insights"""
    
    def __init__(self):
        self.openai_client = None
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
    "product": {{
        "name": "Detected product name or 'Food Product'",
        "brand": "Detected brand or 'Unknown Brand'",
        "category": "Specific food category (e.g., 'Sauce', 'Snack', 'Beverage')"
    }},
    "verdict": "A clear, HONEST, and direct 2-4 sentence verdict about this product's healthiness. Don't sugarcoat - if it's unhealthy, say so plainly. Mention specific concerns.",
    "score": <number 1-10, where 10 is healthiest. Be strict: 7-10 = genuinely healthy, 4-6 = acceptable in moderation, 1-3 = concerning/unhealthy>,
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
    "confidence_note": "Any concerns about OCR quality, missing information, or analysis limitations"
}}

IMPORTANT GUIDELINES:
- **NO SENTENCES** in the "description" fields of `ingredientGroups`. Use comma-separated lists only.
- **NO LaTeX or Markdown math mode**. Never use `\(`, `\)`, `\[`, `\]`, or escape percentages like `\%`. Use plain text like "8%" or "8 percent".
- **NO ASTERISKS or FOOTNOTES**. Never use symbols like `*` or `†`.
- **NO REDUNDANT DESCRIPTORS**. Do not use words like "Permitted", "Added", or "Contains" within the ingredient names themselves. Just the name.
- Be HONEST and CRITICAL. Don't be diplomatic about unhealthy products.
- If it's junk food, call it junk food.
- Mention specific health impacts (diabetes risk, heart health, obesity, etc.).
- Consider the ENTIRE ingredient list, not just the problematic ones.
- The first ingredients matter most (they're present in highest quantities).
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
        analysis['success'] = True
        analysis['confidence'] = confidence
        analysis['method'] = 'ai'
        
        return analysis
    
    def _analyze_with_rules(self, ingredient_text: str, confidence: float) -> Dict[str, Any]:
        """Enhanced rule-based ingredient analysis"""
        from .additive_service import identify_additives, get_processing_score
        
        text_lower = ingredient_text.lower()
        additives = identify_additives(text_lower)
        processing = get_processing_score(text_lower)
        
        # Calculate Score
        score = 8 # Start with a baseline for "whole food"
        
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

        score = max(1, min(10, score))
        
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
