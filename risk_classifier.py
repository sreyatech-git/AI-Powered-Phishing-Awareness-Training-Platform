"""
risk_classifier.py
Maps normalized scores to risk levels.
"""

def classify_risk(score):
    """Maps Level 2 Score (0-100) to Risk Level."""
    if score >= 70: return "CRITICAL"
    if score >= 40: return "HIGH"
    if score >= 20: return "MEDIUM"
    return "LOW"