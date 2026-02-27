def calculate_suitability(user_profile: dict, portfolio_metrics: dict) -> dict:
    """
    Computes Deterministic Suitability Score (0-100) based on user profile and portfolio risk.
    """
    # Define generic risk mapping
    appetite_map = {"Low": 20, "Moderate": 50, "High": 80}
    appetite_val = appetite_map.get(user_profile.get("risk_appetite", "Moderate"), 50)
    
    portfolio_risk = portfolio_metrics.get("portfolio_risk_score", 50)
    
    # Base mismatch (difference between preferred risk vs actual portfolio risk)
    mismatch = abs(appetite_val - portfolio_risk)
    
    # Parse inputs safely
    try:
        age = int(user_profile.get("age", 35))
    except ValueError:
        age = 35
        
    dep_str = str(user_profile.get("dependents", "0"))
    if "3+" in dep_str:
        dependents = 3
    else:
        try:
            dependents = int(dep_str)
        except ValueError:
            dependents = 0
            
    horizon = user_profile.get("investment_horizon", "Medium 3–7 yrs")
    profession = user_profile.get("profession", "Other")
    income = user_profile.get("annual_income", "5–10L")
    largest_holding_percent = portfolio_metrics.get("largest_position_percent", 0)
    
    breakdown = []
    
    # Deterministic Personal Mismatch Logic Rules
    # 1. Age < 30
    if age < 30:
        mismatch *= 0.90
        breakdown.append("Age < 30: Higher volatility tolerance allowed (reduced mismatch penalty by 10%)")
        
    # 2. Age > 50 and Portfolio Risk > 70
    if age > 50 and portfolio_risk > 70:
        mismatch += 15
        breakdown.append("Age > 50 & High Portfolio Risk: Added +15 mismatch penalty")
        
    # 3. Risk Appetite = Low and Portfolio Risk > 60
    if user_profile.get("risk_appetite") == "Low" and portfolio_risk > 60:
        mismatch += 20
        breakdown.append("Low Risk Appetite & High Portfolio Risk: Added +20 mismatch penalty")
        
    # 4. Risk Appetite = High and Portfolio Risk < 40
    if user_profile.get("risk_appetite") == "High" and portfolio_risk < 40:
        mismatch += 10
        breakdown.append("High Risk Appetite & Low Portfolio Risk: Added +10 conservative allocation flag")
        
    # 5. Investment Horizon = Short and Portfolio Risk > 60
    if "Short" in str(horizon) and portfolio_risk > 60:
        mismatch += 20
        breakdown.append("Short Horizon & High Portfolio Risk: Added +20 mismatch penalty")
        
    # 6. Dependents >= 2 and Largest Holding > 40%
    if dependents >= 2 and largest_holding_percent > 40:
        mismatch += 10
        breakdown.append("Dependents >= 2 & Concentration > 40%: Added +10 concentration penalty")
        
    # 7. Profession = Salaried and Income >= 10L
    # Checking for "10-20L", "20L+", etc. (supports different hyphen formatting)
    high_income_categories = ["10-20L", "10–20L", "20L+", "10-20l", "20l+"]
    if profession == "Salaried" and any(inc in str(income).lower() for inc in high_income_categories):
        mismatch *= 0.95
        breakdown.append("Salaried & Income >= 10L: Reduced mismatch penalty by 5%")
        
    # Suitability Score (0-100)
    suitability_score = max(0, min(100, 100 - mismatch))
    suitability_score = round(suitability_score, 0)
    
    # Suitability Level
    if suitability_score >= 75:
        suitability_level = "Aligned"
    elif suitability_score >= 50:
        suitability_level = "Moderate Mismatch"
    else:
        suitability_level = "High Mismatch"
        
    # Life Stage Classification
    if age < 30:
        life_stage = "Early Career Growth Investor"
    elif age <= 45:
        life_stage = "Mid-Career Wealth Builder"
    elif age < 60:
        life_stage = "Pre-Retirement Planner"
    else:
        life_stage = "Capital Preservation Stage"
        
    return {
        "suitability_score": suitability_score,
        "suitability_level": suitability_level,
        "suitability_breakdown": breakdown,
        "life_stage_classification": life_stage
    }

def anonymize_profile_for_llm(user_profile: dict) -> dict:
    """
    Returns a copy of the profile without exact age or raw income to protect PII.
    """
    safe_profile = dict(user_profile)
    
    # Obfuscate age to age group
    if "age" in safe_profile:
        try:
            age_int = int(safe_profile["age"])
            if age_int < 25: group = "<25"
            elif age_int <= 35: group = "25-35"
            elif age_int <= 45: group = "36-45"
            elif age_int <= 55: group = "46-55"
            else: group = "55+"
            safe_profile["age_group"] = group
            del safe_profile["age"]
        except ValueError:
            pass
            
    # Income could just be treated as "Income Category" instead of raw numbers
    if "annual_income" in safe_profile:
        safe_profile["income_range_category"] = safe_profile["annual_income"]
        del safe_profile["annual_income"]
        
    return safe_profile
