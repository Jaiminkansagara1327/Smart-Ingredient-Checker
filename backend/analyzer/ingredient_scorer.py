"""
Ingredient Scoring Engine - Advanced Multi-Criteria Analysis
Universal Formula Implementation:
1. Classifies by Food Type (Solid, Semi-Solid, Liquid)
2. Normalizes to 100g (Solid/Semi) or 100ml (Liquid)
3. Evaluates dimensionless risk ratios based on target Diet Goals
"""
import re
from typing import List, Dict, Tuple, Any

class IngredientScorer:
    
    # -------------------------------------------------------------------------
    # 1. IDENTIFIERS (Additives, processing, basic whole foods)
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

    REFINED_CARBS = {
        'maida', 'refined wheat flour', 'white flour', 'refined flour', 'corn starch',
        'tapioca starch', 'potato starch', 'starch', 'maltodextrin'
    }

    SODIUM_SOURCES = {
        'salt', 'sodium', 'monosodium', 'baking soda', 'baking powder',
        'disodium', 'trisodium', 'nitrite', 'nitrate', 'brine'
    }
    
    WHOLE_FOODS = {
        'oats', 'quinoa', 'barley', 'rice', 'wheat', 'corn', 'millet', 'sorghum',
        'almonds', 'walnuts', 'cashews', 'peanuts', 'seeds', 'nuts',
        'milk', 'yogurt', 'curd', 'cheese', 'paneer', 'butter', 'ghee',
        'fruit', 'berry', 'apple', 'banana', 'mango', 'tomato',
        'vegetable', 'spinach', 'carrot', 'pea', 'bean', 'lentil', 'dal', 'gram',
        'chicken', 'egg', 'fish', 'meat',
        'cocoa', 'cacao', 'coffee', 'tea', 'water', 'spices', 'herbs'
    }

    ADDITIVE_CONCERNS = {
        # High Concern
        'aspartame': 9, 'acesulfame': 8, 'saccharin': 8, 'sucralose': 7,
        'bha': 9, 'bht': 9, 'tbhq': 8, 'sodium benzoate': 7, 'potassium benzoate': 7,
        'nitrite': 10, 'nitrate': 9, 'bromate': 10, 'propyl gallate': 8,
        'tartrazine': 8, 'sunset yellow': 8, 'allura red': 8, 'brilliant blue': 7,
        'msg': 6, 'monosodium glutamate': 6, 'artificial color': 7, 'artificial flavor': 6,
        'carrageenan': 6,
        # Medium Concern
        'gum': 3, 'lecithin': 2, 'phosphate': 4, 'sorbate': 3,
        'benzoate': 5, 'sulfite': 5, 'sulphite': 5, 'dextrin': 3,
        'maltodextrin': 4, 'modified starch': 4, 'yeast extract': 4,
        'flavor enhancer': 5, 'emulsifier': 3, 'stabilizer': 3,
        'thickener': 2, 'acidity regulator': 1, 'anticaking': 2,
        'preservative': 5, 'artificial': 5, 'synthetic': 5,
        'nature identical': 4
    }

    ULTRA_PROCESSED_INDICATORS = [
        'high fructose corn syrup', 'hydrogenated', 'hydrolysed',
        'isolate', 'modified', 'artificial', 'ester', 'fractionated',
        'bleached', 'refined', 'reconstituted', 'flavoring', 'flavouring'
    ]

    # -------------------------------------------------------------------------
    # 2. DIETARY GOAL WEIGHTS & LIMITS
    # -------------------------------------------------------------------------
    GOAL_CONFIGS = {
        'Regular':     {'We': 0.15, 'Ws': 0.20, 'Wna': 0.15, 'Wsf': 0.15, 'Wp2': 0.20, 'Wa': 0.15, 'Wp': 0.15, 'Wf': 0.15, 'sugar_limit': 50, 'Ws_exp': 1.0, 'Wna_exp': 1.0, 'Wsf_exp': 1.0, 'We_exp': 1.0},
        'Weight Loss': {'We': 0.35, 'Ws': 0.35, 'Wna': 0.10, 'Wsf': 0.10, 'Wp2': 0.15, 'Wa': 0.05, 'Wp': 0.10, 'Wf': 0.30, 'sugar_limit': 25, 'Ws_exp': 1.2, 'Wna_exp': 1.0, 'Wsf_exp': 1.0, 'We_exp': 1.2},
        'Weight Gain': {'We': 0.05, 'Ws': 0.15, 'Wna': 0.10, 'Wsf': 0.10, 'Wp2': 0.15, 'Wa': 0.10, 'Wp': 0.50, 'Wf': 0.10, 'sugar_limit': 50, 'Ws_exp': 1.0, 'Wna_exp': 1.0, 'Wsf_exp': 1.0, 'We_exp': 1.0},
        'Diabetic':    {'We': 0.15, 'Ws': 0.60, 'Wna': 0.10, 'Wsf': 0.10, 'Wp2': 0.10, 'Wa': 0.05, 'Wp': 0.10, 'Wf': 0.15, 'sugar_limit': 20, 'Ws_exp': 1.5, 'Wna_exp': 1.0, 'Wsf_exp': 1.0, 'We_exp': 1.0},
        'Heart Health':{'We': 0.10, 'Ws': 0.10, 'Wna': 0.45, 'Wsf': 0.40, 'Wp2': 0.10, 'Wa': 0.05, 'Wp': 0.10, 'Wf': 0.10, 'sugar_limit': 50, 'Ws_exp': 1.0, 'Wna_exp': 1.5, 'Wsf_exp': 1.5, 'We_exp': 1.0},
        'Gym':         {'We': 0.10, 'Ws': 0.10, 'Wna': 0.10, 'Wsf': 0.10, 'Wp2': 0.15, 'Wa': 0.10, 'Wp': 0.70, 'Wf': 0.10, 'sugar_limit': 50, 'Ws_exp': 1.0, 'Wna_exp': 1.0, 'Wsf_exp': 1.0, 'We_exp': 1.0},
    }

    # Reference Limits
    BASE_KCAL = 2000.0
    BASE_SODIUM = 2000.0
    BASE_SAT_FAT = 20.0
    BASE_PROTEIN = 50.0
    BASE_FIBER = 25.0

    def calculate_score(self, ingredients_list: List[str], macros: Dict[str, float] = None, food_type: str = 'Solid', user_goal: str = 'Regular') -> Dict[str, Any]:
        """
        Universal Mathematical Formula:
        Calculates score based on exact macronutrient variables and food type.
        """
        if not ingredients_list:
            return {'score': 0.0, 'score_breakdown': [], 'nova_group': 4, 'details': {}}

        # Use exact macros if provided, otherwise assume worst-case proxies from ingredients
        has_macros = macros is not None and len(macros.keys()) > 0
        if not has_macros:
            # Fallback to pure factual/frequency based ingredient analysis (Simulated macros based on list)
            return self._calculate_legacy_frequency_score(ingredients_list, food_type, user_goal)

        # Ensure goal exists
        config = self.GOAL_CONFIGS.get(user_goal, self.GOAL_CONFIGS['Regular'])
        food_type = food_type.capitalize()
        notes = []

        # Safely extract and CLAMP macros (values per 100g or 100ml)
        # Prevents data errors (e.g. 1000mg salt misread as 1000g) from breaking the score.
        kcal = min(1000.0, max(0.0, float(macros.get('energy_kcal', 0))))
        sugar = min(100.0, max(0.0, float(macros.get('sugars', 0))))
        sodium = max(0.0, float(macros.get('sodium', 0)))
        if sodium < 10 and macros.get('salt', 0) > 0:
            sodium = float(macros.get('salt', 0)) * 400
        sodium = min(10000.0, sodium) # Max 10g salt per 100g
            
        sat_fat = min(100.0, max(0.0, float(macros.get('saturated_fat', 0))))
        tot_fat = min(100.0, max(0.0, float(macros.get('fat', sat_fat))))
        protein = min(100.0, max(0.0, float(macros.get('proteins', 0))))
        fiber = min(100.0, max(0.0, float(macros.get('fiber', 0))))

        # ---------------------------------------------------
        # DESSERT PROTECTION: If it's a cream/custard/yogurt, 
        # do not treat as Liquid beverage
        # ---------------------------------------------------
        orig_food_type = food_type
        if food_type == 'Liquid':
            is_dessert_matrix = any(x in " ".join(ingredients_list).lower() for x in ['cream', 'yogurt', 'custard', 'dessert', 'pudding', 'crème', 'oeufs'])
            if is_dessert_matrix:
                food_type = 'Semi-solid'
                notes.append({'description': "Matrix identified as dairy dessert (Reclassified from Liquid)", 'points': 0})

        # ---------------------------------------------------
        # BASE RISK RATIOS
        # ---------------------------------------------------
        energy_ratio = (kcal / self.BASE_KCAL)
        # Non-linear exponent scaling
        # Uncapped to allow exponential punishment for extreme offenders natively
        # 500kcal (ratio 0.25) * 4 = 1.0. This makes most whole foods (300-400kcal) moderate.
        energy_risk = ((energy_ratio ** 1.3) * 4) ** config.get('We_exp', 1.0)
        sugar_risk = ((sugar / config['sugar_limit']) ** 1.5) ** config.get('Ws_exp', 1.0)
        sodium_risk = ((sodium / 1000.0) ** 1.5) ** config.get('Wna_exp', 1.0)
        sat_fat_risk = ((sat_fat / self.BASE_SAT_FAT) ** 1.5) ** config.get('Wsf_exp', 1.0)

        # Densities (Benefits) with Protein Quality Evaluation
        top_ingredients = [ing.lower() for ing in ingredients_list[:5]]
        
        has_high_quality_protein = any(any(hq in ing for hq in ['whey', 'egg', 'meat', 'chicken', 'fish', 'milk', 'casein', 'soy isolate']) for ing in top_ingredients)
        has_refined_flour_dominant = any(any(c in ing for c in self.REFINED_CARBS) for ing in top_ingredients[:2])
        
        protein_quality_factor = 0.7  # Default mixed
        if has_high_quality_protein:
            protein_quality_factor = 1.0
        elif has_refined_flour_dominant:
            protein_quality_factor = 0.5
            
        if protein < 12.0:
            protein_quality_factor *= 0.5  # Heavy reduction for low absolute protein in Gym mode

        protein_density = min(1.0, protein / self.BASE_PROTEIN) * protein_quality_factor
        fiber_density = min(1.0, fiber / self.BASE_FIBER)

        liquid_penalty = 0.0
        
        # ---------------------------------------------------
        # CATEGORY ADJUSTMENTS
        # ---------------------------------------------------
        if food_type == 'Liquid':
            # Liquid sugar absorption is lethal because 10g per 100ml equals 30g+ in a standard human serving
            sugar_risk = sugar_risk * 2.5
            notes.append({'description': "High volumetric sugar absorption penalty (2.5x)", 'points': 0})
            
            # Sugar-sweetened beverage penalty
            has_added_sugar = any(s in ing.lower() for ing in ingredients_list for s in self.ADDED_SUGARS)
            if sugar > 2.0 or has_added_sugar:
                liquid_penalty = 0.15
                notes.append({'description': "Sugar-sweetened beverage penalty", 'points': -1.5})
                
        elif food_type == 'Semi-solid':
            # Fat Quality Index (e.g., protects cheese from being treated like pure junk oil)
            if tot_fat > 0:
                fat_quality_index = sat_fat / tot_fat
                if fat_quality_index > 0.5:
                    sat_fat_risk = min(1.0, sat_fat_risk * 1.2)
                    notes.append({'description': "Poor fat quality ratio", 'points': -1.0})
                elif fat_quality_index < 0.4:
                    sat_fat_risk = sat_fat_risk * 0.9
                    notes.append({'description': "Healthy fat ratio protected", 'points': +0.5})

        # ---------------------------------------------------
        # PROCESSING & ADDITIVE PENALTIES
        # ---------------------------------------------------
        nova_group, proc_notes = self._determine_nova(ingredients_list)
        notes.extend(proc_notes)
        
        processing_factor_map = {1: 0.0, 2: 0.2, 3: 0.6, 4: 1.0}
        processing_factor = processing_factor_map.get(nova_group, 1.0)

        additive_risk, add_notes = self._calculate_additive_risk(ingredients_list)
        notes.extend(add_notes)
        
        # ---------------------------------------------------
        # STRUCTURAL / GLYCEMIC PENALTIES
        # ---------------------------------------------------
        refined_carb_penalty = 0.0
        # If the food matrix contains mostly refined carbs, Diabetics need to be protected since "Sugars" won't capture starch/maida
        # If the food matrix contains mostly refined carbs in top ingredients
        has_main_refined_carbs = any(any(c in ing.lower() for c in self.REFINED_CARBS) for ing in ingredients_list[:3])
        if has_main_refined_carbs:
            # We use the extreme Sugar weight for Diabetics, and we penalize heavily based on Caloric density
            carb_risk = ((kcal / self.BASE_KCAL) * 4) ** config.get('Ws_exp', 1.0)
            refined_carb_penalty = max(config['Ws'], config['We']) * carb_risk * 1.5
            if refined_carb_penalty > 0.05:
                notes.append({'description': "High glycemic index penalty (Refined carbs dominate)", 'points': 0})

        # ---------------------------------------------------
        # UNIVERSAL MATH FORMULA
        # ---------------------------------------------------
        # RawScore = 1 - (Penalties) + (Benefits)
        total_penalties = (
            (config['We'] * energy_risk) +
            (config['Ws'] * sugar_risk) +
            (config['Wna'] * sodium_risk) +
            (config['Wsf'] * sat_fat_risk) +
            (config['Wp2'] * processing_factor) +
            (config['Wa'] * additive_risk) +
            liquid_penalty +
            refined_carb_penalty
        )
        
        total_benefits = (
            (config['Wp'] * protein_density) +
            (config['Wf'] * fiber_density)
        )
        
        # RawScore mapping resists compression by keeping penalties exponential
        risk_scaling_factor = 3.5
        raw_score = (1.0 + total_benefits) / (1.0 + (total_penalties * risk_scaling_factor))
        
        # Lock to 0.0 -> 1.0
        final_normalized = max(0.0, min(1.0, raw_score))
        
        # Convert to Display 0.0 -> 10.0
        display_score = final_normalized * 10.0
        
        # ---------------------------------------------------
        # BASE FLOOR PROTECTION
        # ---------------------------------------------------
        # If the product contains whole foods (Milk, Eggs, etc.), it shouldn't be 0.0
        # unless it's genuinely harmful.
        has_whole_foods = any(self._is_whole_food(ing) for ing in ingredients_list[:3])
        if has_whole_foods and nova_group < 4:
            display_score = max(display_score, 4.0)
        elif has_whole_foods:
            display_score = max(display_score, 3.0)
            
        display_score = round(display_score, 1)

        notes.append({'description': f"Scored optimized for: {user_goal} ({food_type})", 'points': 0})

        return {
            'score': display_score,
            'score_breakdown': notes,
            'nova_group': nova_group,
            'details': {
                'raw_penalties': total_penalties,
                'raw_benefits': total_benefits,
                'goal_used': user_goal,
                'type_used': food_type
            }
        }

    def _determine_nova(self, ingredients: List[str]) -> Tuple[int, List[Dict]]:
        markers = 0
        for ing in ingredients:
            ing_lower = ing.lower()
            if any(m in ing_lower for m in self.ULTRA_PROCESSED_INDICATORS) or \
               any(m in ing_lower for m in self.ADDITIVE_CONCERNS):
                markers += 1
                
        total = max(1, len(ingredients))
        marker_ratio = markers / total
        
        if markers == 0 and total > 1:
            if all(any(x in ing.lower() for x in self.ADDED_SUGARS | self.SODIUM_SOURCES | self.UNHEALTHY_FATS | {'oil', 'butter', 'starch'}) for ing in ingredients):
                return 2, [{'description': "Culinary ingredient mapping", 'points': 0}]
            return 1, [{'description': "Minimally processed (NOVA 1)", 'points': 0}]
            
        elif markers >= 1 or (markers >= 5 and marker_ratio > 0.3):
             if markers >= 2 or marker_ratio > 0.2:
                 return 4, [{'description': "Ultra-processed product", 'points': -1.5}]
             return 3, [{'description': "Processed product", 'points': -0.5}]
             
        return 2, []

    def _calculate_additive_risk(self, ingredients: List[str]) -> Tuple[float, List[Dict]]:
        risk = 0.0
        notes = []
        for ing in ingredients:
            ing_lower = ing.lower()
            matched = False
            for additive, severity in self.ADDITIVE_CONCERNS.items():
                if additive in ing_lower:
                    risk += severity / 10.0 # converts 1-10 to 0.1-1.0
                    notes.append({'description': f"Toxic additive ({ing})", 'points': -severity/10.0})
                    matched = True
                    break
            
            if not matched and ('ins ' in ing_lower or re.search(r'\be\d{3,4}', ing_lower)):
                risk += 0.5
                notes.append({'description': f"Unknown E-number ({ing})", 'points': -0.5})
                
        return min(1.0, risk), notes

    def _calculate_legacy_frequency_score(self, ingredients: List[str], food_type: str, user_goal: str = 'Regular') -> Dict[str, Any]:
        """
        Fallback scoring logic if strict numeric macros are missing.
        Uses exponential penalty mapping formatted to 0-10, resisting compression.
        """
        config = self.GOAL_CONFIGS.get(user_goal, self.GOAL_CONFIGS['Regular'])
        notes = [{'description': "Warning: Missing exact macros. Score estimated from ingredient list.", 'points': 0}]
        
        nova_group, proc_notes = self._determine_nova(ingredients)
        notes.extend(proc_notes)
        
        # We start with base metrics similar to raw score
        total_penalties = 0.0
        total_benefits = 0.0
        
        sugar_multiplier = (config['Ws'] / self.GOAL_CONFIGS['Regular']['Ws']) ** config.get('Ws_exp', 1.0)
        fat_multiplier = (config['Wsf'] / self.GOAL_CONFIGS['Regular']['Wsf']) ** config.get('Wsf_exp', 1.0)
        energy_multiplier = (config['We'] / self.GOAL_CONFIGS['Regular']['We']) ** config.get('We_exp', 1.0)
        sodium_multiplier = (config['Wna'] / self.GOAL_CONFIGS['Regular']['Wna']) ** config.get('Wna_exp', 1.0)
        protein_multiplier = config.get('Wp', 0.05) / self.GOAL_CONFIGS['Regular'].get('Wp', 0.05)
        
        # 1. Fallback Engine distrusts itself for GYM goals (Can't give elite gym scores without reading literal protein grams)
        if user_goal == 'Gym':
            protein_multiplier *= 0.5
            notes.append({'description': "Gym Score capped (Exact protein unverified)", 'points': 0})
            
        # DESSERT PROTECTION in Legacy Mode
        if food_type == 'Liquid':
            is_dessert_matrix = any(x in " ".join(ingredients).lower() for x in ['cream', 'yogurt', 'custard', 'dessert', 'pudding', 'crème', 'oeufs'])
            if is_dessert_matrix:
                food_type = 'Semi-solid'
                notes.append({'description': "Matrix identified as dairy dessert (Reclassified from Liquid)", 'points': 0})

        for i, ing in enumerate(ingredients):
            ing_lower = ing.lower()
            
            # Simple top 5 analysis for sugar/fat/carbs
            if i < 5:
                if any(s in ing_lower for s in self.ADDED_SUGARS) and 'sugar free' not in ing_lower:
                    base_risk = 0.3 if i == 0 else 0.2
                    penalty = base_risk * sugar_multiplier
                    total_penalties += penalty
                    notes.append({'description': f"High added sugar risk ({ing})", 'points': -penalty})
                    
                if any(f in ing_lower for f in self.UNHEALTHY_FATS):
                    base_risk = 0.3 if i == 0 else 0.2
                    penalty = base_risk * fat_multiplier
                    total_penalties += penalty
                    notes.append({'description': f"Unhealthy fat risk ({ing})", 'points': -penalty})
                    
                if any(c in ing_lower for c in self.REFINED_CARBS):
                    base_risk = 0.25 if i == 0 else 0.15
                    carb_multiplier = max(sugar_multiplier, energy_multiplier)
                    penalty = base_risk * carb_multiplier
                    total_penalties += penalty
                    notes.append({'description': f"Refined empty carbs ({ing})", 'points': -penalty})
                    
                if any(na in ing_lower for na in self.SODIUM_SOURCES):
                    base_risk = 0.25 if i < 3 else 0.1
                    penalty = base_risk * sodium_multiplier
                    total_penalties += penalty
                    notes.append({'description': f"High sodium priority ({ing})", 'points': -penalty})
                    
            # Positive trait tracking
            if self._is_whole_food(ing_lower) and protein_multiplier > 1.0:
                reward = 0.08 * protein_multiplier
                total_benefits += reward
                if i < 3:
                     notes.append({'description': f"Quality whole ingredient ({ing})", 'points': reward})
                     
        # Apply additives
        add_risk, add_notes = self._calculate_additive_risk(ingredients)
        total_penalties += add_risk * 1.5
        notes.extend(add_notes)
        
        # Processing Factor calculation (NOVA)
        processing_factor_map = {1: 0.0, 2: 0.2, 3: 0.6, 4: 1.0}
        processing_factor = processing_factor_map.get(nova_group, 1.0)
        
        nova_multiplier = config['Wp2'] / self.GOAL_CONFIGS['Regular']['Wp2']
        nova_penalty = processing_factor * 0.3 * nova_multiplier
        total_penalties += nova_penalty
        if nova_penalty > 0:
            notes.append({'description': f"Processing penalty (NOVA {nova_group})", 'points': -nova_penalty})
            
        # Asymptotic Math matches the Macro Engine exactly
        risk_scaling_factor = 2.5
        raw_score = (1.0 + total_benefits) / (1.0 + (total_penalties * risk_scaling_factor))
        
        # Lock to 0.0 -> 1.0, with a soft floor so it never hits absolute zero trivially
        final_normalized = max(0.08, min(1.0, raw_score))
        
        display_score = final_normalized * 10.0
        
        # WHOLE FOOD FLOOR protection in Legacy Mode
        has_whole_foods = any(self._is_whole_food(ing) for ing in ingredients[:3])
        if has_whole_foods and nova_group < 4:
            display_score = max(display_score, 4.0)
        elif has_whole_foods:
            display_score = max(display_score, 3.0)
            
        display_score = round(display_score, 1)
        
        # SYSTEMIC CEILING: Fallback Engine distrusts non-whole foods.
        # Ultra-processed foods (NOVA 4) cannot cross 'Pretty Decent' (6.0) without macro proof.
        nova_ceilings = {4: 5.5, 3: 7.5, 2: 9.0, 1: 10.0}
        ceiling = nova_ceilings.get(nova_group, 5.5)
        
        if display_score > ceiling:
            display_score = ceiling
            notes.append({'description': f"Score capped for NOVA {nova_group} (Macros unverified)", 'points': 0})
            
        # Liquid fallback penalty
        if food_type == 'Liquid' and display_score < 7.0:
            display_score = round(max(0.0, display_score - 1.5), 1)
        
        # Add details block so the frontend registers the context properly
        notes.append({'description': f"Scored optimized for: {user_goal} ({food_type})", 'points': 0})
        
        return {
            'score': display_score,
            'score_breakdown': notes,
            'nova_group': nova_group,
            'details': {
                'legacy_fallback': True,
                'goal_used': user_goal,
                'type_used': food_type
            }
        }

    def _is_whole_food(self, ingredient: str) -> bool:
        if any(x in ingredient for x in ['artificial', 'flavor', 'flavour', 'synthetic']):
            return False
        for wf in self.WHOLE_FOODS:
            if re.search(rf'\b{re.escape(wf)}\w*', ingredient):
                return True
        return False
