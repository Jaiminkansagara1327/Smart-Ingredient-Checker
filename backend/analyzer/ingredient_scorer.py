"""
Ingredient Scoring Engine - Advanced Multi-Criteria Analysis
Methodology inspired by EWG Food Scores:
1. Nutrition (Weight: 50%) - Based on ingredient quality mapping
2. Ingredient Concerns (Weight: 30%) - Based on additive toxicology and health markers
3. Processing (Weight: 20%) - Based on NOVA classification extent
"""
import re
from typing import List, Dict, Tuple

class IngredientScorer:
    # -------------------------------------------------------------------------
    # 1. NUTRITION DATA (Sugars, Fats, Sodium, Nutrients)
    # -------------------------------------------------------------------------
    ADDED_SUGARS = {
        'sugar', 'sucrose', 'high fructose corn syrup', 'hfcs', 'corn syrup',
        'cane sugar', 'brown sugar', 'dextrose', 'maltodextrin', 'glucose',
        'fructose', 'invert sugar', 'syrup', 'molasses', 'honey', 'agave',
        'coconut sugar', 'caramel', 'maltose', 'treacle', 'golden syrup'
    }

    UNHEALTHY_FATS = {
        'palm oil', 'palm kernel oil', 'shortening', 'margarine',
        'hydrogenated', 'partially hydrogenated', 'vegetable fat', 'vanaspati',
        'dalda', 'interesterified', 'cottonseed oil', 'corn oil', 'soybean oil'
    }

    SODIUM_SOURCES = {
        'salt', 'sodium', 'monosodium', 'baking soda', 'baking powder',
        'disodium', 'trisodium', 'nitrite', 'nitrate', 'brine'
    }
    
    # Beneficial whole food ingredients (Merged & Simplified for Nutrition Score)
    WHOLE_FOODS = {
        'oats', 'quinoa', 'barley', 'rice', 'wheat', 'corn', 'millet', 'sorghum', # Grains
        'almonds', 'walnuts', 'cashews', 'peanuts', 'seeds', 'nuts', # Nuts/Seeds
        'milk', 'yogurt', 'curd', 'cheese', 'paneer', 'butter', 'ghee', # Dairy
        'fruit', 'berry', 'apple', 'banana', 'mango', 'tomato', # Fruits
        'vegetable', 'spinach', 'carrot', 'pea', 'bean', 'lentil', 'dal', 'gram', # Veg/Legumes
        'chicken', 'egg', 'fish', 'meat', # Proteins
        'cocoa', 'cacao', 'coffee', 'tea', 'water', 'spices', 'herbs' # Others
    }

    # -------------------------------------------------------------------------
    # 2. INGREDIENT CONCERNS (Additives & Toxicity)
    # -------------------------------------------------------------------------
    # Map specific concerns to severity (0-10 scale, 10 being worst)
    ADDITIVE_CONCERNS = {
        # High Concern (Carcinogens, Endocrine Disruptors, etc.)
        'aspartame': 9, 'acesulfame': 8, 'saccharin': 8, 'sucralose': 7,
        'bha': 9, 'bht': 9, 'tbhq': 8, 'sodium benzoate': 7, 'potassium benzoate': 7,
        'nitrite': 10, 'nitrate': 9, 'bromate': 10, 'propyl gallate': 8,
        'tartrazine': 8, 'sunset yellow': 8, 'allura red': 8, 'brilliant blue': 7,
        'msg': 6, 'monosodium glutamate': 6, 'artificial color': 7, 'artificial flavor': 6,
        'carrageenan': 6, 'dioxygen': 0, # inert
        
        # Medium Concern (Allergens, Intolerance, processing aids)
        'gum': 3, 'lecithin': 2, 'phosphate': 4, 'sorbate': 3,
        'benzoate': 5, 'sulfite': 5, 'sulphite': 5, 'dextrin': 3,
        'maltodextrin': 4, 'modified starch': 4, 'yeast extract': 4,
        'flavor enhancer': 5, 'emulsifier': 3, 'stabilizer': 3,
        'thickener': 2, 'acidity regulator': 1, 'anticaking': 2,
        'preservative': 5, 'artificial': 5, 'synthetic': 5,
        'nature identical': 4
    }

    # -------------------------------------------------------------------------
    # 3. PROCESSING INDICATORS (NOVA)
    # -------------------------------------------------------------------------
    ULTRA_PROCESSED_INDICATORS = [
        'high fructose corn syrup', 'hydrogenated', 'hydrolysed',
        'isolate', 'modified', 'artificial', 'ester', 'fractionated',
        'bleached', 'refined', 'reconstituted', 'flavoring', 'flavouring'
    ]

    def calculate_score(self, ingredients_list: List[str]) -> Dict:
        """
        Calculate Weighted Score (Ingredients Only):
        - Ingredient Quality & Safety: 70% (Additives, Sugar, Oils vs Whole Foods)
        - Processing: 30% (NOVA Classification)
        """
        if not ingredients_list:
            return {'score': 0, 'score_breakdown': [], 'nova_group': 4}

        # 1. Ingredient Quality & Safety Score (0-100)
        # Merges Additive Safety + Material Quality (Sugar/Oil vs Whole Food)
        quality_score, quality_notes = self._calculate_quality_score(ingredients_list)
        
        # 2. Processing Score (0-100)
        processing_score, processing_notes, nova_group = self._calculate_processing_score(ingredients_list)

        # Weighted Calculation
        # Quality (70%) + Processing (30%)
        # Note: Processing score is already low for NOVA 4, but we need to ensure the final score reflects the health impact.
        base_score = (quality_score * 0.70) + (processing_score * 0.30)
        
        final_score = base_score

        # DYNAMIC CAPS & SCALING for Processed Foods
        # Fix: Prevent all NOVA 4 products getting exactly 35. 
        # Apply a heavy scaling factor instead of a flat cap.
        if nova_group == 4:
            # Ultra-processed foods are discouraged. 
            # Scale the score down to ensure it stays in the "Poor" to "Average" range (0-45).
            # A "clean" ultra-processed item (rare) might hit 40-45. 
            # A "dirty" one will drop to 10-20.
            final_score = base_score * 0.45 
            processing_notes.append({'description': "Score heavily reduced (Ultra-Processed)", 'points': 0})
            
        elif nova_group == 3:
            # Processed foods. Scale down slightly to cap around 70-75 max.
            final_score = base_score * 0.75

        final_score = round(max(0, min(100, final_score)))

        # Combine notes
        all_notes = quality_notes + processing_notes
        
        return {
            'score': final_score,
            'score_breakdown': all_notes,
            'nova_group': nova_group,
            'details': {
                'quality_score': quality_score, # Replaces concern/nutrition
                'processing_score': processing_score
            }
        }

    def _calculate_quality_score(self, ingredients: List[str]) -> Tuple[float, List[Dict]]:
        """
        Evaluates Ingredient Quality (Additives - Sugar - Oil + Whole Foods).
        Starts at 100.
        """
        score = 100.0
        notes = []
        
        for i, ing in enumerate(ingredients):
            ing_lower = ing.lower()
            
            # 1. Check Additives (Safety)
            matched_concern = False
            for additive, severity in self.ADDITIVE_CONCERNS.items():
                if additive in ing_lower:
                    penalty = severity * 3 # Higher penalty (Max 30 pts per bad additive)
                    score -= penalty
                    matched_concern = True
                    notes.append({
                        'description': f"Contains {ing} (Concerns found)",
                        'points': -penalty
                    })
                    break 
            
            # E-numbers catch-all
            if not matched_concern and ('ins ' in ing_lower or re.search(r'\be\d{3,4}', ing_lower)):
                score -= 10
                notes.append({'description': f"Artificial additive ({ing})", 'points': -10})

            # 2. Check Low Quality Ingredients (Sugar/Refined Oil) - Weighted by order
            # Only checking top 5 ingredients for major impact
            if i < 5:
                # Sugar penalty
                if any(s in ing_lower for s in self.ADDED_SUGARS):
                    # Only penalize if it's NOT 'sugar free'
                    if 'sugar free' not in ing_lower:
                        penalty = 15 if i == 0 else 10
                        score -= penalty
                        notes.append({'description': f"High added sugar ({ing})", 'points': -penalty})
                
                # Unhealthy Fat penalty
                elif any(f in ing_lower for f in self.UNHEALTHY_FATS):
                    penalty = 15 if i == 0 else 10
                    score -= penalty
                    notes.append({'description': f"Unhealthy fat ({ing})", 'points': -penalty})

        # 3. Whole Food Bonus
        whole_food_count = sum(1 for ing in ingredients if self._is_whole_food(ing.lower()))
        if whole_food_count > 0:
            bonus = min(20, whole_food_count * 5) # Max 20 pts bonus
            score += bonus

        return max(0, min(100, score)), notes

    def _calculate_processing_score(self, ingredients: List[str]) -> Tuple[float, List[Dict], int]:
        """
        NOVA-based processing score.
        Returns (Score 0-100, Notes, NOVA Group Int)
        """
        score = 100
        notes = []
        
        # Detect Ultra-Processed Markers
        markers = 0
        for ing in ingredients:
            ing_lower = ing.lower()
            if any(m in ing_lower for m in self.ULTRA_PROCESSED_INDICATORS) or \
               any(m in ing_lower for m in self.ADDITIVE_CONCERNS):
                markers += 1

        # Determine NOVA Group & Base Score
        total = len(ingredients)
        marker_ratio = markers / total if total > 0 else 1
        
        nova_group = 1
        
        if markers == 0 and total > 1:
            # Check if likely NOVA 2 (Culinary ingredients like Oil, Sugar, Salt only)
            if all(any(x in ing.lower() for x in self.ADDED_SUGARS | self.SODIUM_SOURCES | self.UNHEALTHY_FATS | {'oil', 'butter', 'starch'}) for ing in ingredients):
                nova_group = 2
                score = 80
            else:
                nova_group = 1
                score = 100
                notes.append({'description': "Minimally processed", 'points': 0})
                
        elif markers >= 1 or (markers >= 5 and marker_ratio > 0.3):
             # Deep processing
             if markers >= 2 or marker_ratio > 0.2:
                 nova_group = 4
                 score = 40
                 notes.append({'description': "Ultra-processed product", 'points': -20})
             else:
                 nova_group = 3
                 score = 60
                 notes.append({'description': "Processed product", 'points': -10})
                 
        # Fine-tune based on additive count
        if markers > 3:
            penalty = (markers - 3) * 5
            score -= penalty
            
        return max(0, min(100, score)), notes, nova_group

    def _is_whole_food(self, ingredient: str) -> bool:
        """Robust whole food check utilizing word boundaries"""
        # Skip if 'artificial' or 'flavor' is present
        if any(x in ingredient for x in ['artificial', 'flavor', 'flavour', 'synthetic']):
            return False
            
        for wf in self.WHOLE_FOODS:
            if re.search(rf'\b{re.escape(wf)}\w*', ingredient): # Matches "oats", "oatmeal", "oat"
                return True
        return False
