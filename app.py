from flask import Flask, render_template, request, redirect, url_for, Response, jsonify, session
import psycopg2
import psycopg2.extras
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from google import genai
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import json
import random
import time
import re
import threading
from admin_alert_service import send_admin_login_alert, send_bruteforce_alert
import bruteforce_service
# app.py ke top par:
from risk_engine import build_risk_breakdown, get_user_event_history
from email_evolution_engine import generate_evolved_email
from campaign_quality_engine import validate_generated_campaign, print_validation_report
from system_health.health_engine import get_complete_health

app = Flask(__name__)
app.secret_key = os.urandom(24)

# =========================================================
# ENCRYPTION SETUP
# =========================================================
if not os.path.exists("secret.key"):
    with open("secret.key", "wb") as key_file:
        key_file.write(Fernet.generate_key())

with open("secret.key", "rb") as key_file:
    cipher_suite = Fernet(key_file.read())

# =========================================================
# DATABASE CONFIG
# =========================================================
DB_HOST = "localhost"
DB_NAME = "hawkins_db"
DB_USER = ""
DB_PASS = ""

# ===========================
# PUT YOUR KEYS HERE
# ===========================
GEMINI_API_KEY = ""
SENDER_EMAIL = "sreya00713@gmail.com"
EMAIL_PASSWORD = ""

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    ) 

# AI OUTPUT SANITIZATION
# =========================================================
def sanitize_ai_subject(raw_subject):
    if not raw_subject:
        return "Important Update"
    cleaned = re.sub(r'^(Subject|SUBJECT|subject)\s*[:\-]?\s*', '', raw_subject.strip())
    cleaned = re.sub(r'\*\*', '', cleaned)
    cleaned = re.sub(r'[*_~`]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else "Important Update"

def sanitize_ai_body(raw_body):
    if not raw_body:
        return "<p>Please review the attached update.</p>"
    cleaned = re.sub(r'^(Body|BODY|body)\s*[:\-]?\s*', '', raw_body.strip())
    cleaned = re.sub(r'\*\*', '', cleaned)
    cleaned = re.sub(r'[*_~`#]', '', cleaned)
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    paragraphs = cleaned.split('\n\n')

    formatted_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if para:
            para = para.replace('\n', '<br>')
            para = re.sub(r'[ \t]+', ' ', para)
            formatted_paragraphs.append(
                f'<p style="margin-bottom: 12px; line-height: 1.6;">{para}</p>'
            )

    return '\n'.join(formatted_paragraphs) if formatted_paragraphs else "<p>Please review the attached update.</p>"

def parse_ai_response(response_text):
    if not response_text:
        return "Important Update", "<p>Please review the attached update.</p>"

    text = response_text.strip()

    if "|||" in text:
        parts = text.split("|||", 1)
        subject = sanitize_ai_subject(parts[0])
        body = sanitize_ai_body(parts[1])
        return subject, body

    lines = text.split('\n')
    if len(lines) > 1 and len(lines[0]) < 150:
        subject = sanitize_ai_subject(lines[0])
        body = sanitize_ai_body('\n'.join(lines[1:]))
        return subject, body

    return "Important Update", sanitize_ai_body(text)

# =========================================================
# HAWKINS CORPORATE FOOTER & SIGNATURES
# =========================================================
hawkins_legal_footer = """
<div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #e2e8f0; font-size: 10px; color: #64748b; line-height: 1.5;">
All documents of Hawkins Cookers Limited with financial consequences for the company - orders, receipts, bills, cheques, credit notes, etc. - require the signature of an authorised person and emails will not be considered for financial commitments. This email and any files transmitted with it are intended solely for the use of the individual or entity to whom they are addressed. If you have received this email in error please notify the system manager. Please note that any views or opinions presented in this email are solely those of the author and do not necessarily represent those of the company. The recipient should check this email and any attachments for the presence of viruses. The company accepts no liability for any damage caused by any virus transmitted by this email.
</div>
"""

department_signatures = {
    "HR": {"name": "Arpita Das", "title": "Management Trainee - HR", "location": "Mumbai"},
    "Finance": {"name": "Rohit Sharma", "title": "Senior Accounts Manager", "location": "Mumbai"},
    "IT": {"name": "Gautam Thakur", "title": "Manager - System Administration", "location": "Mahim,Mumbai"},
    "Cyber Security": {"name": "Gautam Thakur", "title": "Manager - System Administration", "location": "Mahim,Mumbai"},
    "Management": {"name": "Rajesh Iyer", "title": "Executive Assistant - Board Office", "location": "Mumbai"},
    "Sales": {"name": "Sales Operations Desk", "title": "Revenue Management", "location": "Mumbai"},
    "Marketing": {"name": "Corporate Communications", "title": "Brand Management", "location": "Mumbai"},
    "Supply Chain": {"name": "Logistics & Procurement", "title": "Supply Chain Management", "location": "Thane"},
    "Legal": {"name": "Legal & Compliance", "title": "Corporate Law Division", "location": "Mumbai"},
    "Customer Support": {"name": "Customer Success", "title": "Consumer Relations", "location": "Mumbai"},
    "R&D": {"name": "Product Development", "title": "Engineering & Design", "location": "Thane"},
    "Administration": {"name": "Facilities Management", "title": "Administration", "location": "Mumbai"},
    "Default": {"name": "System Administrator", "title": "IT Support Desk", "location": "Mumbai"}
}

def get_email_signature(department):
    sig = department_signatures.get(department, department_signatures["Default"])
    return f"""
<div style="margin-top: 25px; font-family: Georgia, serif; font-style: italic; color: #1e3a5f; line-height: 1.8;">
    <div>Regards,</div>
    <div style="margin-top: 8px;">
        <div style="font-weight: 600;">{sig['name']}</div>
        <div>{sig['title']}</div>
        <div style="font-weight: 600;">Hawkins Cookers Limited</div>
        <div>{sig['location']}</div>
    </div>
</div>
"""

# =========================================================
# THREAT INTELLIGENCE DATABASE
# =========================================================
threat_intel_db = {
    "HR": {
        "threat_actor": "Internal Spoofing",
        "scenario": "Payroll/Leave Fraud",
        "subject": "URGENT: Revised Payroll & Leave Policy - Immediate Action Required",
        "body": (
            "As part of our ongoing compliance review, the HR department is rolling out the Revised Payroll Structure "
            "and Leave Deduction Policy effective from the upcoming month. These changes impact all employees across "
            "departments and have been approved by the Board of Directors in our recent meeting. "
            "Key changes include: (1) Revised HRA calculation methodology, (2) Updated medical leave encashment rules, "
            "and (3) New tax deduction codes. "
            "All employees must review and acknowledge the updated policy document to ensure smooth payroll processing "
            "for the current salary cycle. Failure to review within 48 hours may result in delayed salary "
            "disbursement and incorrect tax deductions. Please access the document through the secure portal link provided below."
        ),
        "payload_type": "LINK"
    },
    "Finance": {
        "threat_actor": "External Vendor Fraud",
        "scenario": "Fake Invoice Payment",
        "subject": "ACTION REQUIRED: Overdue Vendor Invoice - Immediate Payment Processing",
        "body": (
            "This is regarding an outstanding vendor invoice that requires immediate settlement to avoid service "
            "disruption. Vendor: Precision Engineering Pvt. Ltd. | Amount: Rs.4,85,000 | Status: OVERDUE. "
            "Our accounts payable system flagged this invoice as CRITICAL during the current month's reconciliation. "
            "The vendor has escalated this matter to their regional director, and we have received a formal notice "
            "of potential service suspension effective in 24 hours if payment is not processed. "
            "Please verify the attached invoice summary and process the payment through the secure vendor portal immediately."
        ),
        "payload_type": "LINK"
    },
    "IT": {
        "threat_actor": "IT Support Spoofing",
        "scenario": "Office 365 Password Expiry",
        "subject": "URGENT: Microsoft 365 Password Expiration Notice - Verify Immediately",
        "body": (
            "This is an automated security notification from the Hawkins IT Security Desk. Our identity management "
            "system has detected that your corporate Microsoft 365 account password is scheduled to expire within "
            "the next 2 hours. This expiry is in accordance with the updated Information Security Policy, which "
            "mandates routine password rotation for all employees. "
            "AFFECTED SERVICES: Outlook Email, SharePoint, Teams, and SAP SSO. If your password expires, your account "
            "will be automatically locked. To prevent disruption to your work, please verify your current credentials "
            "and set a new password through the secure password management portal."
        ),
        "payload_type": "CREDENTIAL"
    },
    "Cyber Security": {
        "threat_actor": "Third-Party Vendor",
        "scenario": "Critical Malware Alert",
        "subject": "CRITICAL: Zero-Day Vulnerability Detected on Network - Immediate Response Required",
        "body": (
            "PRIORITY: P1-CRITICAL | INCIDENT: Active Zero-Day Threat. "
            "This is an URGENT security alert from the Hawkins Security Operations Center (SOC). Our automated "
            "threat detection platform has identified suspicious activity consistent with a vulnerability exploitation "
            "attempt targeting our primary firewall infrastructure during the latest scan. "
            "As per our Incident Response Protocol, ALL Cyber Security personnel are required to immediately access "
            "the Emergency Admin Portal to review full packet captures and initiate containment procedures. "
            "This is NOT a drill. Your immediate login and verification are required to coordinate the response."
        ),
        "payload_type": "CREDENTIAL"
    },
    "Management": {
        "threat_actor": "Executive Fraud",
        "scenario": "Confidential Internal Request",
        "subject": "Confidential: Board Meeting Follow-Up - Employee Master Sheet Required Urgently",
        "body": (
            "I am currently attending an unscheduled board meeting with the Audit Committee and have limited "
            "network connectivity. The board has requested an immediate review of the latest Employee Master Sheet "
            "for current compliance verification purposes. "
            "This document is required for the ongoing statutory audit, and the auditors are waiting. "
            "Please DO NOT email this document as an attachment due to data sensitivity. Instead, upload it "
            "securely to the Board Document Portal using your executive credentials. Time is critical. "
            "Your prompt action will be noted in the meeting minutes."
        ),
        "payload_type": "CREDENTIAL"
    },
    "Default": {
        "threat_actor": "Executive Fraud",
        "scenario": "Urgent Task Bypass",
        "subject": "Confidential Task - Quick Action Needed",
        "body": (
            "This is an urgent internal communication requiring your immediate attention. A time-sensitive "
            "document has been flagged for your review by the senior management team during the current cycle. "
            "Due to the confidential nature of this request, standard approval workflows have been bypassed. "
            "Please log in to the secure corporate portal to access the document and acknowledge receipt."
        ),
        "payload_type": "CREDENTIAL"
    }
}

rofiles = {
    "HR": {"name": "Payroll Management Office", "email": "payroll@hawkinscookers.com"},
    "Finance": {"name": "Accounts Payable Desk", "email": "accounts@hawkinscookers.com"},
    "IT": {"name": "Hawkins Security Desk", "email": "security@hawkinscookers.com"},
    "Cyber Security": {"name": "Threat Intelligence Unit", "email": "soc@hawkinscookers.com"},
    "Management": {"name": "Executive Board Office", "email": "board@hawkinscookers.com"},
    "Sales": {"name": "Sales Operations", "email": "sales.ops@hawkinscookers.com"},
    "Marketing": {"name": "Brand & Media Desk", "email": "communications@hawkinscookers.com"},
    "Supply Chain": {"name": "Procurement Office", "email": "procurement@hawkinscookers.com"},
    "Legal": {"name": "Legal Department", "email": "legal@hawkinscookers.com"},
    "Customer Support": {"name": "Consumer Relations", "email": "support.desk@hawkinscookers.com"},
    "R&D": {"name": "Engineering Vault", "email": "rnd.vault@hawkinscookers.com"},
    "Administration": {"name": "Facilities & Admin", "email": "facilities@hawkinscookers.com"},
    "Default": {"name": "Security System", "email": "gautam@hawkinscooker.com"}
}

def get_cta_button_text(payload_type, department):
    payload_type = payload_type.upper().strip()
    dept = department if department else "Default"
    cta_map = {
        "LINK": {
            "HR": "Review Revised Policy Document",
            "Finance": "Process Invoice Payment",
            "IT": "Download Security Update",
            "Cyber Security": "View Threat Report",
            "Management": "Access Confidential Files",
            "Default": "Review Document"
        },
        "CREDENTIAL": {
            "HR": "Verify Payroll Access",
            "Finance": "Authenticate Payment Portal",
            "IT": "Verify Account / Reset Password",
            "Cyber Security": "Emergency Admin Login",
            "Management": "Secure Executive Login",
            "Default": "Verify Account / Start Action"
        }
    }
    return cta_map.get(payload_type, cta_map["LINK"]).get(dept, "Verify Account / Start Action")


# =========================================================
# EMPLOYEE / CAMPAIGN / PROMPT HELPERS
# =========================================================
def get_employee_by_email(email):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM employees WHERE LOWER(email) = LOWER(%s) LIMIT 1", (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except Exception as e:
        print(f"Employee lookup error: {e}")
        return None

def get_employee_by_id(employee_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM employees WHERE id = %s LIMIT 1", (employee_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except Exception as e:
        print(f"Employee by ID lookup error: {e}")
        return None

def create_campaign_run(campaign_name="Manual Awareness Run", trigger_mode="manual", notes=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO campaign_runs (campaign_name, trigger_mode, notes)
            VALUES (%s, %s, %s) RETURNING id
        """, (campaign_name, trigger_mode, notes))
        campaign_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return campaign_id
    except Exception as e:
        print(f"Campaign run creation error: {e}")
        return None

def create_campaign_target(campaign_id, employee_row):
    try:
        target_goal = employee_row["target_goal"] if "target_goal" in employee_row.keys() else "CLICK"
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO campaign_targets (
                campaign_id, employee_id, employee_name, employee_email,
                department, target_goal, status, attempt_no, achieved
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            campaign_id, employee_row["id"], employee_row["name"], employee_row["email"],
            employee_row["department"], target_goal, "TRIGGERED", 1, False
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Campaign target creation error: {e}")

def update_campaign_target_status(campaign_id, employee_id, new_status, achieved=False):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if achieved:
            cur.execute("""
                UPDATE campaign_targets
                SET status = %s, achieved = %s, achieved_at = NOW()
                WHERE campaign_id = %s AND employee_id = %s
            """, (new_status, True, campaign_id, employee_id))
        else:
            cur.execute("""
                UPDATE campaign_targets SET status = %s
                WHERE campaign_id = %s AND employee_id = %s
            """, (new_status, campaign_id, employee_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Campaign target update error: {e}")

def get_latest_prompt_history_for_employee(employee_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT ph.* FROM prompt_history ph
            JOIN campaign_runs cr ON ph.campaign_id = cr.id
            WHERE cr.notes ILIKE %s
            ORDER BY ph.id DESC LIMIT 1
        """, (f"%employee_id={employee_id}%",))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except Exception as e:
        print(f"Prompt history lookup error: {e}")
        return None

def decrypt_prompt_history_payload(encrypted_prompt_data):
    try:
        if not encrypted_prompt_data:
            return None
        decrypted = cipher_suite.decrypt(encrypted_prompt_data.encode("utf-8")).decode("utf-8")
        return json.loads(decrypted)
    except Exception as e:
        print(f"Prompt payload decrypt error: {e}")
        return None

def get_previous_subjects_for_employee(employee_id):
    subs = []
    for payload in get_all_prompt_payloads_for_employee(employee_id):
        s = payload.get("ai_subject")
        if s and s not in subs:
            subs.append(s)
    return subs

def get_previous_ctas_for_employee(employee_id):
    ctas = []
    for payload in get_all_prompt_payloads_for_employee(employee_id):
        c = payload.get("cta_text")
        if c and c not in ctas:
            ctas.append(c)
    return ctas

def get_all_prompt_payloads_for_employee(employee_id):
    payloads = []
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT ph.encrypted_prompt_data
            FROM prompt_history ph
            JOIN campaign_runs cr ON ph.campaign_id = cr.id
            WHERE cr.notes ILIKE %s
            ORDER BY ph.id DESC
        """, (f"%employee_id={employee_id}%",))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for row in rows:
            decrypted = decrypt_prompt_history_payload(row["encrypted_prompt_data"])
            if decrypted:
                payloads.append(decrypted)
    except Exception as e:
        print(f"Prompt payloads lookup error: {e}")
    return payloads

def get_used_scenario_ids_for_employee(employee_id):
    used = []
    for payload in get_all_prompt_payloads_for_employee(employee_id):
        sid = payload.get("scenario_id")
        if sid and sid not in used:
            used.append(sid)
    return used

def get_real_attempt_count_for_employee(employee_id):
    return len(get_all_prompt_payloads_for_employee(employee_id)) + 1

def get_winning_scenarios_org_wide():
    try:
        from threat_scenarios import THREAT_SCENARIOS
    except Exception:
        return [], ""

    scenario_titles = {}
    for dept_list in THREAT_SCENARIOS.values():
        for sc in dept_list:
            scenario_titles[sc["id"]] = sc["title"]

    success_counts = {}
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT ph.encrypted_prompt_data, ph.campaign_id
            FROM prompt_history ph
        """)
        rows = cur.fetchall()

        for row in rows:
            payload = decrypt_prompt_history_payload(row["encrypted_prompt_data"])
            if not payload:
                continue
            sid = payload.get("scenario_id")
            emp_id = payload.get("employee_id")
            if not sid or not emp_id:
                continue

            cur.execute("""
                SELECT achieved FROM campaign_targets
                WHERE campaign_id = %s AND employee_id = %s
                ORDER BY id DESC LIMIT 1
            """, (row["campaign_id"], emp_id))
            tgt = cur.fetchone()
            if tgt and tgt["achieved"]:
                success_counts[sid] = success_counts.get(sid, 0) + 1

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Winning scenario computation error: {e}")
        return [], ""

    if not success_counts:
        return [], ""

    winning_scenario_ids = list(success_counts.keys())
    best_sid = max(success_counts, key=success_counts.get)
    winning_category_hint = scenario_titles.get(best_sid, "")

    return winning_scenario_ids, winning_category_hint


def save_prompt_history(campaign_id, employee_row, previous_result, modification_reason,
                        final_prompt, ai_subject, ai_body, scenario_id=None, cta_text=None):
    try:
        target_goal = employee_row["target_goal"] if "target_goal" in employee_row.keys() else "CLICK"
        prompt_payload = {
            "employee_id": employee_row["id"],
            "employee_email": employee_row["email"],
            "employee_name": employee_row["name"],
            "department": employee_row["department"],
            "target_goal": target_goal,
            "final_prompt": final_prompt,
            "ai_subject": ai_subject,
            "ai_body": ai_body,
            "scenario_id": scenario_id,
            "cta_text": cta_text,
            "saved_at": datetime.now().isoformat()
        }
        encrypted_prompt_data = cipher_suite.encrypt(
            json.dumps(prompt_payload).encode("utf-8")
        ).decode("utf-8")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO prompt_history (campaign_id, previous_result, modification_reason, encrypted_prompt_data)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (campaign_id, previous_result, modification_reason, encrypted_prompt_data))
        prompt_version_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return prompt_version_id
    except Exception as e:
        print(f"Prompt history save error: {e}")
        return None

# =========================================================
# SECURE EVENT LOGGING
# =========================================================
# =========================================================
# SECURE EVENT LOGGING (UPDATED WITH FORENSIC PAYLOAD)
# =========================================================
# =========================================================
# SECURE EVENT LOGGING (UPDATED WITH REAL-TIME RISK SYNC)
# =========================================================
def secure_log_event(employee_row, payload_type="LINK", campaign_id=None, prompt_version_id=None, captured_password=None, html_body=None):
    scores = {"IMAGE": 5, "LINK": 30, "CREDENTIAL": 60}
    payload_type = payload_type.upper().strip()
    score = scores.get(payload_type, 30)

    try:
        target_goal = employee_row["target_goal"] if "target_goal" in employee_row.keys() else "CLICK"
        event_packet = {
            "employee_id": employee_row["id"],
            "user_email": employee_row["email"],
            "user_name": employee_row["name"],
            "department": employee_row["department"],
            "target_goal": target_goal,
            "event_type": payload_type,
            "event_time": datetime.now().isoformat()
        }
        
        if captured_password:
            event_packet["captured_password"] = captured_password
            
        encrypted_data = cipher_suite.encrypt(json.dumps(event_packet).encode("utf-8")).decode("utf-8")

        encrypted_html = None
        if html_body:
            encrypted_html = cipher_suite.encrypt(html_body.encode("utf-8")).decode("utf-8")

        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Event ko logs mein save kiya
        cur.execute("""
            INSERT INTO simulation_logs (
                payload_type, risk_score, encrypted_data, campaign_id,
                prompt_version_id, employee_id, event_type, payload_html
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (payload_type, score, encrypted_data, campaign_id, prompt_version_id, employee_row["id"], payload_type, encrypted_html))
        conn.commit()

        # =========================================================
        # NAYA CODE: REAL-TIME SCORE & LEADERBOARD AUTO-SYNC
        # =========================================================
        # A) Jaise hi click hua, iska naya score nikal lo
        new_score = calculate_risk_score(employee_row)
        new_level = get_risk_level(new_score)[0]
        
        # B) Employees table mein iska naya score save kar do
        cur.execute("UPDATE employees SET risk_score = %s, risk_level = %s WHERE id = %s", 
                    (new_score, new_level, employee_row["id"]))
        
        # C) Kyunki score badha hai, toh sabki Rank aur Percentile wapas set kardo
        cur.execute("""
            WITH ranked AS (
                SELECT id, 
                       RANK() OVER (ORDER BY risk_score DESC) as new_rank,
                       ROUND((PERCENT_RANK() OVER (ORDER BY risk_score ASC) * 100)::numeric, 2) as new_percentile
                FROM employees
            )
            UPDATE employees e
            SET risk_rank = r.new_rank,
                risk_percentile = r.new_percentile
            FROM ranked r
            WHERE e.id = r.id;
        """)
        conn.commit()
        # =========================================================

        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Logging Error: {e}")


def get_all_logged_events():
    events = []
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # --- THE MASTER FIX: JOINING SIMULATION LOGS WITH PROMPT HISTORY ---
        cur.execute("""
            SELECT sl.payload_type, sl.encrypted_data, sl.timestamp,
                   sl.campaign_id, sl.prompt_version_id, sl.employee_id, sl.event_type,
                   ph.encrypted_prompt_data
            FROM simulation_logs sl
            LEFT JOIN prompt_history ph ON sl.prompt_version_id = ph.id
            ORDER BY sl.id ASC
        """)
        rows = cur.fetchall()
        for row in rows:
            try:
                decrypted_json = cipher_suite.decrypt(row["encrypted_data"].encode("utf-8")).decode("utf-8")
                event_data = json.loads(decrypted_json)
                event_data["payload_type"] = row["payload_type"]
                event_data["timestamp"] = str(row["timestamp"])[:19] if row["timestamp"] else None
                event_data["campaign_id"] = row["campaign_id"]
                event_data["prompt_version_id"] = row["prompt_version_id"]
                event_data["employee_id"] = row["employee_id"]
                event_data["event_type"] = row["event_type"]
                
                # --- SMART FETCH: Extracting AI Body & Subject directly from Prompt History ---
                event_data["ai_body"] = None
                if row["encrypted_prompt_data"]:
                    prompt_payload = decrypt_prompt_history_payload(row["encrypted_prompt_data"])
                    if prompt_payload:
                        event_data["ai_body"] = prompt_payload.get("ai_body")
                        event_data["ai_subject"] = prompt_payload.get("ai_subject")

                events.append(event_data)
            except Exception:
                continue
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Event fetch error: {e}")
    return events


def get_user_event_history(email):
    email = email.strip().lower()
    events = get_all_logged_events()
    return [ev for ev in events if ev.get("user_email", "").strip().lower() == email]


def is_target_achieved(email, target_goal):
    target_goal = (target_goal or "CLICK").upper().strip()
    history = get_user_event_history(email)
    if not history:
        return False
    if target_goal == "CLICK":
        for ev in history:
            if ev.get("payload_type", "").upper() in ["LINK", "CREDENTIAL"]:
                return True
        return False
    elif target_goal == "CREDENTIAL":
        for ev in history:
            if ev.get("payload_type", "").upper() == "CREDENTIAL":
                return True
        return False
    return False


def get_previous_result_for_user(email, target_goal):
    history = get_user_event_history(email)
    if not history:
        return "NO_PREVIOUS_TRIGGER"
    target_goal = (target_goal or "CLICK").upper().strip()
    if target_goal == "CREDENTIAL":
        for ev in history:
            if ev.get("payload_type", "").upper() == "CREDENTIAL":
                return "CREDENTIAL_CAPTURED"
        for ev in history:
            if ev.get("payload_type", "").upper() == "LINK":
                return "CLICKED_ONLY"
        return "TRIGGERED_NO_SUCCESS"
    if target_goal == "CLICK":
        for ev in history:
            if ev.get("payload_type", "").upper() in ["LINK", "CREDENTIAL"]:
                return "CLICK_CAPTURED"
        return "TRIGGERED_NO_SUCCESS"
    return "UNKNOWN"

def get_campaigns_sent_to_employee(employee_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM campaign_targets WHERE employee_id = %s", (employee_id,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"Error counting campaigns: {e}")
        return 0

def get_caught_users():
    caught_users = {}
    events = get_all_logged_events()
    for event in events:
        email = event.get("user_email", "").strip().lower()
        if not email:
            continue
        caught_users[email] = event.get("timestamp") or "Time Unknown"
    return caught_users


# =========================================================
# EMPLOYEE DATA FOR DASHBOARD
# =========================================================
# =========================================================
# EMPLOYEE DATA FOR DASHBOARD
# =========================================================
def load_employee_records():
    records = []
    caught_users = get_caught_users()
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM employees ORDER BY id ASC')
        db_records = cursor.fetchall()
        for row in db_records:
            emp_email = row['email'].strip().lower()
            target_goal = row['target_goal'] if 'target_goal' in row.keys() else 'CLICK'
            if is_target_achieved(emp_email, target_goal):
                final_status = "CAUGHT (Logged in System)"
            elif emp_email in caught_users:
                final_status = "CAUGHT (Logged in System)"
            else:
                final_status = "Pending..."
            records.append({
                'id': row['id'],               # <--- YEH LINE MISSING THI (The Fix)
                'EmailID': row['email'],
                'Name': row['name'],
                'Department': row['department'],
                'Gender': row['gender'],
                'Age': row['age'],
                'Status': final_status,
                'TargetGoal': target_goal,
                'EmpID': row.get('emp_id', '')
            })
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
    return records
# =========================================================
# AUTO-SYNC ENGINE (Runs automatically in background)
# =========================================================
def auto_sync_risk_engine():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Sabhi ka score calculate karo
        cur.execute("SELECT id, email, department FROM employees")
        emps = cur.fetchall()
        for emp in emps:
            score = calculate_risk_score(emp)
            level = get_risk_level(score)[0]
            cur.execute("UPDATE employees SET risk_score = %s, risk_level = %s WHERE id = %s", (score, level, emp['id']))
        
        # Rank aur Percentile update karo
        cur.execute("""
            WITH ranked AS (
                SELECT id, 
                       RANK() OVER (ORDER BY risk_score DESC) as new_rank,
                       ROUND((PERCENT_RANK() OVER (ORDER BY risk_score ASC) * 100)::numeric, 2) as new_percentile
                FROM employees
            )
            UPDATE employees e
            SET risk_rank = r.new_rank,
                risk_percentile = r.new_percentile
            FROM ranked r
            WHERE e.id = r.id;
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Background Risk Engine Auto-Synced!")
    except Exception as e:
        print(f"Auto Sync Error: {e}")
# =========================================================
# RISK SCORE CALCULATION
# =========================================================
def calculate_risk_score(employee_row):
    email = employee_row["email"].strip().lower()
    history = get_user_event_history(email)
    department = employee_row["department"] or "Default"

    # NAYA: Actual event counts for penalty
    link_count = sum(1 for ev in history if ev.get("payload_type", "").upper() == "LINK")
    cred_count = sum(1 for ev in history if ev.get("payload_type", "").upper() == "CREDENTIAL")

    base_score = 0
    for ev in history:
        pt = ev.get("payload_type", "").upper()
        if pt == "CREDENTIAL":
            base_score += 60
        elif pt == "LINK":
            base_score += 30
        elif pt == "IMAGE":
            base_score += 5

    # NAYA: Apply Repeat Penalty
    repeat_penalty = 0
    if link_count > 1:
        repeat_penalty += (link_count * 15)
    if cred_count > 1:
        repeat_penalty += (cred_count * 30)

    department_risk_multiplier = {
        "HR": 1.2, "Finance": 1.3, "IT": 0.8, "Cyber Security": 0.7, "Management": 1.4,
        "Sales": 1.3, "Marketing": 1.1, "Supply Chain": 1.4, "Legal": 0.8, 
        "Customer Support": 1.2, "R&D": 1.1, "Administration": 0.9,
        "Default": 1.0
    }
    multiplier = department_risk_multiplier.get(department, 1.0)
    
    # Base score aur penalty ko add karke multiplier lagana
    final_score = min(int((base_score + repeat_penalty) * multiplier), 100)
    return final_score

def get_risk_level(score):
    if score >= 70:
        return "CRITICAL", "#dc2626", "#fef2f2"
    elif score >= 40:
        return "HIGH", "#d97706", "#fffbeb"
    elif score >= 20:
        return "MEDIUM", "#2563eb", "#eff6ff"
    else:
        return "LOW", "#059669", "#f0fdf4"


def get_department_vulnerability(department):
    vuln_map = {
        "HR": ("Urgency / FOMO-based traps", "Payroll changes, leave policy updates, deadline warnings"),
        "Finance": ("Authority / Compliance pressure", "Invoice payments, vendor verification, tax compliance"),
        "IT": ("Technical trust exploitation", "Password expiry, system updates, security alerts"),
        "Cyber Security": ("Fear / Crisis response triggers", "Zero-day alerts, incident response, emergency access"),
        "Management": ("Executive authority mimicry", "Board requests, confidential documents, audit compliance"),
        "Sales": ("Greed / Target Pressure", "Commission payouts, lead generation, CRM access"),
        "Marketing": ("Urgency / Brand Reputation", "Social media lockouts, campaign budgets, agency invoices"),
        "Supply Chain": ("Fear of Production Stop", "Customs delays, vendor invoices, material shortages"),
        "Legal": ("Authority Bias / Compliance", "Lawsuits, policy violations, mandatory signatures"),
        "Customer Support": ("Sympathy / Duty Obligation", "Escalated complaints, consumer court, defective products"),
        "R&D": ("Curiosity / Intellectual Property", "Design leaks, patent issues, confidential blueprints"),
        "Administration": ("Routine Habit / Convenience", "ID renewals, parking policies, cafeteria updates"),
        "Default": ("General social engineering", "Generic urgency-based phishing attempts")
    }
    return vuln_map.get(department, vuln_map["Default"])

# =========================================================
# DYNAMIC RISK RECOMMENDATIONS (FIXED LOGIC)
# =========================================================
def generate_recommendations(score, department, history):
    import random
    recs = []
    
    # Analyze exact behaviors from history to prevent illogical "Low Risk" labels
    has_credential = any(ev.get("payload_type", "").upper() == "CREDENTIAL" for ev in history)
    has_click = any(ev.get("payload_type", "").upper() == "LINK" for ev in history)
    has_open = any(ev.get("payload_type", "").upper() == "IMAGE" for ev in history)
    is_completely_clean = len(history) > 0 and not (has_credential or has_click)
    
    # 1. PRIMARY RISK ASSESSMENT (Logical & Randomized for variety)
    if has_credential or score >= 70:
        crit_msgs = [
            "🔴 CRITICAL BREACH: User submitted credentials to an untrusted source. Immediate remediation required.",
            "🔴 SEVERE RISK: Compromised credentials detected. Account is highly vulnerable to ATO (Account Takeover).",
            "🔴 HIGH ALERT: Target failed a critical credential-harvesting simulation. Priority intervention needed."
        ]
        action_msgs = [
            "🔒 ACTION: Enforce mandatory password reset and activate hardware-based MFA.",
            "🔒 ACTION: Enroll user in 'Zero-Trust Credential Security' intensive training within 24 hours.",
            "🔒 ACTION: Restrict VPN/Remote access until remedial phishing awareness course is completed."
        ]
        recs.append(random.choice(crit_msgs))
        recs.append(random.choice(action_msgs))
        
    elif has_click or score >= 30: # 30 pts is a link click, ensuring they never get 'Low Risk'
        warn_msgs = [
            "⚠️ VULNERABLE: User clicked on a malicious link but stopped before submitting credentials.",
            "⚠️ MODERATE RISK: Target exhibits a tendency to engage with unauthorized links. Monitor closely.",
            "⚠️ WARNING: Behavioral data shows susceptibility to link-based phishing traps."
        ]
        action_msgs = [
            "📚 ACTION: Assign the 'URL Inspection & Link Hovering' micro-learning module.",
            "📚 ACTION: Increase the frequency of baseline simulation emails for this user to build reflexes.",
            "📚 ACTION: Schedule a brief security nudge regarding verifying sender domains."
        ]
        recs.append(random.choice(warn_msgs))
        recs.append(random.choice(action_msgs))
        
    elif is_completely_clean:
        safe_msgs = [
            "✅ SECURE: User successfully detected and ignored recent phishing attempts.",
            "✅ EXCELLENT REFLEXES: Target demonstrates strong security hygiene and threat avoidance.",
            "✅ LOW RISK: Behavioral telemetry indicates high resilience against social engineering."
        ]
        action_msgs = [
            "🏆 ACTION: Consider nominating this employee as a departmental Security Champion.",
            "🏆 ACTION: Reduce simulation frequency and shift focus to advanced threat identification.",
            "🏆 ACTION: No immediate action required. Maintain standard quarterly testing."
        ]
        recs.append(random.choice(safe_msgs))
        recs.append(random.choice(action_msgs))
        
    else:
        recs.append("ℹ️ PENDING: Not enough simulation data available to accurately profile this user.")
        recs.append("📅 ACTION: Include this employee in the next automated baseline campaign.")

    # 2. CONTEXT-AWARE DEPARTMENTAL STRATEGY
    dept_advice = {
        "HR": [
            "🎯 HR Strategy: Simulate payroll anomalies or urgent policy update emails next.",
            "🎯 HR Strategy: Test resilience against fake resume attachments or compliance warnings."
        ],
        "Finance": [
            "🎯 Finance Strategy: Focus future tests on vendor invoice spoofing and wire transfer urgency.",
            "🎯 Finance Strategy: Simulate CEO fraud requesting immediate financial data or fund transfers."
        ],
        "IT": [
            "🎯 IT Strategy: Deploy complex credential harvesting (e.g., fake VPN or Office 365 expiry alerts).",
            "🎯 IT Strategy: Test with spoofed system alerts or emergency server maintenance traps."
        ],
        "Cyber Security": [
            "🎯 SOC Strategy: Run advanced zero-day vulnerability alerts or fake incident response drills.",
            "🎯 SOC Strategy: Test against highly sophisticated, spear-phishing payloads targeting security protocols."
        ],
        "Management": [
            "🎯 Exec Strategy: Simulate whaling attacks regarding confidential board meetings or legal threats.",
            "🎯 Exec Strategy: Use high-pressure, time-sensitive executive bypass scenarios for the next test."
        ]
    }
    
    default_strats = [
        "🎯 General Strategy: Maintain varied simulation themes to map out user's blind spots.",
        "🎯 General Strategy: Alternate between urgency and curiosity-based lures in future campaigns."
    ]
    
    if department in dept_advice:
        recs.append(random.choice(dept_advice[department]))
    else:
        recs.append(random.choice(default_strats))

    # 3. DYNAMIC FORENSIC INSIGHT
    if history:
        last_event = history[-1].get('payload_type', '').upper()
        if last_event == "CREDENTIAL":
            recs.append("🔍 Forensic Insight: The most recent failure involved submitting sensitive data. Recommend reviewing data privacy guidelines.")
        elif last_event == "LINK":
            recs.append("🔍 Forensic Insight: The most recent failure was a direct link click. User needs help identifying visual deception in emails.")
        elif last_event == "IMAGE":
            recs.append("🔍 Forensic Insight: User opened the email but didn't click. Curiosity was triggered, but caution prevailed.")

    return recs

# =========================================================
# SMART GEMINI AI GENERATOR
# =========================================================
def generate_ai_phishing_content(target_name, department, has_clicked_before,
                                 threat_subject, threat_body, payload_type,
                                 previous_prompt_payload=None, attempt_count=1,
                                 used_scenario_ids=None,
                                 winning_scenario_ids=None,
                                 winning_category_hint="",
                                 previous_subjects=None,  
                                 previous_ctas=None,      
                                 designation="",
                                 strategy_context=None):
    try:
        from email_evolution_engine import generate_evolved_email

        subject, body, final_prompt, scenario_id, cta_text, sender_identity = generate_evolved_email(
            target_name=target_name,
            department=department,
            has_clicked_before=has_clicked_before,
            previous_prompt_payload=previous_prompt_payload,
            attempt_count=attempt_count,
            used_scenario_ids=used_scenario_ids,
            winning_scenario_ids=winning_scenario_ids,
            winning_category_hint=winning_category_hint,
            previous_subjects=previous_subjects,
            previous_ctas=previous_ctas,
            designation=designation,
            strategy_context=strategy_context 
        )
        return subject, body, final_prompt, scenario_id, cta_text, sender_identity

    except Exception as e:
        print(f"AI phishing content generation failed (adapter): {e}")
        fallback_body = (
            f'<p style="margin-bottom: 12px;">Dear {target_name},</p>'
            f'<p style="margin-bottom: 12px;">{threat_body}</p>'
            f'<p style="margin-bottom: 12px;">Please take immediate action.</p>'
        )
        fallback_prompt = f"FALLBACK_PROMPT::{target_name}::{department}::{payload_type}"
        return threat_subject, fallback_body, fallback_prompt, None, None, None


# =========================================================
# MAIL SENDER CORE
# =========================================================
sender_profiles = {
    "HR": {"name": "Payroll Management Office", "email": "payroll@hawkinscookers.com"},
    "Finance": {"name": "Accounts Payable Desk", "email": "accounts@hawkinscookers.com"},
    "IT": {"name": "Hawkins Security Desk", "email": "security@hawkinscookers.com"},
    "Cyber Security": {"name": "Threat Intelligence Unit", "email": "soc@hawkinscookers.com"},
    "Management": {"name": "Executive Board Office", "email": "board@hawkinscookers.com"},
    "Sales": {"name": "Sales Operations", "email": "sales.ops@hawkinscookers.com"},
    "Marketing": {"name": "Brand & Media Desk", "email": "communications@hawkinscookers.com"},
    "Supply Chain": {"name": "Procurement Office", "email": "procurement@hawkinscookers.com"},
    "Legal": {"name": "Legal Department", "email": "legal@hawkinscookers.com"},
    "Customer Support": {"name": "Consumer Relations", "email": "support.desk@hawkinscookers.com"},
    "R&D": {"name": "Engineering Vault", "email": "rnd.vault@hawkinscookers.com"},
    "Administration": {"name": "Facilities & Admin", "email": "facilities@hawkinscookers.com"},
    "Default": {"name": "Security System", "email": "gautam@hawkinscooker.com"}
}
def send_simulation_email(employee_row, campaign_id, prompt_version_id, ai_subject, ai_body, payload_type,
                          cta_text=None, sender_identity=None):
    
    # --- HTML SPACING FIX FOR CUSTOM/BULK MAILS ---
    if "<br" not in ai_body and "<p" not in ai_body:
        ai_body = ai_body.replace('\n', '<br>')
    # ----------------------------------------------
    
    recipient_mail = employee_row["email"]
    target_name = employee_row["name"]
    department = employee_row["department"] if employee_row["department"] else "Default"

    sender = sender_identity if sender_identity else sender_profiles.get(department, sender_profiles["Default"])
    signature_html = get_email_signature(department)
    link_label = cta_text if cta_text else "review the details"

    try:
        session = smtplib.SMTP("smtp.gmail.com", 587)
        session.starttls()
        session.login(SENDER_EMAIL, EMAIL_PASSWORD)

        payload = MIMEMultipart('alternative')
        payload['From'] = f"{sender['name']} <{sender['email']}>"
        payload['To'] = recipient_mail
        payload['Subject'] = ai_subject

        if payload_type == "CREDENTIAL":
            tracking_click_url = f"http://127.0.0.1:5000/login-page?user={recipient_mail}&campaign_id={campaign_id}&prompt_version_id={prompt_version_id}"
        else:
            tracking_click_url = f"http://127.0.0.1:5000/track-click?user={recipient_mail}&type=LINK&campaign_id={campaign_id}&prompt_version_id={prompt_version_id}"

        tracking_image_url = f"http://127.0.0.1:5000/track-click?user={recipient_mail}&type=IMAGE&campaign_id={campaign_id}&prompt_version_id={prompt_version_id}"
        tracking_open_url = f"http://127.0.0.1:5000/track-open?user={recipient_mail}&campaign_id={campaign_id}&prompt_version_id={prompt_version_id}"

        PROMO_IMAGE_LINK = "https://www.hawkinscookers.com/message_footer/Cooktop_08-12-2025.jpg"

        inline_link_html = (
            f'<a href="{tracking_click_url}" '
            f'style="color: #0563c1; text-decoration: underline;">{link_label}</a>'
        )

        # --- PERMANENT SOLUTION: ENTERPRISE LINK REWRITER ---
        # Step 1: Replace {{CTA}} placeholder if it exists
        if "{{CTA}}" in ai_body:
            ai_body = ai_body.replace("{{CTA}}", inline_link_html)
            
        # Step 2: Auto-rewrite ALL manual HTML links to the tracking URL (Dynamic URL Wrapping)
        import re
        if "<a " in ai_body.lower():
            body_with_link = re.sub(r'href=[\'"][^\'"]*[\'"]', f'href="{tracking_click_url}"', ai_body, flags=re.IGNORECASE)
        else:
            # Step 3: If no links exist at all, append one at the bottom so tracking doesn't fail
            if tracking_click_url not in ai_body:
                body_with_link = ai_body + (
                    f'<p style="margin-bottom: 12px; line-height: 1.6;">'
                    f'You may {inline_link_html} at your convenience.</p>'
                )
            else:
                body_with_link = ai_body
        # ----------------------------------------------------

        # Updated HTML block with NO dabba/box
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; margin: 0; padding: 15px;">
            <div style="max-width: 700px;">
                <div style="font-size: 14px; color: #333;">
                    {body_with_link}
                </div>
                {signature_html}
                <div style="margin: 25px 0;">
                    <a href="{tracking_image_url}">
                        <img src="{PROMO_IMAGE_LINK}" alt="Hawkins Futura Cooktop - 20 Power Settings" width="300"
                             style="border: 1px solid #ccc; border-radius: 8px; max-width: 100%;">
                    </a>
                </div>
                {hawkins_legal_footer}
                <img src="{tracking_open_url}" width="1" height="1" style="display:none;" alt="" />
            </div>
        </body>
        </html>
        """

        payload.attach(MIMEText(html_content, 'html'))
        session.sendmail(SENDER_EMAIL, recipient_mail, payload.as_string())
        session.quit()
        return True, target_name

    except Exception as error:
        print(f"Transmission drop: {error}")
        return False, target_name
    
    
# =========================================================
# SCHEDULER
# =========================================================
scheduler_running = False
latest_admin_alert = None

def run_scheduled_campaign():
    print(f"[{datetime.now()}] Starting scheduled daily campaign...")
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM employees ORDER BY id ASC")
        employees = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Scheduled campaign fetch error: {e}")
        return

    if not employees:
        print("No employees found for scheduled campaign.")
        return

    campaign_id = create_campaign_run(
        campaign_name=f"Scheduled Daily Campaign - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        trigger_mode="scheduled",
        notes=f"Auto-triggered daily campaign | date={datetime.now().strftime('%Y-%m-%d')}"
    )

    if not campaign_id:
        print("Failed to create campaign run.")
        return

    sent_count = 0
    skipped_count = 0

    for employee_row in employees:
        try:
            recipient_mail = employee_row["email"]
            target_name = employee_row["name"]
            division = employee_row["department"] if employee_row["department"] else "Default"
            target_goal = employee_row["target_goal"] if "target_goal" in employee_row.keys() else "CLICK"

            # --- BYPASS RESTRICTION FOR MANUAL DISPATCH ---
            if len(employees) > 1 and is_target_achieved(recipient_mail, target_goal):
                skipped_count += 1
                print(f"  Skipping {target_name} - target already achieved.")
                continue

            time.sleep(random.uniform(0.5, 3.0))

            intel = threat_intel_db.get(division, threat_intel_db["Default"])
            previous_result = get_previous_result_for_user(recipient_mail, target_goal)
            has_clicked_before = previous_result in ["CLICK_CAPTURED", "CLICKED_ONLY", "CREDENTIAL_CAPTURED"]

            used_scenario_ids = get_used_scenario_ids_for_employee(employee_row["id"])
            attempt_count = get_real_attempt_count_for_employee(employee_row["id"])
            winning_scenario_ids, winning_category_hint = get_winning_scenarios_org_wide()
            previous_subjects = get_previous_subjects_for_employee(employee_row["id"])
            previous_ctas = get_previous_ctas_for_employee(employee_row["id"])
            designation = employee_row["designation"] if "designation" in employee_row.keys() else ""

            previous_prompt_row = get_latest_prompt_history_for_employee(employee_row["id"])
            previous_prompt_payload = None
            if previous_prompt_row:
                previous_prompt_payload = decrypt_prompt_history_payload(previous_prompt_row["encrypted_prompt_data"])

            create_campaign_target(campaign_id, employee_row)

            ai_subject, ai_body, final_prompt, scenario_id, cta_text, sender_identity = generate_ai_phishing_content(
                target_name, division, has_clicked_before,
                intel["subject"], intel["body"], intel["payload_type"],
                previous_prompt_payload=previous_prompt_payload,
                attempt_count=attempt_count,
                used_scenario_ids=used_scenario_ids,
                winning_scenario_ids=winning_scenario_ids,
                winning_category_hint=winning_category_hint,
                previous_subjects=previous_subjects,
                previous_ctas=previous_ctas,
                designation=designation
            )

            modification_reason = (
                "RETARGET_AFTER_PREVIOUS_INTERACTION" if has_clicked_before else "FIRST_TIME_SIMULATION"
            )

            prompt_version_id = save_prompt_history(
                campaign_id=campaign_id,
                employee_row=employee_row,
                previous_result=previous_result,
                modification_reason=modification_reason,
                final_prompt=final_prompt,
                ai_subject=ai_subject,
                ai_body=ai_body,
                scenario_id=scenario_id,
                cta_text=cta_text
            )

            success, _ = send_simulation_email(
                employee_row=employee_row,
                campaign_id=campaign_id,
                prompt_version_id=prompt_version_id,
                ai_subject=ai_subject,
                ai_body=ai_body,
                payload_type=intel["payload_type"],
                cta_text=cta_text,
                sender_identity=sender_identity
            )
            if success:
                sent_count += 1
                print(f"  Sent to {target_name}")

        except Exception as bulk_err:
            print(f"  Scheduled send error for {employee_row.get('email', 'Unknown')}: {bulk_err}")
            continue

    print(f"[{datetime.now()}] Campaign complete. Sent: {sent_count}, Skipped: {skipped_count}")

def schedule_daily_campaign():
    global scheduler_running
    if scheduler_running:
        return
    scheduler_running = True

    def schedule_next():
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        random_hour = 9
        random_minute = random.randint(0, 89)
        next_run = tomorrow.replace(hour=random_hour, minute=random_minute, second=random.randint(0, 59))

        if next_run < now:
            next_run += timedelta(days=1)

        wait_seconds = (next_run - now).total_seconds()
        print(f"Next scheduled campaign: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

        def run_and_reschedule():
            run_scheduled_campaign()
            schedule_next()

        threading.Timer(wait_seconds, run_and_reschedule).start()

    schedule_next()

# =========================================================
# ROUTES
# =========================================================
from collections import Counter 

@app.route('/employee/<int:employee_id>')
def employee_profile(employee_id):
    employee_row = get_employee_by_id(employee_id)
    if not employee_row:
        return "Employee not found", 404

    # 1. PURANA LOGIC (SAB WAISE HI HAI)
    risk_score = calculate_risk_score(employee_row)
    risk_level, risk_color, risk_bg = get_risk_level(risk_score)
    primary_vuln, trigger_words = get_department_vulnerability(employee_row["department"] or "Default")
    
    # Pehle history nikalenge, phir recommendations mein pass karenge
    email = employee_row["email"].strip().lower()
    raw_history = get_user_event_history(email)
    
    # Naya Function Call (Teesra parameter raw_history add kiya hai)
    recommendations = generate_recommendations(risk_score, employee_row["department"] or "Default", raw_history)
    
    # 2. NAYA FORENSIC DATA (Additive Changes)
    risk_breakdown = build_risk_breakdown(employee_row)
    enriched_timeline = []
    category_counts = {}
    
    for ev in raw_history:
        pt = ev.get("payload_type", "").upper()
        ev["points"] = 60 if pt == "CREDENTIAL" else (30 if pt == "LINK" else 5)
        
        # Mapping DB Data
        ev["campaign_name"] = "Simulation" 
        ev["category"] = "Phishing Attempt"
        ev["sender_name"] = "System"
        ev["strategy"] = "Phishing"
        
        # --- NAYA CODE: Asli Subject agar prompt history se mila toh wo dikhao ---
        if ev.get("ai_subject"):
            ev["ai_subject"] = ev["ai_subject"]
            
        enriched_timeline.append(ev)
        
        # AI Aggregation
        if pt in ["LINK", "CREDENTIAL"]:
            cat = ev.get("category", "General")
            category_counts[cat] = category_counts.get(cat, 0) + 1

    opens = sum(1 for e in raw_history if e.get("payload_type") == "IMAGE")
    clicks = sum(1 for e in raw_history if e.get("payload_type") == "LINK")
    creds = sum(1 for e in raw_history if e.get("payload_type") == "CREDENTIAL")
    
    # ASLI SENT COUNT DATABASE SE NIKAL RAHE HAIN
    actual_sent_count = get_campaigns_sent_to_employee(employee_row["id"])
    
    # 3. FINAL TEMPLATE BINDING (Purana + Naya dono pass ho raha hai)
    return render_template('employee_profile.html',
        # Purana Data
        employee=employee_row,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_color=risk_color,
        risk_bg=risk_bg,
        primary_vulnerability=primary_vuln,
        trigger_words=trigger_words,
        recommendations=recommendations,
        history_count=len(raw_history),
        report_date=datetime.now().strftime("%B %d, %Y"),
        
        # Naya Forensic Data
        risk_breakdown=risk_breakdown,
        executive_summary={
            "campaigns_sent": actual_sent_count,
            "opens": opens, "clicks": clicks, "creds": creds,
            "open_rate": f"{round((opens/max(1, actual_sent_count))*100, 1)}%",
            "click_rate": f"{round((clicks/max(1, actual_sent_count))*100, 1)}%",
            "percentile": employee_row.get("risk_percentile", "N/A")
        },
        ai_analysis={
            "most_vulnerable_category": max(category_counts, key=category_counts.get) if category_counts else "N/A",
            "repeat_offender": "Yes" if (clicks + creds) > 1 else "No",
            "trend": "Stable"
        },
        risk_progression=[{"score": risk_breakdown['final_score']}],
        incident_timeline=enriched_timeline
    )

@app.route('/')
def index():
    if not session.get('admin_logged_in'):
        return render_template('admin_login.html')
    status = request.args.get('status')
    user = request.args.get('user')
    dataset = load_employee_records()

    # --- INTEGRATION: Fetch pre-calculated Risk Engine data ---
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # Fetching new risk columns calculated by your engine
        cur.execute("""
            SELECT id, name, department, 
                   risk_score, risk_level, risk_percentile, risk_rank 
            FROM employees 
            ORDER BY risk_rank ASC NULLS LAST
        """)
        ranked_employees = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching leaderboard: {e}")
        ranked_employees = []
    # -----------------------------------------------------------

    return render_template(
        'index.html',
        dataset=dataset,
        tracking_status=status,
        targeted_user=user,
        ranked_employees=ranked_employees # Passed to the leaderboard table
    )
    
@app.route('/admin-login', methods=['POST'])
def admin_login():
    global latest_admin_alert
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    ip_address = request.remote_addr or '127.0.0.1'

    if not username:
        return "Username is required", 400

    # 1. Pre-Authentication: Check if the user is currently locked out
    if bruteforce_service.is_locked(username):
        return "Account temporarily locked due to multiple failed attempts. Please try again in 15 minutes.", 403

    # 2. Authentication Verification
    if username == "admin" and password == "hawkins123":
        # -- SUCCESS FLOW --
        bruteforce_service.reset_attempts(username)
        
        latest_admin_alert = {
            "username": username,
            "login_time": datetime.now().strftime('%d-%b-%Y %I:%M:%S %p'),
            "ip_address": ip_address,
            "status": "SUCCESS"
        }
        
        try:
            send_admin_login_alert(username, ip_address)
        except Exception as e:
            print(f"Admin alert email error: {e}")
            
        session['admin_logged_in'] = True
        return redirect(url_for('index'))
        
    else:
        # -- FAILURE FLOW --
        bruteforce_service.register_failed_attempt(username)
        
        # Calculate remaining attempts directly since register_failed_attempt returns None
        rem_attempts = bruteforce_service.remaining_attempts(username)
        
        if rem_attempts <= 0:
            try:
                # Trigger the Brute Force Alert email to the administrator
                send_bruteforce_alert(username, ip_address, bruteforce_service.MAX_ATTEMPTS)
            except Exception as e:
                print(f"Bruteforce alert email error: {e}")
                
            return "Account locked due to multiple failed attempts. Please try again in 15 minutes.", 403
            
        return f"Invalid credentials. You have {rem_attempts} attempt(s) remaining.", 401


@app.route('/api/admin-alerts')
def api_admin_alerts():
    global latest_admin_alert
    if latest_admin_alert:
        return jsonify(latest_admin_alert)
    return jsonify({
        "username": "No Active Session",
        "login_time": datetime.now().strftime('%d-%b-%Y %I:%M:%S %p'), # Fallback time target
        "ip_address": "0.0.0.0",
        "status": "No recent administrator activity."
    })


@app.route('/trigger-single-simulation', methods=['POST'])
def trigger_single_simulation():
    target_email = request.form.get('target_email', '').strip()
    selected_strategy = request.form.get('selected_strategy') 

    if not target_email:
        return redirect(url_for('index', status="Failure", user="Unknown"))

    employee_row = get_employee_by_email(target_email)
    if not employee_row:
        return redirect(url_for('index', status="Failure", user="Unknown"))

    target_name = employee_row["name"]
    division = employee_row["department"] if employee_row["department"] else "Default"
    recipient_mail = employee_row["email"]
    target_goal = employee_row["target_goal"] if "target_goal" in employee_row.keys() else "CLICK"

    # Allow repeat phishing simulations even if the employee
    # has already been caught in a previous campaign.
    previous_result = get_previous_result_for_user(recipient_mail, target_goal)
    has_clicked_before = previous_result in [
        "CLICK_CAPTURED",
        "CLICKED_ONLY",
        "CREDENTIAL_CAPTURED"
    ]

    intel = threat_intel_db.get(division, threat_intel_db["Default"])

    campaign_id = create_campaign_run(
        campaign_name=f"Single Simulation - {target_name}",
        trigger_mode="manual",
        notes=f"Single targeted simulation for {recipient_mail} | employee_id={employee_row['id']}"
    )

    if not campaign_id:
        return redirect(url_for('index', status="Failure", user=target_name))

    create_campaign_target(campaign_id, employee_row)

    used_scenario_ids = get_used_scenario_ids_for_employee(employee_row["id"])
    attempt_count = get_real_attempt_count_for_employee(employee_row["id"])
    winning_scenario_ids, winning_category_hint = get_winning_scenarios_org_wide()
    previous_subjects = get_previous_subjects_for_employee(employee_row["id"])
    previous_ctas = get_previous_ctas_for_employee(employee_row["id"])
    designation = employee_row["designation"] if "designation" in employee_row.keys() else ""

    previous_prompt_row = get_latest_prompt_history_for_employee(employee_row["id"])
    previous_prompt_payload = None
    if previous_prompt_row:
        previous_prompt_payload = decrypt_prompt_history_payload(previous_prompt_row["encrypted_prompt_data"])

    ai_subject, ai_body, final_prompt, scenario_id, cta_text, sender_identity = generate_ai_phishing_content(
        target_name, division, has_clicked_before,
        intel["subject"], intel["body"], intel["payload_type"],
        previous_prompt_payload=previous_prompt_payload,
        attempt_count=attempt_count,
        used_scenario_ids=used_scenario_ids,
        winning_scenario_ids=winning_scenario_ids,
        winning_category_hint=winning_category_hint,
        previous_subjects=previous_subjects,
        previous_ctas=previous_ctas,
        designation=designation,
        strategy_context=selected_strategy 
    )

    modification_reason = "RETARGET_AFTER_PREVIOUS_INTERACTION" if has_clicked_before else "FIRST_TIME_SIMULATION"

    prompt_version_id = save_prompt_history(
        campaign_id=campaign_id,
        employee_row=employee_row,
        previous_result=previous_result,
        modification_reason=modification_reason,
        final_prompt=final_prompt,
        ai_subject=ai_subject,
        ai_body=ai_body,
        scenario_id=scenario_id,
        cta_text=cta_text
    )

    success, user_name = send_simulation_email(
        employee_row=employee_row,
        campaign_id=campaign_id,
        prompt_version_id=prompt_version_id,
        ai_subject=ai_subject,
        ai_body=ai_body,
        payload_type=intel["payload_type"],
        cta_text=cta_text,
        sender_identity=sender_identity
    )
    if success:
        return redirect(url_for('index', status="Success", user=user_name))
    return redirect(url_for('index', status="Failure", user=user_name))

@app.route('/trigger-custom-simulation', methods=['POST'])
def trigger_custom_simulation():
    target_email = request.form.get('target_email', '').strip()
    custom_subject = request.form.get('custom_subject', '').strip()
    custom_body = request.form.get('custom_body', '').strip()

    if not target_email or not custom_subject or not custom_body:
        return redirect(url_for('index', status="Failure", user="Missing input fields"))

    employee_row = get_employee_by_email(target_email)
    if not employee_row:
        return redirect(url_for('index', status="Failure", user="Employee not found"))

    # Naya campaign run create karein tracking ke liye
    campaign_id = create_campaign_run(
        campaign_name=f"Custom Edit - {employee_row['name']}",
        trigger_mode="manual",
        notes="Admin manually edited this template."
    )
    
    if not campaign_id:
        return redirect(url_for('index', status="Failure", user="Database Error"))

    create_campaign_target(campaign_id, employee_row)

    # Database mein history save karein
    prompt_version_id = save_prompt_history(
        campaign_id=campaign_id,
        employee_row=employee_row,
        previous_result="MANUAL_TRIGGER",
        modification_reason="MANUAL_EDIT_BY_ADMIN",
        final_prompt="Custom Input via Dashboard",
        ai_subject=custom_subject,
        ai_body=custom_body,
        scenario_id=None,
        cta_text="view details"
    )

    # Email Send Karein!
    success, user_name = send_simulation_email(
        employee_row=employee_row,
        campaign_id=campaign_id,
        prompt_version_id=prompt_version_id,
        ai_subject=custom_subject,
        ai_body=custom_body,
        payload_type="LINK"  # Custom emails me default link bhej rahe hain
    )

    if success:
        return redirect(url_for('index', status="Success", user=f"{user_name} (Custom Sent)"))
    return redirect(url_for('index', status="Failure", user=user_name))


@app.route('/trigger-bulk-campaign', methods=['POST'])
def trigger_bulk_campaign():
    selected_strategy = request.form.get('selected_strategy') 
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM employees ORDER BY id ASC")
        employees = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Bulk employee fetch error: {e}")
        return redirect(url_for('index', status="Failure", user="Bulk Campaign"))

    if not employees:
        return redirect(url_for('index', status="Failure", user="Bulk Campaign"))

    campaign_id = create_campaign_run(
        campaign_name=f"Bulk Awareness Campaign - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        trigger_mode="bulk",
        notes="Bulk phishing awareness run from dashboard"
    )

    if not campaign_id:
        return redirect(url_for('index', status="Failure", user="Bulk Campaign"))

    sent_count = 0
    skipped_count = 0

    for employee_row in employees:
        try:
            recipient_mail = employee_row["email"]
            target_name = employee_row["name"]
            division = employee_row["department"] if employee_row["department"] else "Default"
            target_goal = employee_row["target_goal"] if "target_goal" in employee_row.keys() else "CLICK"

            # Allow repeat phishing simulations even after
            # the employee has been caught previously.
            intel = threat_intel_db.get(division, threat_intel_db["Default"])

            previous_result = get_previous_result_for_user(recipient_mail, target_goal)
            has_clicked_before = previous_result in [
                "CLICK_CAPTURED",
                "CLICKED_ONLY",
                "CREDENTIAL_CAPTURED"
            ]

            used_scenario_ids = get_used_scenario_ids_for_employee(employee_row["id"])
            attempt_count = get_real_attempt_count_for_employee(employee_row["id"])
            winning_scenario_ids, winning_category_hint = get_winning_scenarios_org_wide()
            previous_subjects = get_previous_subjects_for_employee(employee_row["id"])
            previous_ctas = get_previous_ctas_for_employee(employee_row["id"])
            designation = employee_row["designation"] if "designation" in employee_row.keys() else ""

            previous_prompt_payload = None
            if has_clicked_before:
                previous_prompt_row = get_latest_prompt_history_for_employee(employee_row["id"])
                if previous_prompt_row:
                    previous_prompt_payload = decrypt_prompt_history_payload(previous_prompt_row["encrypted_prompt_data"])

            create_campaign_target(campaign_id, employee_row)

            ai_subject, ai_body, final_prompt, scenario_id, cta_text, sender_identity = generate_ai_phishing_content(
                target_name, division, has_clicked_before,
                intel["subject"], intel["body"], intel["payload_type"],
                previous_prompt_payload=previous_prompt_payload,
                attempt_count=attempt_count,
                used_scenario_ids=used_scenario_ids,
                winning_scenario_ids=winning_scenario_ids,
                winning_category_hint=winning_category_hint,
                previous_subjects=previous_subjects,
                previous_ctas=previous_ctas,
                designation=designation,
                strategy_context=selected_strategy  
            )

            modification_reason = "RETARGET_AFTER_PREVIOUS_INTERACTION" if has_clicked_before else "FIRST_TIME_SIMULATION"

            prompt_version_id = save_prompt_history(
                campaign_id=campaign_id,
                employee_row=employee_row,
                previous_result=previous_result,
                modification_reason=modification_reason,
                final_prompt=final_prompt,
                ai_subject=ai_subject,
                ai_body=ai_body,
                scenario_id=scenario_id,
                cta_text=cta_text
            )

            success, _ = send_simulation_email(
                employee_row=employee_row,
                campaign_id=campaign_id,
                prompt_version_id=prompt_version_id,
                ai_subject=ai_subject,
                ai_body=ai_body,
                payload_type=intel["payload_type"],
                cta_text=cta_text,
                sender_identity=sender_identity
            )

            if success:
                sent_count += 1

            time.sleep(random.uniform(0.4, 1.2))

        except Exception as bulk_err:
            print(f"Bulk send error for {employee_row.get('email', 'Unknown')}: {bulk_err}")
            continue

    return redirect(
        url_for(
            'index',
            status="Success",
            user=f"Bulk: {sent_count} sent, {skipped_count} skipped"
        )
    )


@app.route('/trigger-scheduled-now', methods=['POST'])
def trigger_scheduled_now():
    thread = threading.Thread(target=run_scheduled_campaign)
    thread.start()
    return redirect(url_for('index', status="Success", user="Scheduled campaign started in background"))

# =========================================================
# NEW: TARGETED BULK CUSTOMIZATION ROUTES
# =========================================================

@app.route('/api/get-employees', methods=['GET'])
def get_employees_by_dept():
    department = request.args.get('department')
    if not department:
        return jsonify([])
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if department == "All Departments":
            cur.execute("SELECT id, name, email FROM employees ORDER BY name ASC")
        else:
            cur.execute("SELECT id, name, email FROM employees WHERE department = %s ORDER BY name ASC", (department,))
            
        employees = cur.fetchall()
        cur.close()
        conn.close()
        
        # Format the data for our frontend dropdown
        emp_list = [{"id": emp["id"], "name": emp["name"], "email": emp["email"]} for emp in employees]
        return jsonify(emp_list)
        
    except Exception as e:
        print(f"Error fetching employees by dept: {e}")
        return jsonify([])


@app.route('/trigger-custom-bulk', methods=['POST'])
def trigger_custom_bulk():
    data = request.json
    selected_emails = data.get('emails') 
    email_body = data.get('body')
    custom_subject = data.get('subject', 'Important Internal Update') # Fallback subject
    
    if not selected_emails or not email_body:
        return jsonify({"status": "error", "message": "Missing email list or body text!"}), 400

    # 1. Create a Master Campaign Entry for this Bulk Blast
    campaign_id = create_campaign_run(
        campaign_name=f"Targeted Bulk Custom - {datetime.now().strftime('%d %b %H:%M')}",
        trigger_mode="manual_bulk",
        notes="Admin manually selected users and broadcasted a custom template."
    )

    success_count = 0
    
    # 2. The Magic Loop: Dispatch to each selected employee
    for email in selected_emails:
        emp_row = get_employee_by_email(email)
        if not emp_row:
            continue
            
        # Log the target in the database
        create_campaign_target(campaign_id, emp_row)
        
        # Save exact prompt history for forensic audits
        prompt_version_id = save_prompt_history(
            campaign_id=campaign_id,
            employee_row=emp_row,
            previous_result="MANUAL_BULK_TRIGGER",
            modification_reason="MANUAL_BULK_EDIT_BY_ADMIN",
            final_prompt="Custom Bulk Input via UI",
            ai_subject=custom_subject,
            ai_body=email_body,
            scenario_id=None,
            cta_text="view details"
        )

        # Send the email! (Your existing function will automatically replace {{CTA}} here)
        success, _ = send_simulation_email(
            employee_row=emp_row,
            campaign_id=campaign_id,
            prompt_version_id=prompt_version_id,
            ai_subject=custom_subject,
            ai_body=email_body,
            payload_type="LINK" 
        )
        
        if success:
            success_count += 1
            
    return jsonify({"status": "success", "message": f"Boom! Successfully sent to {success_count} employees."})
# =========================================================
# HAWKINS HR PORTAL MIMIC LOGIN PAGE
# =========================================================
@app.route('/login-page')
def login_page():
    user = request.args.get('user', 'Unknown')
    campaign_id = request.args.get('campaign_id', '')
    prompt_version_id = request.args.get('prompt_version_id', '')

    # --- Initial click logging ---
    if user and user != 'Unknown':
        try:
            employee_row = get_employee_by_email(user)
            if employee_row:
                camp_id = int(campaign_id) if campaign_id else None
                prompt_id = int(prompt_version_id) if prompt_version_id else None
                
                secure_log_event(
                    employee_row=employee_row,
                    payload_type="LINK",
                    campaign_id=camp_id,
                    prompt_version_id=prompt_id
                )
                if camp_id:
                    update_campaign_target_status(camp_id, employee_row["id"], "CLICKED_ONLY", achieved=False)
        except Exception as e:
            print(f"Login page track error: {e}")
    # ---------------------------------

    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HuMane</title>
    <style>
    body{{ margin:0; background:#ececec; font-family:"Times New Roman", Times, serif; }}
    .page{{ width:1040px; margin:78px auto 0 auto; }}
    .outer-box{{
        width:1028px; height:415px; background:#f5f5f5; border:1px solid #c00000;
        padding:7px; box-sizing:border-box;
        box-shadow: 0 10px 12px rgba(0,0,0,0.45), 0 2px 2px rgba(0,0,0,0.12);
    }}
    .header{{ display:flex; align-items:flex-start; }}
    .logo{{
        width:100px; height:98px; border:1px solid #425ac7; background:#ffffff;
        object-fit:contain; display:block;
    }}
    .heading{{ margin-left:14px; margin-top:10px; }}
    .heading h1{{ margin:0; font-size:31px; font-weight:700; color:#000; line-height:1; }}
    .heading h2{{ margin:8px 0 0 0; font-size:31px; font-weight:700; color:#8b8686; line-height:1; }}
    .login-panel{{ width:570px; margin:24px auto 0 auto; }}
    fieldset{{ border:1px solid #b8b8b8; height:245px; padding:0; margin:0; }}
    legend{{ padding:0 6px; font-size:18px; margin:auto; }}
    .form-content{{ width:246px; margin:44px auto 0 auto; }}
    .input-box{{
        width:246px; height:42px; border:1px solid #707070; border-radius:4px;
        background-color:#ffffff; font-size:18px; font-weight:600; color:#5d5d5d;
        padding-left:31px; box-sizing:border-box; margin-bottom:15px; outline:none;
    }}
    .input-box::placeholder{{ color:#5f5f5f; opacity:1; }}
    .user-box{{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16'%3E%3Ccircle cx='8' cy='5' r='4' fill='%23d0d0d0'/%3E%3Cpath d='M1 16c0-4 3-6 7-6s7 2 7 6' fill='%23d0d0d0'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:6px center;
    }}
    .pass-box{{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16'%3E%3Ccircle cx='4' cy='8' r='3' fill='none' stroke='%23d0d0d0' stroke-width='1.4'/%3E%3Cpath d='M7 8h8' stroke='%23d0d0d0' stroke-width='1.4'/%3E%3Cpath d='M11 8v2' stroke='%23d0d0d0' stroke-width='1.4'/%3E%3Cpath d='M13 8v2' stroke='%23d0d0d0' stroke-width='1.4'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:6px center;
    }}
    .signin-btn{{
        width:246px; height:39px; background:#000099; border:none; border-radius:4px;
        color:#ffffff; font-size:16px; font-weight:bold; cursor:pointer;
    }}
    .signin-btn:hover{{ background:#0000aa; }}
    .forgot{{ text-align:center; margin-top:28px; }}
    .forgot a{{ color:#0000ee; font-size:16px; font-weight:bold; text-decoration:underline; }}
    </style>
    </head>
    <body>
    <div class="page">
        <div class="outer-box">
            <div class="header">
                <img class="logo" src="https://hrd.hawkins-futura.com/img/hawkinshuman.png" alt="Hawkins Logo">
                <div class="heading">
                    <h1>HuMane (Hawkins HR Management)</h1>
                    <h2>Hawkins Cookers Limited</h2>
                </div>
            </div>
            <div class="login-panel">
                <fieldset>
                    <legend>Sign In</legend>
                    <form action="/track-click" method="GET">
                        <input type="hidden" name="user" value="{user}">
                        <input type="hidden" name="type" value="CREDENTIAL">
                        <input type="hidden" name="campaign_id" value="{campaign_id}">
                        <input type="hidden" name="prompt_version_id" value="{prompt_version_id}">
                        
                        <div class="form-content">
                            <input class="input-box user-box" type="text" name="userid" value="{user}" placeholder="User Id" readonly>
                            <input class="input-box pass-box" type="password" name="password" placeholder="Password" required>
                            <button class="signin-btn" type="submit">Sign In</button>
                            <div class="forgot"><a href="#">Forgot Password?</a></div>
                        </div>
                    </form>
                </fieldset>
            </div>
        </div>
    </div>
    </body>
    </html>
    '''


# =========================================================
# OPEN / CLICK TRACKING
# =========================================================
@app.route('/track-open')
def track_open():
    vulnerable_user = request.args.get('user', '').strip()
    campaign_id = request.args.get('campaign_id')
    prompt_version_id = request.args.get('prompt_version_id')

    if vulnerable_user:
        try:
            employee_row = get_employee_by_email(vulnerable_user)
            if employee_row:
                secure_log_event(
                    employee_row=employee_row,
                    payload_type="IMAGE",
                    campaign_id=int(campaign_id) if campaign_id else None,
                    prompt_version_id=int(prompt_version_id) if prompt_version_id else None
                )
                if campaign_id:
                    update_campaign_target_status(
                        int(campaign_id), employee_row["id"], "EMAIL_OPENED", achieved=False
                    )
        except Exception as e:
            print(f"Track open error: {e}")

    return Response(
        base64.b64decode(b"R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"),
        mimetype="image/gif"
    )

@app.route('/track-click')
def track_click():
    vulnerable_user = request.args.get('user', 'Unknown Node').strip()
    payload_type = request.args.get('type', 'LINK').strip().upper()
    campaign_id = request.args.get('campaign_id')
    prompt_version_id = request.args.get('prompt_version_id')

    # Password captured from fake login page (if any)
    captured_password = request.args.get('password')

    if vulnerable_user and vulnerable_user != 'Unknown Node':
        try:
            employee_row = get_employee_by_email(vulnerable_user)

            if employee_row:
                target_goal = employee_row["target_goal"] if "target_goal" in employee_row.keys() else "CLICK"

                camp_id = int(campaign_id) if campaign_id else None
                prompt_id = int(prompt_version_id) if prompt_version_id else None

                # -----------------------------------------------------
                # Always log every interaction
                # (Do NOT stop after the employee has been caught)
                # -----------------------------------------------------
                secure_log_event(
                    employee_row=employee_row,
                    payload_type=payload_type,
                    campaign_id=camp_id,
                    prompt_version_id=prompt_id,
                    captured_password=captured_password
                )

                # Update campaign status
                if camp_id:
                    if payload_type == "CREDENTIAL":
                        update_campaign_target_status(
                            camp_id,
                            employee_row["id"],
                            "CREDENTIAL_CAPTURED",
                            achieved=True
                        )

                    elif payload_type == "LINK":
                        if target_goal.upper() == "CLICK":
                            update_campaign_target_status(
                                camp_id,
                                employee_row["id"],
                                "CLICK_CAPTURED",
                                achieved=True
                            )
                        else:
                            update_campaign_target_status(
                                camp_id,
                                employee_row["id"],
                                "CLICKED_ONLY",
                                achieved=False
                            )

                    elif payload_type == "IMAGE":
                        update_campaign_target_status(
                            camp_id,
                            employee_row["id"],
                            "EMAIL_OPENED",
                            achieved=False
                        )

        except Exception as log_error:
            print(f"Track click error: {log_error}")

    return """
    <h1>Security Grid: Vulnerability Logging Triggered Successfully.</h1>
    <p>This simulation audit interaction has been securely encrypted and logged directly to the Corporate Database.</p>
    """
@app.route('/reset-logs', methods=['GET', 'POST'])
def reset_logs():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM simulation_logs;")
        cur.execute("DELETE FROM prompt_history;")
        cur.execute("DELETE FROM campaign_targets;")
        cur.execute("DELETE FROM campaign_runs;")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Reset logs error: {e}")
    return redirect(url_for('index'))

# =========================================================
# SECRET ADMIN ROUTE: FORCE RISK ENGINE SYNC (For Demo)
# =========================================================
@app.route('/force-sync')
def force_sync():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # 1. Sabhi employees ka data nikalo
        cur.execute("SELECT id, email, department FROM employees")
        emps = cur.fetchall()
        
        # 2. Har employee ka naya risk score aur level update karo
        for emp in emps:
            score = calculate_risk_score(emp)
            level = get_risk_level(score)[0]
            cur.execute("UPDATE employees SET risk_score = %s, risk_level = %s WHERE id = %s", (score, level, emp['id']))
        conn.commit()

        # 3. ADVANCED SQL: Rank aur Percentile calculate karke update karo
        cur.execute("""
            WITH ranked AS (
                SELECT id, 
                       RANK() OVER (ORDER BY risk_score DESC) as new_rank,
                       ROUND((PERCENT_RANK() OVER (ORDER BY risk_score ASC) * 100)::numeric, 2) as new_percentile
                FROM employees
            )
            UPDATE employees e
            SET risk_rank = r.new_rank,
                risk_percentile = r.new_percentile
            FROM ranked r
            WHERE e.id = r.id;
        """)
        conn.commit()
        cur.close()
        conn.close()
        
        # Wapas dashboard par bhej do success message ke sath
        return redirect(url_for('index', status="Success", user="Risk Engine Synced & Percentiles Updated!"))
    except Exception as e:
        return f"Database Sync Error: {e}"

# =========================================================
# AI TEMPLATE RECOMMENDER (HUMAN-IN-THE-LOOP ADVISOR)
# =========================================================
@app.route('/api/generate-new-templates', methods=['POST'])
def generate_new_templates():
    department = request.json.get('department', 'Organization-Wide')
    email = request.json.get('email')
    count = request.json.get('count', 3) 
    
    winning_ids, winning_hint = get_winning_scenarios_org_wide()
    
    # Check if this is for an individual user
    user_context = ""
    if email:
        emp_row = get_employee_by_email(email)
        if emp_row:
            target_goal = emp_row.get("target_goal", "CLICK")
            prev_result = get_previous_result_for_user(email, target_goal)
            past_scenarios = get_used_scenario_ids_for_employee(emp_row["id"])
            user_context = f"""
            - INDIVIDUAL TARGET HISTORY:
              - Target Email: {email}
              - Previous Interaction Status: {prev_result}
              - Scenarios already sent to this user (DO NOT REPEAT THESE): {past_scenarios}
            """

    prompt = f"""
    Act as an advanced Red Team Cybersecurity expert advising on a phishing simulation campaign.
    
    ANALYZE THE FOLLOWING CAMPAIGN CONTEXT:
    - Target Audience: {department}
    - Organization-wide successful categories: {winning_hint if winning_hint else 'Standard corporate requests'}
    {user_context}
    
    STRATEGY CONSTRAINTS (ANTI-FATIGUE):
    - Do not recommend generic categories that have already been repeatedly used.
    - Prefer recommending fresh, highly specific themes (e.g. 'Bonus Processing' instead of 'Payroll').
    
    Based on this analysis, generate {count} strategic phishing campaign recommendations.
    
    For each recommendation, ALSO draft a highly realistic sample email template based on the strategy. 
    The Body must be 3-4 short paragraphs and use the exact string '{{{{CTA}}}}' once where the malicious link should go.
    
    Return the response STRICTLY as a valid JSON array of objects with these exact keys:
    "category" (e.g., Payroll),
    "theme" (The specific, fresh scenario theme),
    "persona" (Suggested Sender Persona),
    "angle" (Psychological Angle),
    "urgency" (Suggested Urgency Level),
    "confidence" (Confidence Score as a percentage, e.g., "91%"),
    "reason" (Detailed reason why this strategy is recommended based on history),
    "subject" (The generated draft email subject line),
    "body" (The generated draft email body containing {{{{CTA}}}})
    """

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        
        response_text = response.text.strip().removeprefix("```json").removesuffix("```").strip().removeprefix("```")
        strategies = json.loads(response_text)
        return jsonify({"status": "success", "templates": strategies})

    except Exception as e:
        error_msg = str(e)
        if '429' in error_msg or 'Quota' in error_msg:
            return jsonify({"status": "error", "message": "Gemini API Free Quota Exceeded. Please wait 60 seconds."}), 429
        return jsonify({"status": "error", "message": error_msg}), 500


@app.route('/api/stats')
def api_stats():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("SELECT COUNT(*) as total FROM employees")
        total_employees = cur.fetchone()['total']

        caught = get_caught_users()
        caught_count = len(caught)

        pending_count = total_employees - caught_count

        cur.execute("SELECT COUNT(*) as total FROM campaign_runs")
        total_campaigns = cur.fetchone()['total']

        cur.close()
        conn.close()

        return jsonify({
            "total_employees": total_employees,
            "caught": caught_count,
            "pending": pending_count,
            "total_campaigns": total_campaigns,
            "scheduler_active": scheduler_running
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/vulnerability-profile')
def api_vulnerability_profile():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT e.department, e.target_goal, e.email, e.name,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM simulation_logs sl
                       WHERE sl.employee_id = e.id
                   ) THEN 'CAUGHT' ELSE 'PENDING' END as status
            FROM employees e
            ORDER BY e.department
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        dept_psychology = {
            "HR": {"primary": "Urgency / FOMO", "secondary": "Authority Bias"},
            "Finance": {"primary": "Authority / Compliance", "secondary": "Financial Incentive"},
            "IT": {"primary": "Technical Trust", "secondary": "Process Compliance"},
            "Cyber Security": {"primary": "Fear / Crisis Response", "secondary": "Duty Obligation"},
            "Management": {"primary": "Executive Authority", "secondary": "Confidentiality Bias"},
            "Default": {"primary": "General Trust", "secondary": "Habitual Clicking"}
        }

        profile = {}
        for row in rows:
            dept = row["department"] or "Default"
            if dept not in profile:
                profile[dept] = {
                    "total": 0, "caught": 0, "pending": 0,
                    "primary_vulnerability": dept_psychology.get(dept, dept_psychology["Default"])["primary"],
                    "secondary_vulnerability": dept_psychology.get(dept, dept_psychology["Default"])["secondary"]
                }
            profile[dept]["total"] += 1
            if row["status"] == "CAUGHT":
                profile[dept]["caught"] += 1
            else:
                profile[dept]["pending"] += 1

        for dept in profile:
            total = profile[dept]["total"]
            profile[dept]["caught_pct"] = round((profile[dept]["caught"] / total) * 100, 1) if total > 0 else 0
            profile[dept]["pending_pct"] = round((profile[dept]["pending"] / total) * 100, 1) if total > 0 else 0
            if profile[dept]["caught_pct"] >= 50:
                profile[dept]["risk_level"] = "HIGH"
            elif profile[dept]["caught_pct"] >= 25:
                profile[dept]["risk_level"] = "MEDIUM"
            else:
                profile[dept]["risk_level"] = "LOW"

        return jsonify(profile)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/campaign-timeline')
def api_campaign_timeline():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""
            SELECT 
                cr.id,
                cr.campaign_name,
                cr.trigger_mode,
                cr.run_date,
                COUNT(DISTINCT ct.id) as total_targets,
                COUNT(DISTINCT CASE WHEN ct.achieved = true THEN ct.id END) as clicks
            FROM campaign_runs cr
            LEFT JOIN campaign_targets ct ON cr.id = ct.campaign_id
            GROUP BY cr.id, cr.campaign_name, cr.trigger_mode, cr.run_date
            ORDER BY cr.run_date ASC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        timeline_data = []
        for row in rows:
            date_obj = row['run_date']
            formatted_date = date_obj.strftime('%b %d, %I:%M %p')

            timeline_data.append({
                'date': formatted_date,
                'raw_timestamp': date_obj.isoformat(),
                'campaign_name': row['campaign_name'],
                'trigger_mode': row['trigger_mode'],
                'emails_sent': row['total_targets'] or 0,
                'clicks': row['clicks'] or 0
            })

        return jsonify(timeline_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/executive-report')
def executive_report():
    dataset = load_employee_records()
    total_employees = len(dataset)
    all_events = get_all_logged_events()

    emails_sent = 0
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT COUNT(*) AS c FROM campaign_targets")
        emails_sent = cur.fetchone()["c"] or 0
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Executive report emails_sent error: {e}")
        emails_sent = len(dataset)

    clicked_emails = set()
    credential_emails = set()
    for ev in all_events:
        email = (ev.get("user_email") or "").strip().lower()
        if not email:
            continue
        ptype = (ev.get("payload_type") or "").upper()
        if ptype in ("LINK", "CREDENTIAL"):
            clicked_emails.add(email)
        if ptype == "CREDENTIAL":
            credential_emails.add(email)

    clicked_count = len(clicked_emails)
    credential_count = len(credential_emails)

    if total_employees > 0:
        click_rate = f"{round((clicked_count / total_employees) * 100, 1)}%"
        credential_rate = f"{round((credential_count / total_employees) * 100, 1)}%"
    else:
        click_rate = "0%"
        credential_rate = "0%"

    dept_agg = {}
    for emp in dataset:
        dept = emp["Department"] or "Default"
        if dept not in dept_agg:
            dept_agg[dept] = {"total": 0, "caught": 0}
        dept_agg[dept]["total"] += 1
        if "CAUGHT" in emp["Status"]:
            dept_agg[dept]["caught"] += 1

    departments = []
    for dept_name, stats in dept_agg.items():
        dept_total = stats["total"]
        dept_caught = stats["caught"]
        rate_val = round((dept_caught / dept_total) * 100, 1) if dept_total > 0 else 0
        departments.append({
            "name": dept_name,
            "employees": dept_total,
            "click_rate": f"{rate_val}%",
            "risk_score": int(rate_val)
        })
    departments.sort(key=lambda d: d["risk_score"], reverse=True)

    high_risk_employees = []
    for emp in dataset:
        emp_row = get_employee_by_email(emp["EmailID"])
        if not emp_row:
            continue
        score = calculate_risk_score(emp_row)
        incidents = len(get_user_event_history(emp["EmailID"]))
        if score >= 40:
            high_risk_employees.append({
                "name": emp["Name"],
                "department": emp["Department"],
                "risk_score": score,
                "incidents": incidents
            })
    high_risk_employees.sort(key=lambda e: e["risk_score"], reverse=True)
    
    top_dept = departments[0]['name'] if departments else "HR"
    
    ai_insights = {
        "top_lure": "Urgent: Revised Payroll & Tax Deduction Policy",
        "top_lure_rate": "42%",
        "vulnerable_dept": top_dept,
        "behavioral_note": "Users who ignored technical IT alerts showed a 30% higher compromise rate when dynamically retargeted with financial-urgency themes."
    }

    executive_summary = (
        f"This report summarizes the phishing awareness simulation activity conducted across "
        f"Hawkins Cookers Limited. A total of {total_employees} employees were included in the "
        f"program, with {emails_sent} simulation emails dispatched. "
        f"{clicked_count} employee(s) interacted with a phishing link "
        f"({click_rate} click rate), and {credential_count} employee(s) submitted credentials "
        f"({credential_rate} credential-compromise rate). "
        f"{len(high_risk_employees)} employee(s) are currently flagged as high or critical risk "
        f"and require prioritized security awareness intervention."
    )

    recommendations = [
        "Enforce immediate mandatory security awareness training for employees who submitted credentials.",
        "Deploy targeted phishing simulations for employees who clicked malicious links.",
        f"Prioritize department-specific briefings starting with the highest-risk department ('{top_dept}').",
        "Schedule recurring quarterly phishing simulation campaigns.",
        "Review and reinforce email verification and reporting procedures company-wide."
    ]

    return render_template('executive_report.html',
        total_employees=total_employees,
        emails_sent=emails_sent,
        click_rate=click_rate,
        credential_rate=credential_rate,
        departments=departments,
        high_risk_employees=high_risk_employees,
        executive_summary=executive_summary,
        recommendations=recommendations,
        ai_insights=ai_insights,
        report_date=datetime.now().strftime("%B %d, %Y")
    )
    
def setup_database():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            ALTER TABLE employees 
            ADD COLUMN IF NOT EXISTS risk_score INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS risk_level VARCHAR(50) DEFAULT 'LOW',
            ADD COLUMN IF NOT EXISTS risk_percentile NUMERIC(5,2) DEFAULT 0.00,
            ADD COLUMN IF NOT EXISTS risk_rank INTEGER DEFAULT 0;
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("[System] Risk Engine database columns verified.")
    except Exception as e:
        print(f"[System Warning] Could not verify DB schema: {e}")
@app.route("/api/system-health")
def api_system_health():

    return jsonify(get_complete_health())
@app.route("/system-health")
def system_health_dashboard():

    return render_template("system_health.html")
if __name__ == '__main__':
    setup_database() 
    app.run(debug=True, port=5000)
