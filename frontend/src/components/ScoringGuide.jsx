import React from 'react';
import './ScoringGuide.css';
import { IoShieldCheckmarkOutline, IoCalculatorOutline, IoFlaskOutline, IoFitnessOutline, IoWarningOutline } from "react-icons/io5";

const ScoringGuide = () => {
    return (
        <div className="guide-wrapper">
            <header className="guide-header">
                <h1 className="guide-title">Science Behind Ingrexa Score</h1>
                <p className="guide-subtitle">Transparency is our core. Here is how we mathematically evaluate what goes into your body.</p>
            </header>

            <section className="guide-section">
                <div className="formula-card">
                    <div className="formula-icon">
                        <IoCalculatorOutline />
                    </div>
                    <div className="formula-box">
                        <span className="formula-text">Score = </span>
                        <div className="fraction">
                            <span className="numerator">1 + Σ Nutrients+</span>
                            <span className="denominator">1 + (Σ Concerns × Goal)</span>
                        </div>
                    </div>
                    <p className="formula-desc">
                        We use an <strong>Asymptotic Scoring Model</strong>. Instead of just subtracting points, we compare the nutritional value against the processing risks. This ensures that no single "good" ingredient can hide a high amount of "bad" additives.
                    </p>
                </div>
            </section>

            <section className="guide-section">
                <h2 className="section-title"><IoShieldCheckmarkOutline className="icon-v" /> How We Calculate: The Step-by-Step Logic</h2>
                <div className="calculation-steps">
                    <div className="step-card">
                        <div className="step-number">01</div>
                        <div className="step-body">
                            <strong>Macro-Nutrient Normalization</strong>
                            <p>We convert every ingredient's weight into a "relative health impact." Protein and Fiber are assigned <strong>positive weights</strong>, while Saturated Fats and Sodium enter our <strong>penalty queue</strong>. We use a base of 100g to ensure fair comparison across all food categories.</p>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-number">02</div>
                        <div className="step-body">
                            <strong>Ingredient Risk Profiling</strong>
                            <p>Our AI scans the text for <strong>1,500+ industrial keywords</strong>. Emulsifiers, thickeners, and Artificial Sweeteners trigger "Negative Multipliers." One high-risk chemical can reduce the score by up to 15% before macros are even considered.</p>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-number">03</div>
                        <div className="step-body">
                            <strong>Density & Sugar Analysis</strong>
                            <p>Liquid sugar (fructose/syrups) is mathematically <strong>2.5x more punitive</strong> than naturally occurring sugars in solids. We also apply an "Energy Density" filter—highly caloric foods with low fiber density are flagged as "Empty Calories."</p>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-number">04</div>
                        <div className="step-body">
                            <strong>Asymptotic Compression</strong>
                            <p>Finally, we run the totals through our <strong>Non-Linear Formula</strong>. This prevents a "perfect" health food from being ruined by one tiny additive, while simultaneously preventing a "bad" food from masking its risks with added synthetic vitamins.</p>
                        </div>
                    </div>
                </div>
            </section>

            <section className="guide-section">
                <h2 className="section-title"><IoFitnessOutline className="icon-v" /> Goal-Based Tailoring</h2>
                <p className="section-intro">A product's score isn't universal. When you select a goal, our engine recalculates the entire formula by shifting the <strong>"Goal Weight"</strong> multiplier:</p>

                <div className="goals-detailed">
                    <div className="goal-detail-card">
                        <div className="goal-detail-header">
                            <span className="goal-name">Diabetic / Low Carb</span>
                            <span className="goal-multiplier">3.5x Sugar Penalty</span>
                        </div>
                        <p className="goal-detail-text">The <strong>Σ Concerns</strong> part of the formula is heavily weighted towards Sugar and Refined Carbs. Even a small amount of added sugar will exponentially drop the final score.</p>
                    </div>

                    <div className="goal-detail-card">
                        <div className="goal-detail-header">
                            <span className="goal-name">Gym / Muscle Building</span>
                            <span className="goal-multiplier">2x Protein Reward</span>
                        </div>
                        <p className="goal-detail-text">The <strong>Σ Nutrients+</strong> numerator is modified to prioritize Protein density. Products with high protein get a "formula boost," allowing them to maintain a higher score even with moderate sodium.</p>
                    </div>

                    <div className="goal-detail-card">
                        <div className="goal-detail-header">
                            <span className="goal-name">Heart Health</span>
                            <span className="goal-multiplier">4x Sodium Weight</span>
                        </div>
                        <p className="goal-detail-text">Our engine shifts the <strong>Concerns</strong> focus to Sodium and Saturated Fats. Salt-heavy snacks like chips or instant noodles will face a mathematical "penalty floor" that prevents them from scoring above a 4.</p>
                    </div>

                    <div className="goal-detail-card">
                        <div className="goal-detail-header">
                            <span className="goal-name">Weight Loss</span>
                            <span className="goal-multiplier">Energy Density Cap</span>
                        </div>
                        <p className="goal-detail-text">For this goal, the <strong>Denominator</strong> is calculated based on calories per 100g. If a product is "Calorie Dense" (like oils or nuts), the score rewards fiber much higher to balance the energy intake.</p>
                    </div>
                </div>
            </section>

            <section className="guide-section nova-showcase">
                <header className="nova-header">
                    <h2 className="section-title"><IoFlaskOutline className="icon-v" /> The "Real Food" Rule</h2>
                    <p className="section-intro">Beyond nutrients, we analyze <strong>industrial processing</strong>. We use the international NOVA system to ensure you aren't just eating "engineered" food.</p>
                </header>

                <div className="nova-levels">
                    <div className="nova-level-item">
                        <div className="nova-badge n1">NOVA 1</div>
                        <div className="nova-content">
                            <strong>Unprocessed / Minimum</strong>
                            <p>Nature in its raw form. Seeds, fruit, milk, or eggs. High score potential.</p>
                        </div>
                    </div>

                    <div className="nova-level-item">
                        <div className="nova-badge n2">NOVA 2</div>
                        <div className="nova-content">
                            <strong>Processed Ingredients</strong>
                            <p>Items like oils, butter, or salt. These are kitchen staples, not meals.</p>
                        </div>
                    </div>

                    <div className="nova-level-item">
                        <div className="nova-badge n3">NOVA 3</div>
                        <div className="nova-content">
                            <strong>Processed Foods</strong>
                            <p>Traditional canning or simple bread. Safe, but scored with caution.</p>
                        </div>
                    </div>

                    <div className="nova-level-item featured-level">
                        <div className="nova-badge n4">NOVA 4</div>
                        <div className="nova-content">
                            <strong>Ultra-Processed (UPF)</strong>
                            <p>Formulations of industrial substances (flavors, thickeners, colors). These products face our <strong>5.5/10 Score Cap</strong>. No amount of "added fiber" can bypass this rule.</p>
                        </div>
                    </div>
                </div>

                <div className="nova-conclusion">
                    <p>
                        <IoWarningOutline className="warn-icon" />
                        <strong>Why the Cap?</strong> Studies show UPFs are linked to metabolic issues regardless of their calorie count. Our math reflects this biology.
                    </p>
                </div>
            </section>
        </div>
    );
};

export default ScoringGuide;
