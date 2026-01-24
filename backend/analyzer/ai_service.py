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
                self.openai_client = OpenAI(api_key=api_key)
    
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
        
        prompt = f"""You are a food safety and nutrition expert. Analyze the following ingredient list and provide a comprehensive health assessment.

Ingredient List:
{ingredient_text}

OCR Confidence: {confidence}%

Please provide your analysis in the following JSON format:
{{
    "product": {{
        "name": "Detected product name or 'Unknown Product'",
        "brand": "Detected brand or 'Unknown Brand'",
        "category": "Food category"
    }},
    "verdict": "A clear, honest 2-3 sentence verdict about this product's healthiness",
    "score": <number 1-10, where 10 is healthiest>,
    "suitability": {{
        "goodFor": "Who should consume this (comma-separated)",
        "cautionFor": "Who should be cautious (comma-separated)",
        "avoidFor": "Who should avoid this (comma-separated)"
    }},
    "ingredientGroups": [
        {{
            "title": "Category name",
            "description": "What these ingredients do",
            "note": "Health impact or concern"
        }}
    ],
    "flags": [
        {{"icon": "🚩", "text": "Notable flag"}}
    ],
    "confidence_note": "Any concerns about OCR quality or missing information"
}}

Be honest and critical. If ingredients are unhealthy, say so clearly."""

        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a food safety expert providing honest ingredient analysis."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        analysis = json.loads(response.choices[0].message.content)
        analysis['success'] = True
        analysis['confidence'] = confidence
        analysis['method'] = 'ai'
        
        return analysis
    
    def _analyze_with_rules(self, ingredient_text: str, confidence: float) -> Dict[str, Any]:
        """Rule-based ingredient analysis (fallback when AI is not available)"""
        
        text_lower = ingredient_text.lower()
        
        # Detect concerning ingredients
        red_flags = []
        if any(term in text_lower for term in ['high fructose corn syrup', 'hfcs']):
            red_flags.append({'icon': '🚩', 'text': 'High Fructose Corn Syrup'})
        if any(term in text_lower for term in ['artificial color', 'red 40', 'yellow 5', 'blue 1']):
            red_flags.append({'icon': '🎨', 'text': 'Artificial Colors'})
        if any(term in text_lower for term in ['msg', 'monosodium glutamate']):
            red_flags.append({'icon': '⚠️', 'text': 'MSG Present'})
        if 'trans fat' in text_lower or 'partially hydrogenated' in text_lower:
            red_flags.append({'icon': '🚫', 'text': 'Trans Fats'})
        if any(term in text_lower for term in ['sodium benzoate', 'potassium sorbate', 'bha', 'bht']):
            red_flags.append({'icon': '🧪', 'text': 'Preservatives'})
        
        # Detect positive ingredients
        good_flags = []
        if 'organic' in text_lower:
            good_flags.append({'icon': '🌱', 'text': 'Organic Ingredients'})
        if 'whole grain' in text_lower or 'whole wheat' in text_lower:
            good_flags.append({'icon': '🌾', 'text': 'Whole Grains'})
        if any(term in text_lower for term in ['vitamin', 'mineral', 'fortified']):
            good_flags.append({'icon': '💊', 'text': 'Fortified'})
        
        # Calculate score based on flags
        score = 7  # Start neutral
        score -= len(red_flags) * 1.5
        score += len(good_flags) * 0.5
        score = max(1, min(10, score))
        
        # Generate verdict
        if score >= 8:
            verdict = "This product appears to have a clean ingredient list with minimal processing and few concerning additives."
        elif score >= 6:
            verdict = "This product has a moderate ingredient profile. Some processed ingredients present but generally acceptable for occasional consumption."
        else:
            verdict = "This product contains several concerning ingredients including artificial additives and highly processed components. Consider healthier alternatives."
        
        return {
            'success': True,
            'confidence': confidence,
            'method': 'rules',
            'product': {
                'name': 'Food Product',
                'brand': 'Unknown Brand',
                'category': 'Packaged Food',
            },
            'verdict': verdict,
            'score': round(score),
            'suitability': {
                'goodFor': 'General population (in moderation)',
                'cautionFor': 'Those with dietary restrictions, children',
                'avoidFor': 'People with specific allergies (check label)',
            },
            'ingredientGroups': [
                {
                    'title': 'Detected Ingredients',
                    'description': ingredient_text[:200] + ('...' if len(ingredient_text) > 200 else ''),
                    'note': f'Extracted with {confidence:.0f}% confidence',
                }
            ],
            'flags': red_flags + good_flags,
            'confidence_note': f'Analysis based on {confidence:.0f}% OCR confidence. For best results, ensure clear image quality.',
        }


def analyze_product_from_ocr(ocr_result) -> Dict[str, Any]:
    """
    Main function to analyze product from OCR result
    
    Args:
        ocr_result: OCRResult object from ocr_service
    
    Returns:
        Dictionary with complete analysis
    """
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
                'Check that the image is not upside down or sideways',
            ],
            'extracted_text': ocr_result.text[:200] if ocr_result.text else None,
            'confidence': ocr_result.confidence,
            'quality_score': ocr_result.quality_score,
        }
    
    # Analyze ingredients
    analysis = analyzer.analyze_ingredients(
        ocr_result.text,
        ocr_result.quality_score
    )
    
    # Add OCR metadata
    analysis['ocr_metadata'] = {
        'method': ocr_result.method,
        'confidence': ocr_result.confidence,
        'quality_score': ocr_result.quality_score,
        'text_length': len(ocr_result.text),
    }
    
    return analysis
