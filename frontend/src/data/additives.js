const additives = [
  // --- A ---
  {
    id: 1,
    name: "Aspartame",
    category: "Artificial Sweetener",
    status: "Caution",
    description: "Common zero-calorie sweetener. Contains phenylalanine; dangerous for individuals with PKU and a known trigger for migraines or gut sensitivity in some people."
  },
  {
    id: 2,
    name: "Artificial Colorings (Allura Red / Tartrazine)",
    category: "Coloring Agent",
    status: "Avoid",
    description: "Petroleum-derived synthetic dyes. Highly scrutinized for links to hyperactivity in children and potential mild allergic/histamine reactions."
  },
  // --- B ---
  {
    id: 3,
    name: "Butylated Hydroxyanisole (BHA)",
    category: "Preservative",
    status: "Avoid",
    description: "Synthetic antioxidant used to prevent fats from spoiling. Listed as a suspected endocrine disruptor and anticipated human carcinogen."
  },
  {
    id: 4,
    name: "Bleached Flour Agents (Benzoyl Peroxide)",
    category: "Flour Treatment",
    status: "Caution",
    description: "Used to whiten wheat flour. Severely strips natural nutrients and often masks highly processed, gluten-heavy refined grain foods."
  },
  // --- C ---
  {
    id: 5,
    name: "Casein / Caseinate",
    category: "Emulsifier / Texture Modifier",
    status: "Avoid",
    description: "🚨 DAIRY ALLERGEN. A major milk protein used to improve texture in processed meats and non-dairy creamers. High risk for dairy allergy sufferers."
  },
  {
    id: 6,
    name: "Carrageenan",
    category: "Thickener / Stabilizer",
    status: "Caution",
    description: "Seaweed extract used widely in dairy alternatives. Extensively debated for causing gut inflammation, bloating, and altering microbiome health."
  },
  // --- D ---
  {
    id: 7,
    name: "Dextrin / Maltodextrin",
    category: "Thickener / Bulking Agent",
    status: "Caution",
    description: "🚨 GLUTEN RISK. Highly processed starch usually made from corn, but sometimes derived from wheat. Spikes blood sugar rapidly due to high glycemic index."
  },
  {
    id: 8,
    name: "Diacetyl",
    category: "Artificial Flavoring",
    status: "Avoid",
    description: "Chemical mimicking buttery flavor. While ingested safely in small amounts, it is linked to severe respiratory inflammation when processed or inhaled."
  },
  // --- E ---
  {
    id: 9,
    name: "Erythritol",
    category: "Sugar Alcohol Sweetener",
    status: "Caution",
    description: "Bulk low-calorie sweetener. Frequently causes digestive distress, gas, and cramping when consumed in moderate to high quantities."
  },
  {
    id: 10,
    name: "Ethylenediamine Tetraacetic Acid (EDTA)",
    category: "Preservative / Chelating Agent",
    status: "Caution",
    description: "Used to bind minerals and prevent flavor degradation. Can cause mineral binding imbalances if consumed excessively over long periods."
  },
  // --- F ---
  {
    id: 11,
    name: "Fructose (High Fructose Corn Syrup)",
    category: "Sweetener",
    status: "Avoid",
    description: "Highly processed corn syrup derivative. Strongly linked to fatty liver disease, type-2 diabetes, obesity, and metabolic syndrome."
  },
  {
    id: 12,
    name: "Fumaric Acid",
    category: "Acidity Regulator",
    status: "Safe",
    description: "Naturally occurring organic acid used to add sour notes to rye breads and tart candies. Generally safe and non-toxic."
  },
  // --- G ---
  {
    id: 13,
    name: "Guar Gum",
    category: "Thickener / Emulsifier",
    status: "Caution",
    description: "Seed-derived fiber used in sauces and ice creams. Can trigger gas, loose stools, and abdominal discomfort in individuals with sensitive guts."
  },
  {
    id: 14,
    name: "Gluten (Vital Wheat Gluten Additive)",
    category: "Binder / Texturizer",
    status: "Avoid",
    description: "🚨 GLUTEN ALLERGEN. Pure wheat protein isolated and added to low-protein flours and meat substitutes. Triggers severe autoimmune response in Celiac disease."
  },
  // --- H ---
  {
    id: 15,
    name: "Hydrolyzed Vegetable Protein (HVP)",
    category: "Flavor Enhancer",
    status: "Caution",
    description: "🚨 GLUTEN / SOY RISK. Chemically broken-down plant protein often made from wheat or soy. Contains hidden naturally occurring monosodium glutamate (MSG)."
  },
  {
    id: 16,
    name: "Hexane-Processed Soy Isolates",
    category: "Protein Supplement / Texturizer",
    status: "Avoid",
    description: "🚨 SOY ALLERGEN. Soy protein extracted using chemical solvents like hexane. Known allergen base used heavily in protein bars and meat analogues."
  },
  // --- I ---
  {
    id: 17,
    name: "Invert Sugar Syrup",
    category: "Sweetener",
    status: "Avoid",
    description: "Sucrose split into glucose and fructose. Used to keep baked goods moist, but acts as an added fast-absorbing refined sugar that causes insulin spikes."
  },
  {
    id: 18,
    name: "Inosinate (Disodium Inosinate)",
    category: "Flavor Enhancer",
    status: "Caution",
    description: "Synergistic savory chemical modifier often paired directly with MSG. Individuals tracking gout or purine restrictions should avoid it."
  },
  // --- J ---
  {
    id: 19,
    name: "Juice Concentrates (Deionized)",
    category: "Sweetener",
    status: "Caution",
    description: "Fruit juice stripped of its natural minerals, flavors, and fibers. Functions purely as a hidden, concentrated layout sugar substitute."
  },
  {
    id: 20,
    name: "Juniper Extract",
    category: "Natural Flavoring Agent",
    status: "Safe",
    description: "Botanical aromatic extract used primarily in beverages. Generally non-toxic, though rare contact or ingestion sensitivities can happen."
  },
  // --- K ---
  {
    id: 21,
    name: "Karaya Gum",
    category: "Thickener / Laxative Binder",
    status: "Caution",
    description: "Natural tree exudate gum. Used in dressings and spreads. Known to cause mild laxative effects and allergic reactions in specific cohorts."
  },
  {
    id: 22,
    name: "Konjac Flour / Glucomannan",
    category: "Gelling Agent / Thickener",
    status: "Safe",
    description: "Extremely dense dietary soluble fiber matrix. Generally safe but creates choking risks if used in firm, bite-sized jelly treats."
  },
  // --- L ---
  {
    id: 23,
    name: "Lactose",
    category: "Bulking Filler / Sweetener",
    status: "Avoid",
    description: "🚨 DAIRY ALLERGEN. Milk sugar crystallization derivative. Triggers heavy digestive upset, gas, and cramping for lactose intolerant individuals."
  },
  {
    id: 24,
    name: "Lecithin (Soy-derived)",
    category: "Emulsifier",
    status: "Caution",
    description: "🚨 SOY RISK. Keeps fats and water mixed uniformly. Most soy lecithin is processed enough to lack soy proteins, but highly sensitive allergy types should check sources."
  },
  // --- M ---
  {
    id: 25,
    name: "Monosodium Glutamate (MSG)",
    category: "Flavor Enhancer",
    status: "Caution",
    description: "Amino acid salt providing savory umami flavor. Regarded safe globally, but can cause temporary headaches or flushing in sensitive subsets."
  },
  {
    id: 26,
    name: "Modified Food Starch",
    category: "Thickener",
    status: "Caution",
    description: "🚨 GLUTEN RISK. Chemically modified plant carbohydrate. If derived from wheat without explicit labeling, it poses a hidden risk for Celiac sufferers."
  },
  // --- N ---
  {
    id: 27,
    name: "Natamycin",
    category: "Antifungal Preservative",
    status: "Caution",
    description: "🚨 DAIRY COATING. An antifungal agent applied to the rind of cheeses to prevent mold growth. Can trigger responses in individuals highly sensitive to mold or dairy derivatives."
  },
  {
    id: 28,
    name: "Neotame",
    category: "Artificial Sweetener",
    status: "Caution",
    description: "Ultra-potent artificial sweetener derived from aspartame structure. Chemically stable but heavily synthesized and processed."
  },
  // --- O ---
  {
    id: 29,
    name: "Oat Fiber (Uncertified)",
    category: "Bulking Texturizer",
    status: "Caution",
    description: "🚨 GLUTEN RISK. Added dietary fiber. Unless certified gluten-free, oats suffer massive cross-contamination from wheat during agricultural harvesting."
  },
  {
    id: 30,
    name: "Oleoresins",
    category: "Concentrated Spice Extract",
    status: "Safe",
    description: "Natural plant spice extract residues used for standardizing color and flavor profiles. Clean and safe unless specific spice allergies exist."
  },
  // --- P ---
  {
    id: 31,
    name: "Potassium Bromate",
    category: "Flour Maturing Enhancer",
    status: "Avoid",
    description: "Oxidizing agent used to strengthen bread dough structure. Banned in many countries due to potential carcinogenic properties if baked incorrectly."
  },
  {
    id: 32,
    name: "Polysorbate 60 / 80",
    category: "Emulsifier",
    status: "Avoid",
    description: "Synthetic compounds used to keep ice cream and baked goods creamy. Suspected of shifting healthy gut microflora and degrading gut lining layers."
  },
  // --- Q ---
  {
    id: 33,
    name: "Quillaia Saponins",
    category: "Foaming Agent",
    status: "Caution",
    description: "Natural bark extract used to create foam headers in soft drinks like root beer. Safe in low limits but acts as a heavy local throat irritant if concentrated."
  },
  {
    id: 34,
    name: "Quinoline Yellow",
    category: "Synthetic Dye",
    status: "Avoid",
    description: "Coal-tar derived artificial color hue. Heavily restricted or banned in multiple global regions due to asthma and hyperactivity links in minors."
  },
  // --- R ---
  {
    id: 35,
    name: "Red 40 (Allura Red AC)",
    category: "Artificial Color",
    status: "Avoid",
    description: "Extremely common petroleum-derived red dye. Extensively monitored for links to behavioral shifts, focus reduction, and hives in children."
  },
  {
    id: 36,
    name: "Rice Malt Syrup",
    category: "Sweetener",
    status: "Caution",
    description: "Alternative sweetener made by breaking down rice starch. Completely fructose-free, but possesses a sky-high glycemic index that spikes insulin."
  },
  // --- S ---
  {
    id: 37,
    name: "Sodium Benzoate",
    category: "Preservative",
    status: "Caution",
    description: "Inhibits mold growth in acidic foods. Can convert into benzene (a known carcinogen) if combined directly inside formula drinks with Vitamin C."
  },
  {
    id: 38,
    name: "Sodium Metabisulfite",
    category: "Sulfite Preservative",
    status: "Avoid",
    description: "🚨 SULFITE ALLERGEN. Chemical bleaching and preservation agent. Known to trigger acute asthma attacks and heavy respiratory reactions in sulfite-allergic groups."
  },
  // --- T ---
  {
    id: 39,
    name: "Tartrazine (Yellow 5)",
    category: "Artificial Color",
    status: "Avoid",
    description: "Bright yellow azo dye. Noted for inducing aspirin-like allergy responses, asthma breathing issues, and hives in susceptible individuals."
  },
  {
    id: 40,
    name: "Textured Vegetable Protein (TVP)",
    category: "Meat Substitute Filler",
    status: "Avoid",
    description: "🚨 SOY / GLUTEN ALLERGEN. Manufactured plant extract made largely from defatted soy flour. Heavy trigger base for consumers tracking legume sensitivities."
  },
  // --- U ---
  {
    id: 41,
    name: "Unbleached Wheat Flour Additive",
    category: "Refined Base Grain",
    status: "Avoid",
    description: "🚨 GLUTEN ALLERGEN. Standard enriched grain base. Contains natural concentrations of gluten proteins, causing immediate digestive distress to Celiac patients."
  },
  {
    id: 42,
    name: "Urea",
    category: "Fermentation Nutrient",
    status: "Safe",
    description: "Nitrogen compound used as a yeast food source during heavy commercial alcohol processing. Safely consumed when restricted within regulatory parameters."
  },
  // --- V ---
  {
    id: 43,
    name: "Vegetable Oil (Partially Hydrogenated)",
    category: "Fat Emollient / Oil Base",
    status: "Avoid",
    description: "The technical classification source for harmful industrial Trans Fats. Directly raises LDL (bad) cholesterol and significantly increases coronary heart disease risks."
  },
  {
    id: 44,
    name: "Vanillin (Ethyl Vanillin Synthetic)",
    category: "Artificial Flavoring",
    status: "Safe",
    description: "Lab-synthesized alternative to natural vanilla extract beans. Highly consistent, cost-effective, and safe for standard consumer intake."
  },
  // --- W ---
  {
    id: 45,
    name: "Whey Protein Concentrate",
    category: "Protein Filler / Texturizer",
    status: "Avoid",
    description: "🚨 DAIRY ALLERGEN. Liquid milk byproduct powder. Heavily rich in residual lactose and dairy proteins, causing immediate bloating or allergic flare-ups."
  },
  {
    id: 46,
    name: "Wheat Starch",
    category: "Thickening Binder",
    status: "Avoid",
    description: "🚨 GLUTEN ALLERGEN. Carbohydrate matrix isolated from wheat plants. Frequently holds trace amounts of gluten fractions unless certified gluten-isolated."
  },
  // --- X ---
  {
    id: 47,
    name: "Xanthan Gum",
    category: "Stabilizer / Thickener",
    status: "Caution",
    description: "Bacterial fermentation sugar product. Widely utilized in gluten-free baking, but known to trigger gas, bloating, and mild digestive shifts if overconsumed."
  },
  {
    id: 48,
    name: "Xylitol",
    category: "Sugar Alcohol Sweetener",
    status: "Caution",
    description: "Plant-derived sugar alcohol. Causes dramatic gastrointestinal distress or laxative effects in humans if over-eaten. (Extremely toxic to pets)."
  },
  // --- Y ---
  {
    id: 49,
    name: "Yeast Extract (Autolyzed)",
    category: "Flavor Enhancer",
    status: "Caution",
    description: "🚨 GLUTEN RISK. Savory concentrated extract containing rich free glutamates. Often grown on barley crops, presenting a cross-contamination hazard for gluten sensitivity."
  },
  {
    id: 50,
    name: "Yellow 6 (Sunset Yellow FCF)",
    category: "Synthetic Color dye",
    status: "Avoid",
    description: "Artificial chemical coloring compound. Highly monitored across Europe due to suspected connections with asthma, allergies, and skin rashes."
  },
  // --- Z ---
  {
    id: 51,
    name: "Zein",
    category: "Glaze Glosser / Coating agent",
    status: "Safe",
    description: "Corn-extracted protein powder used to coat vitamin tablets and candies. Naturally gluten-free and easily processed by the human metabolic system."
  },
  {
    id: 52,
    name: "Zinc Oxide Additive",
    category: "Nutrient Fortifier",
    status: "Safe",
    description: "Mineral additive used to artificially fortify refined breakfast cereals. Completely safe and highly effective at addressing zinc deficiencies."
  }
];

export default additives;