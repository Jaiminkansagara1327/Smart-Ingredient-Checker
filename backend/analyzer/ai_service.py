"""
AI-powered ingredient analysis service
Uses OpenAI GPT to analyze ingredient lists and provide health insights
Combined with scientific scoring based on NOVA/Nutri-Score methodology
"""
import os
import json
from typing import Dict, Any, Optional
from .ingredient_scorer import IngredientScorer
from .off_service import search_product_by_name

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
            model="gpt-4-turbo-preview",
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
        """Enhanced rule-based ingredient analysis using scientific scorer"""
        from .additive_service import identify_additives, get_processing_score
        
        # Parse ingredients from the text
        ingredients_list = self._extract_ingredients_from_text(ingredient_text)
        
        # Use our scientific scorer for the actual score
        score_data = self.scorer.calculate_score(ingredients_list)
        
        # Get additional context from additive service for descriptions
        additives = identify_additives(ingredient_text.lower())
        processing = get_processing_score(ingredient_text.lower())
        
        # Create verdict based on score
        score = score_data['score']
        if score >= 85:
            verdict = f"Excellent choice! This product contains {score_data['whole_food_ratio']}% whole food ingredients and minimal processing. A genuinely healthy option for your diet."
        elif score >= 70:
            verdict = f"Good quality product with {score_data['whole_food_ratio']}% whole food ingredients. {processing} with acceptable ingredients."
        elif score >= 55:
            verdict = f"Average product. {processing}. Contains some processed ingredients - consume in moderation."
        elif score >= 40:
            verdict = f"Heavily processed with {len(additives)} detected additives. {processing}. Limit consumption."
        else:
            verdict = f"Ultra-processed junk food. Contains many artificial ingredients. Consider a more natural alternative."

        # Map ingredients to groups
        ingredient_groups = []
        
        # Add score breakdown
        if score_data['score_breakdown']:
            breakdown_desc = ", ".join([f"{item['description']} ({item['points']:+d})" for item in score_data['score_breakdown'][:3]])
            ingredient_groups.append({
                "title": "Score Breakdown",
                "description": breakdown_desc,
                "note": f"NOVA Group {score_data['nova_group']}: {['Unprocessed', 'Processed ingredients', 'Processed food', 'Ultra-processed'][score_data['nova_group']-1]}"
            })
        
        if additives:
            ingredient_groups.append({
                "title": "Detected Additives",
                "description": ", ".join([a['name'] for a in additives[:5]]),
                "note": "Specifically checked against food safety databases."
            })

        return {
            'success': True,
            'confidence': confidence,
            'method': 'scientific_scorer',
            'product': {
                'name': 'Detected Product',
                'brand': 'Unknown',
                'category': 'Packaged Food',
            },
            'verdict': verdict,
            'score': score,
            'nova_group': score_data['nova_group'],
            'whole_food_percentage': score_data['whole_food_ratio'],
            'suitability': {
                'goodFor': 'General fitness' if score >= 70 else 'Limited use only',
                'cautionFor': 'Everyone' if score < 40 else 'Sensitive individuals',
                'avoidFor': 'Regular consumption' if score < 55 else 'Those avoiding processed foods',
            },
            'ingredientGroups': ingredient_groups,
            'ingredients': ingredients_list,
            'flags': []
        }
    
    def _extract_ingredients_from_text(self, text: str) -> list:
        """Extract individual ingredients from text"""
        if ',' in text:
            return [i.strip() for i in text.split(',') if i.strip()]
        return [i.strip() for i in text.split('\n') if i.strip()]


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


def analyze_product_from_text(text: str) -> Dict[str, Any]:
    """
    Main entry point for analyzing ingredients from text string
    """
    analyzer = IngredientAnalyzer()
    
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
