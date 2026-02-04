"""
Ingredient Scoring Engine - Based on Open Food Facts & Nutri-Score methodology
Scientifically accurate scoring system for food ingredient analysis
"""

class IngredientScorer:
    """
    Advanced ingredient scoring based on:
    - NOVA classification (processing level)
    - Nutri-Score methodology
    - Additive analysis
    - Whole food recognition
    """
    
    # Known harmful additives
    HARMFUL_ADDITIVES = {
        # Artificial colors
        'E102', 'E104', 'E110', 'E122', 'E124', 'E129', 'E131', 'E132', 'E133',
        'Tartrazine', 'Sunset Yellow', 'Allura Red', 'Brilliant Blue',
        
        # Preservatives of concern
        'E210', 'E211', 'E212', 'E213', 'E214', 'E215', 'E216', 'E217', 'E218', 'E219',
        'Sodium Benzoate', 'Potassium Benzoate', 'BHA', 'BHT', 'TBHQ',
        
        # Controversial sweeteners
        'E951', 'E950', 'E954', 'Aspartame', 'Acesulfame K', 'Saccharin',
        
        # Trans fats
        'Hydrogenated', 'Partially Hydrogenated',
        
        # Harmful preservatives
        'E249', 'E250', 'E251', 'E252', 'Sodium Nitrite', 'Sodium Nitrate',
    }
    
    # Beneficial whole food ingredients - COMPREHENSIVE DATABASE
    WHOLE_FOODS = {
        # Grains & Cereals
        'oats', 'quinoa', 'barley', 'brown rice', 'whole wheat', 'whole grain',
        'wheat flour', 'rye', 'millet', 'buckwheat', 'spelt', 'amaranth', 'teff',
        'sorghum', 'wild rice', 'farro', 'bulgur', 'rice', 'wheat', 'corn', 'maize',
        
        # Nuts & Seeds
        'almonds', 'walnuts', 'cashews', 'pecans', 'peanuts', 'hazelnuts', 'pistachios',
        'macadamia', 'brazil nuts', 'pine nuts',
        'sunflower seeds', 'pumpkin seeds', 'chia seeds', 'flax seeds', 'flaxseed',
        'sesame', 'hemp seeds', 'poppy seeds',
        
        # Fruits
        'apple', 'banana', 'strawberry', 'blueberry', 'raspberry', 'blackberry', 'mango',
        'orange', 'lemon', 'lime', 'grape', 'cherry', 'cranberry', 'date', 'fig',
        'raisins', 'dried fruit', 'apricot', 'peach', 'pear', 'plum', 'prune',
        'pineapple', 'papaya', 'guava', 'kiwi', 'watermelon', 'melon', 'cantaloupe',
        'pomegranate', 'passion fruit', 'dragon fruit', 'lychee', 'coconut',
        
        # Vegetables
        'tomato', 'carrot', 'spinach', 'kale', 'broccoli', 'pepper', 'bell pepper',
        'onion', 'garlic', 'ginger', 'celery', 'cucumber', 'lettuce', 'cabbage',
        'cauliflower', 'zucchini', 'eggplant', 'asparagus', 'beetroot', 'beet',
        'sweet potato', 'potato', 'pumpkin', 'squash', 'radish', 'turnip',
        'mushroom', 'green beans', 'snow peas', 'artichoke', 'brussels sprouts',
        
        # Legumes & Pulses
        'chickpeas', 'lentils', 'beans', 'black beans', 'kidney beans', 'pinto beans',
        'white beans', 'navy beans', 'lima beans', 'peas', 'green peas', 'split peas',
        'soy', 'soybeans', 'tofu', 'tempeh', 'edamame', 'mung beans',
        
        # Dairy & Alternatives
        'milk', 'cream', 'butter', 'ghee', 'cheese', 'yogurt', 'yoghurt', 'curd',
        'whey', 'paneer', 'cottage cheese', 'ricotta', 'mozzarella', 'cheddar',
        'almond milk', 'soy milk', 'oat milk', 'coconut milk',
        
        # Proteins
        'eggs', 'egg', 'chicken', 'beef', 'pork', 'lamb', 'mutton', 'turkey', 'duck',
        'fish', 'salmon', 'tuna', 'cod', 'sardines', 'mackerel', 'trout', 'tilapia',
        'shrimp', 'prawns', 'crab', 'lobster', 'shellfish', 'meat',
        
        # Oils (healthier ones)
        'olive oil', 'extra virgin olive oil', 'avocado oil', 'coconut oil',
        'sunflower oil', 'sesame oil', 'mustard oil', 'groundnut oil', 'peanut oil',
        'flaxseed oil', 'walnut oil', 'almond oil',
        
        # Natural Sweeteners
        'honey', 'maple syrup', 'agave', 'agave nectar', 'molasses', 'date syrup',
        'jaggery', 'stevia', 'monk fruit', 'coconut sugar', 'palm sugar',
        
        # SUPERFOODS & ADAPTOGENS
        'moringa', 'spirulina', 'chlorella', 'wheatgrass', 'acai', 'goji', 'goji berries',
        'maca', 'cacao', 'raw cacao', 'cocoa', 'matcha', 'green tea',
        'ashwagandha', 'tulsi', 'holy basil', 'reishi', 'cordyceps', 'lions mane',
        'rhodiola', 'schisandra', 'ginseng', 'astragalus',
        
        # HERBS & SPICES (Comprehensive)
        'turmeric', 'curcumin', 'ginger', 'cinnamon', 'cardamom', 'cloves', 'nutmeg',
        'basil', 'oregano', 'thyme', 'rosemary', 'sage', 'mint', 'peppermint',
        'coriander', 'cilantro', 'parsley', 'dill', 'fennel', 'fenugreek',
        'cumin', 'paprika', 'cayenne', 'chili', 'black pepper', 'white pepper',
        'vanilla', 'saffron', 'bay leaves', 'curry leaves', 'mustard seeds',
        'anise', 'star anise', 'tarragon', 'marjoram', 'chamomile', 'lavender',
        
        # AYURVEDIC & TRADITIONAL INGREDIENTS
        'amla', 'amalaki', 'triphala', 'brahmi', 'shankhpushpi', 'guduchi',
        'neem', 'giloy', 'shatavari', 'vidari', 'licorice', 'liquorice', 'mulethi',
        'ajwain', 'carom seeds', 'methi', 'pudina', 'jeera', 'haldi',
        
        # Fermented & Cultured Foods
        'kimchi', 'sauerkraut', 'miso', 'kombucha', 'kefir', 'yogurt culture',
        'probiotic', 'vinegar', 'apple cider vinegar', 'rice vinegar',
        
        # Others
        'salt', 'sea salt', 'himalayan salt', 'rock salt', 'water', 'yeast',
        'baking soda', 'baking powder', 'pectin', 'agar', 'gelatin', 'collagen',
        'nutritional yeast', 'seaweed', 'nori', 'kelp', 'wakame', 'dulse',
        'chlorophyll', 'aloe', 'aloe vera',
    }
    
    # Red flag ingredients
    RED_FLAGS = {
        'high fructose corn syrup': -20,
        'hfcs': -20,
        'partially hydrogenated': -25,
        'hydrogenated': -25,
        'trans fat': -25,
        'msg': -8,
        'monosodium glutamate': -8,
        'artificial flavor': -5,
        'artificial color': -5,
        'artificial sweetener': -10,
    }
    
    def calculate_score(self, ingredients_list: list) -> dict:
        """
        Calculate comprehensive health score (0-100)
        
        Args:
            ingredients_list: List of ingredient strings
            
        Returns:
            dict with score, breakdown, and analysis
        """
        if not ingredients_list:
            return {'score': 50, 'breakdown': [], 'nova_group': 3}
        
        # Start with classification
        nova_group = self._classify_nova(ingredients_list)
        base_score = self._get_base_score_from_nova(nova_group)
        
        adjustments = []
        current_score = base_score
        
        # Count whole foods
        whole_food_count = self._count_whole_foods(ingredients_list)
        whole_food_ratio = whole_food_count / len(ingredients_list)
        
        if whole_food_ratio > 0.8:
            bonus = 15
            current_score += bonus
            adjustments.append({
                'description': f'Excellent! {int(whole_food_ratio*100)}% whole food ingredients detected',
                'points': bonus
            })
        elif whole_food_ratio > 0.5:
            bonus = 8
            current_score += bonus
            adjustments.append({
                'description': f'{int(whole_food_ratio*100)}% whole food ingredients',
                'points': bonus
            })
        
        # Check for harmful additives
        harmful_found = self._find_harmful_additives(ingredients_list)
        for additive in harmful_found:
            penalty = -5
            current_score += penalty
            adjustments.append({
                'description': f'Contains {additive} (artificial additive)',
                'points': penalty
            })
        
        # Check for red flag ingredients
        for ingredient in ingredients_list:
            ing_lower = ingredient.lower()
            for red_flag, penalty in self.RED_FLAGS.items():
                if red_flag in ing_lower:
                    current_score += penalty
                    adjustments.append({
                        'description': f'Contains {ingredient} (highly processed)',
                        'points': penalty
                    })
                    break
        
        # Short, clean ingredient lists get bonus
        if len(ingredients_list) <= 5 and whole_food_ratio > 0.6:
            bonus = 10
            current_score += bonus
            adjustments.append({
                'description': 'Simple recipe with few ingredients',
                'points': bonus
            })
        
        # Cap score between 0-100
        final_score = max(0, min(100, current_score))
        
        return {
            'score': round(final_score),
            'score_breakdown': adjustments,
            'nova_group': nova_group,
            'whole_food_ratio': round(whole_food_ratio * 100)
        }
    
    def _classify_nova(self, ingredients: list) -> int:
        """
        Classify product using NOVA groups (1-4)
        1: Unprocessed/minimally processed
        2: Processed culinary ingredients
        3: Processed foods
        4: Ultra-processed
        """
        # Ultra-processed indicators
        ultra_indicators = [
            'high fructose corn syrup', 'hfcs', 'hydrogenated', 'hydrolysed',
            'modified starch', 'maltodextrin', 'dextrose', 'corn syrup',
            'artificial', 'flavor enhancer', 'emulsifier', 'thickener',
            'glazing agent', 'bleaching agent', 'bulking agent'
        ]
        
        # Check for E-numbers (additives)
        e_number_count = sum(1 for ing in ingredients if 'e' in ing.lower() and any(c.isdigit() for c in ing))
        
        # Check for ultra-processed indicators
        ultra_count = 0
        for ing in ingredients:
            ing_lower = ing.lower()
            if any(indicator in ing_lower for indicator in ultra_indicators):
                ultra_count += 1
        
        # Classify
        if ultra_count >= 3 or e_number_count >= 5:
            return 4  # Ultra-processed
        
        if ultra_count >= 1 or e_number_count >= 2:
            return 3  # Processed
        
        whole_food_count = self._count_whole_foods(ingredients)
        if whole_food_count / len(ingredients) > 0.7:
            return 1  # Unprocessed/minimally processed
        
        return 2  # Processed culinary ingredients
    
    def _get_base_score_from_nova(self, nova_group: int) -> int:
        """Get base score from NOVA classification"""
        base_scores = {
            1: 90,  # Unprocessed/minimally processed
            2: 75,  # Processed culinary ingredients
            3: 55,  # Processed foods
            4: 25,  # Ultra-processed
        }
        return base_scores.get(nova_group, 50)
    
    def _count_whole_foods(self, ingredients: list) -> int:
        """Count how many ingredients are recognizable whole foods"""
        count = 0
        for ing in ingredients:
            ing_lower = ing.lower()
            for whole_food in self.WHOLE_FOODS:
                if whole_food in ing_lower:
                    count += 1
                    break
        return count
    
    def _find_harmful_additives(self, ingredients: list) -> list:
        """Find harmful additives in ingredient list"""
        found = []
        for ing in ingredients:
            ing_upper = ing.upper()
            for additive in self.HARMFUL_ADDITIVES:
                if additive.upper() in ing_upper:
                    found.append(ing)
                    break
        return found
