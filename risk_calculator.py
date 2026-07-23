"""
risk_calculator.py
Contains approved mathematical models for Phishing Risk Assessment.
"""

EVENT_WEIGHTS = {
    "LINK": 10,
    "CREDENTIAL": 50,
    "IMAGE": 2,
    "MALWARE": 60,
    "MFA": 20
}

ROLE_WEIGHTS = {"Manager": 1.2, "Employee": 1.0, "Admin": 1.3}
DEPARTMENT_WEIGHTS = {"Finance": 1.5, "HR": 1.2, "IT": 0.9, "Management": 1.4, "Default": 1.0}

def calculate_base_event_score(event_counts):
    """Formula 1: Risk = Σ(Event Count × Event Weight)"""
    return sum(event_counts.get(e, 0) * EVENT_WEIGHTS.get(e, 0) for e in event_counts)

def calculate_exponential_penalty(base_score, count, weight_key):
    """Formula 2: Penalty = Base × ((Weight^Count − 1) / (Weight − 1))"""
    if count <= 1: return 0
    weight = EVENT_WEIGHTS.get(weight_key, 1.0)
    # Ensuring denominator isn't 0
    divisor = (weight - 1) if weight > 1 else 0.1 
    return base_score * ((weight ** count - 1) / divisor)

def normalize_risk(raw_score):
    """Formula 6: Normalized Risk = (Raw Score / (Raw Score + 100)) × 100"""
    return (raw_score / (raw_score + 100)) * 100

def calculate_final_risk(event_counts, role, dept, training_reward=0, report_reward=0):
    """
    Combines Formulas 1-6 for Level 2 Overall Employee Risk.
    """
    base = calculate_base_event_score(event_counts)
    
    # FIX: Apply repeat penalty for BOTH Credentials and Links
    cred_penalty = calculate_exponential_penalty(base, event_counts.get("CREDENTIAL", 0), "CREDENTIAL")
    link_penalty = calculate_exponential_penalty(base, event_counts.get("LINK", 0), "LINK")
    
    # Aggregation
    risk = base + cred_penalty + link_penalty
    
    # Weighting (Formulas 3 & 4)
    risk *= ROLE_WEIGHTS.get(role, 1.0)
    risk *= DEPARTMENT_WEIGHTS.get(dept, 1.0)
    
    # Rewards (Formula 5)
    final_risk = risk - training_reward - report_reward
    
    # Normalization (Formula 6)
    return normalize_risk(max(0, final_risk))
