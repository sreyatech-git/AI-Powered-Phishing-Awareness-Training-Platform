"""
department_risk.py
Calculates department-level risk metrics.
"""

def calculate_department_scores(employee_scores_df):
    """Formula 7: Dept Risk = (0.70 × Avg) + (0.30 × Max)"""
    dept_stats = employee_scores_df.groupby("department")["risk_score"].agg(["mean", "max"])
    dept_stats["risk_score"] = (0.70 * dept_stats["mean"]) + (0.30 * dept_stats["max"])
    return dept_stats.reset_index()