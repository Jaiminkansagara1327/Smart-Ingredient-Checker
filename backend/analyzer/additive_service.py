# Common Food Additives and their Health Impact
# Sourced from common food safety standards (WHO/FDA/EU)

ADDITIVES_DB = {
    # Preservatives
    "e211": {"name": "Sodium Benzoate", "risk": "Caution", "description": "Used to prevent mold. Can form benzene (carcinogen) when combined with Vitamin C."},
    "e202": {"name": "Potassium Sorbate", "risk": "Safe", "description": "A mild preservative. Generally considered safe but can cause allergies in rare cases."},
    "e250": {"name": "Sodium Nitrite", "risk": "Avoid", "description": "Common in processed meats. Linked to increased risk of heart disease and type 2 diabetes."},
    
    # Colors
    "e129": {"name": "Allura Red (Red 40)", "risk": "Avoid", "description": "Linked to hyperactivity in children and potential immune system impacts."},
    "e102": {"name": "Tartrazine (Yellow 5)", "risk": "Avoid", "description": "Known to cause allergic reactions and hyperactivity."},
    "e110": {"name": "Sunset Yellow", "risk": "Avoid", "description": "Synthetic coal tar dye. Linked to allergies and hyperactivity."},
    
    # Flavor Enhancers
    "e621": {"name": "Monosodium Glutamate (MSG)", "risk": "Caution", "description": "Can cause headaches or sweating in sensitive individuals."},
    
    # Sweeteners
    "e951": {"name": "Aspartame", "risk": "Caution", "description": "Low-calorie sweetener. Controversial; some studies suggest links to gut health issues."},
    "e950": {"name": "Acesulfame K", "risk": "Avoid", "description": "Usually mixed with other sweeteners. Contains methylene chloride, a known carcinogen."},
    "high fructose corn syrup": {"name": "HFCS", "risk": "Avoid", "description": "Highly processed sugar. Major contributor to obesity and liver disease."},
    
    # Thickeneders/Emulsifiers
    "e407": {"name": "Carrageenan", "risk": "Caution", "description": "Derived from seaweed. May cause digestive inflammation in some people."},
    "e415": {"name": "Xanthan Gum", "risk": "Safe", "description": "Produced by fermentation. Generally safe but can cause bloating in large amounts."}
}

def identify_additives(text):
    text = text.lower()
    found = []
    for code, info in ADDITIVES_DB.items():
        if code in text or info['name'].lower() in text:
            found.append(info)
    return found

def get_processing_score(text):
    text = text.lower()
    # High-processing signals
    ultra_processed_signals = [
        "hydrogenated", "hydrolyzed", "isolate", "syrup", "modified starch", 
        "dextrose", "maltodextrin", "artificial", "flavoring"
    ]
    
    count = sum(1 for signal in ultra_processed_signals if signal in text)
    if count > 4: return "Ultra-Processed"
    if count > 2: return "Processed"
    return "Minimally Processed"
