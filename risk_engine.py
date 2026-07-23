import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime
from risk_calculator import calculate_final_risk
from risk_classifier import classify_risk
import json

DB_CONFIG = {"host": "localhost", "database": "hawkins_cyber", "user": "postgres", "password": "admin123"}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def generate_enterprise_risk_scores():
    conn = get_db_connection()
    employees_df = pd.read_sql_query("SELECT * FROM employees", conn)
    logs_df = pd.read_sql_query("SELECT employee_id, event_type FROM simulation_logs", conn)
    
    results = []
    for _, emp in employees_df.iterrows():
        events = logs_df[logs_df["employee_id"] == emp["id"]]
        counts = {
            "LINK": len(events[events["event_type"] == "LINK"]),
            "CREDENTIAL": len(events[events["event_type"] == "CREDENTIAL"]),
            "IMAGE": len(events[events["event_type"] == "IMAGE"])
        }
        
        score = calculate_final_risk(counts, emp.get("designation"), emp.get("department"))
        results.append({"id": emp["id"], "risk_score": score, "risk_level": classify_risk(score)})
    
    # Formulas 8 & 9: Ranking and Percentile
    df = pd.DataFrame(results).sort_values(by="risk_score", ascending=False)
    df["risk_rank"] = range(1, len(df) + 1)
    df["risk_percentile"] = (df["risk_score"].rank(pct=True) * 100).round(2)
    
    # Sync to DB
    cur = conn.cursor()
    query = "UPDATE employees SET risk_score=%s, risk_level=%s, risk_percentile=%s, risk_rank=%s WHERE id=%s"
    data = [(r["risk_score"], r["risk_level"], r["risk_percentile"], r["risk_rank"], r["id"]) for _, r in df.iterrows()]
    psycopg2.extras.execute_batch(cur, query, data)
    conn.commit()
    cur.close()
    conn.close()
    print("Risk Engine successfully synchronized PostgreSQL.")

def build_risk_breakdown(employee_row, specific_history=None): 
    """
    Detailed breakdown of risk math.
    """
    email = employee_row["email"].strip().lower()
    history = specific_history if specific_history is not None else get_user_event_history(email)
    department = employee_row["department"] or "Default"

    # Count actual events to calculate penalties properly
    link_count = sum(1 for ev in history if ev.get("payload_type", "").upper() == "LINK")
    cred_count = sum(1 for ev in history if ev.get("payload_type", "").upper() == "CREDENTIAL")

    # 1. Base Score
    base_score = 0
    for ev in history:
        pt = ev.get("payload_type", "").upper()
        if pt == "CREDENTIAL": base_score += 60
        elif pt == "LINK": base_score += 30
        elif pt == "IMAGE": base_score += 5

    # 2. Multipliers/Weights
    dept_weights = {
        "HR": 1.2, "Finance": 1.3, "IT": 0.8,
        "Cyber Security": 0.7, "Management": 1.4, "Default": 1.0
    }
    dept_weight = dept_weights.get(department, 1.0)
    
    # FIX: Calculate actual repeat penalty instead of hardcoding 0
    # Using a simplified multiplier for the breakdown view
    repeat_penalty = 0
    if link_count > 1:
        repeat_penalty += (link_count * 15) # Add 15 extra points per repeated link click
    if cred_count > 1:
        repeat_penalty += (cred_count * 30) # Add 30 extra points per repeated credential submission

    training_reward = 0

    # 3. Calculation
    normalized_score = min(int((base_score + repeat_penalty) * dept_weight - training_reward), 100)
    
    # Determine Level
    if normalized_score >= 70: level = "CRITICAL"
    elif normalized_score >= 40: level = "HIGH"
    elif normalized_score >= 20: level = "MEDIUM"
    else: level = "LOW"

    return {
        "final_score": normalized_score,
        "base_score": base_score,
        "repeat_penalty": repeat_penalty,
        "dept_weight": dept_weight,
        "training_reward": training_reward,
        "risk_level": level
    }

def get_user_event_history(email):
    email = email.strip().lower()
    events = []
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # Simulation logs se data fetch karein
        cur.execute("SELECT * FROM simulation_logs ORDER BY id ASC")
        rows = cur.fetchall()
        for row in rows:
            # Encrypted data decrypt karein
            decrypted_json = cipher_suite.decrypt(row["encrypted_data"].encode("utf-8")).decode("utf-8")
            event_data = json.loads(decrypted_json)
            if event_data.get("user_email", "").strip().lower() == email:
                event_data["payload_type"] = row["payload_type"]
                events.append(event_data)
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching history in risk_engine: {e}")
    return events
if __name__ == "__main__":
    generate_enterprise_risk_scores()
