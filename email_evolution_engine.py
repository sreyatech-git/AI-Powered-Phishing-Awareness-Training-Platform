# email_evolution_engine.py

import random
from google import genai
from threat_scenarios import THREAT_SCENARIOS
from datetime import datetime
import json
from campaign_quality_engine import (
    validate_generated_campaign,
    print_validation_report
)

SCENARIO_CATEGORY = {
    "hr_payroll_policy": "Payroll",
    "hr_attendance_correction": "Attendance",
    "hr_benefits_enrollment": "Benefits",
    "fin_invoice_payment": "Procurement",
    "fin_expense_reimbursement": "Expenses",
    "fin_tax_clearance": "Tax",
    "it_m365_password": "Identity",
    "it_vpn_certificate": "Infrastructure",
    "it_software_license": "Licensing",
    "cs_zero_day_alert": "Threat",
    "cs_incident_report": "Incident",
    "cs_mfa_enrollment": "Identity",
    "mgmt_board_materials": "Governance",
    "mgmt_confidential_request": "Executive",
    "mgmt_strategy_feedback": "Strategy",
    "def_general_update": "SystemMaintenance",
    "def_profile_review": "ProfileUpdate",
    # New Departments
    "sales_crm_update": "CRM",
    "sales_commission_dispute": "Payroll",
    "sales_bec_contract": "Legal",
    "sales_executive_discount": "Executive",
    "mktg_social_media_alert": "SocialMedia",
    "mktg_budget_approval": "Finance",
    "mktg_influencer_invoice": "Procurement",
    "mktg_brand_crisis": "PR",
    "supply_vendor_delay": "Logistics",
    "supply_logistics_portal": "Infrastructure",
    "supply_bec_bank_change": "Procurement",
    "supply_ai_disruption": "Strategy",
    "legal_nda_signature": "Legal",
    "legal_policy_violation": "Compliance",
    "legal_court_summons": "Legal",
    "legal_exec_contract_bypass": "Executive",
    "support_escalated_complaint": "CustomerRelations",
    "support_sla_breach": "Operations",
    "support_gdpr_violation": "Compliance",
    "support_weaponized_pdf": "Threat",
    "rnd_patent_issue": "IP",
    "rnd_design_review": "Engineering",
    "rnd_ip_theft": "Threat",
    "rnd_fake_collaboration": "Strategy",
    "admin_office_policy": "Facilities",
    "admin_parking_allocation": "Facilities",
    "admin_bec_vendor_invoice": "Procurement",
    "admin_safety_compliance": "Compliance",
}

SENDER_IDENTITY_POOL = {
    "Payroll":           {"team": "Payroll Team", "email": "payroll@hawkinscookers.com"},
    "Attendance":        {"team": "HR Operations", "email": "hr.operations@hawkinscookers.com"},
    "Benefits":          {"team": "Employee Benefits Desk", "email": "benefits@hawkinscookers.com"},
    "Procurement":       {"team": "Procurement Team", "email": "procurement@hawkinscookers.com"},
    "Expenses":          {"team": "Accounts Payable", "email": "accounts@hawkinscookers.com"},
    "Tax":               {"team": "Finance & Taxation", "email": "taxation@hawkinscookers.com"},
    "Identity":          {"team": "Identity & Access Management", "email": "iam@hawkinscookers.com"},
    "Infrastructure":    {"team": "IT Infrastructure", "email": "it.infra@hawkinscookers.com"},
    "Licensing":         {"team": "IT Asset Management", "email": "it.assets@hawkinscookers.com"},
    "Threat":            {"team": "Security Operations Center", "email": "soc@hawkinscookers.com"},
    "Incident":          {"team": "Incident Response Team", "email": "irt@hawkinscookers.com"},
    "Governance":        {"team": "Board Office", "email": "board@hawkinscookers.com"},
    "Executive":         {"team": "Executive Office", "email": "exec.office@hawkinscookers.com"},
    "Strategy":          {"team": "Strategy & Planning", "email": "strategy@hawkinscookers.com"},
    "SystemMaintenance": {"team": "IT Service Desk", "email": "servicedesk@hawkinscookers.com"},
    "ProfileUpdate":     {"team": "HR Shared Services", "email": "hr.shared@hawkinscookers.com"},
    "CRM": {"team": "CRM Administration", "email": "crm.admin@hawkinscookers.com"},
    "SocialMedia": {"team": "Digital Marketing", "email": "social@hawkinscookers.com"},
    "PR": {"team": "Corporate PR", "email": "pr@hawkinscookers.com"},
    "Logistics": {"team": "Global Logistics", "email": "logistics@hawkinscookers.com"},
    "Compliance": {"team": "Compliance Office", "email": "compliance@hawkinscookers.com"},
    "CustomerRelations": {"team": "Client Success", "email": "client.success@hawkinscookers.com"},
    "Operations": {"team": "Service Operations", "email": "operations@hawkinscookers.com"},
    "IP": {"team": "Intellectual Property Desk", "email": "ip.desk@hawkinscookers.com"},
    "Engineering": {"team": "Engineering Control", "email": "engineering@hawkinscookers.com"},
    "Facilities": {"team": "Facilities & Safety", "email": "facilities.safety@hawkinscookers.com"},
}

def _dept_key(department: str) -> str:
    return department if department in THREAT_SCENARIOS else "Default"

def _category_of(scenario_id: str) -> str:
    return SCENARIO_CATEGORY.get(scenario_id, "General")

def resolve_sender_identity(scenario: dict, department: str) -> dict:
    category = _category_of(scenario["id"])
    identity = SENDER_IDENTITY_POOL.get(category)
    if identity:
        return {"name": identity["team"], "email": identity["email"]}
    return sender_profiles.get(department, sender_profiles["Default"])

def select_next_scenario(department: str, used_ids: list,
                         used_categories: list = None,
                         preferred_ids: list = None) -> dict:
    dept = _dept_key(department)
    preferred_ids = preferred_ids or []
    used_categories = used_categories or []

    all_scenarios = THREAT_SCENARIOS[dept]
    unused = [sc for sc in all_scenarios if sc["id"] not in used_ids]

    if preferred_ids:
        preferred_unused = [sc for sc in unused if sc["id"] in preferred_ids]
        if preferred_unused:
            return random.choice(preferred_unused)

    fresh_category = [sc for sc in unused if _category_of(sc["id"]) not in used_categories]
    if fresh_category:
        return random.choice(fresh_category)

    if unused:
        return random.choice(unused)

    if preferred_ids:
        preferred_all = [sc for sc in all_scenarios if sc["id"] in preferred_ids]
        if preferred_all:
            return random.choice(preferred_all)

    return random.choice(all_scenarios)

def build_prompt(
    target_name: str,
    department: str,
    designation: str,
    scenario: dict,
    sender_team: str,
    has_clicked_before: bool,
    previous_subjects: list,
    previous_ctas: list,
    previous_body_snippet: str,
    attempt_count: int,
    is_repeat_category: bool = False,
    winning_category_hint: str = "",
    strategy_context: str = None
) -> str:
    
    designation = designation or "Employee"
    current_time_str = datetime.now().strftime("%B %Y") 

    memory_lines = []
    if previous_subjects:
        joined = " | ".join(f"'{s}'" for s in previous_subjects[:6] if s)
        if joined:
            memory_lines.append(f"The employee has ALREADY received emails with these subjects: {joined}. Do NOT reuse or paraphrase any of them. Use a clearly different subject and topic.")
    if previous_ctas:
        joined_cta = " | ".join(f"'{c}'" for c in previous_ctas[:6] if c)
        if joined_cta:
            memory_lines.append(f"Previously used hyperlink phrases: {joined_cta}. Use a DIFFERENT hyperlink phrase this time.")
    if previous_body_snippet:
        memory_lines.append(f"Avoid repeating this earlier theme/phrasing: '{previous_body_snippet[:80]}...'.")
    memory_block = " ".join(memory_lines)

    if has_clicked_before:
        evolution = "The employee interacted with an earlier email but did not complete the requested action. Take a fresh, unrelated angle from a different internal team. "
    else:
        evolution = "The employee ignored previous emails. Present this as a completely new, unrelated corporate communication from a different internal team so it does not feel like a follow-up. "

    category_context = ""
    if winning_category_hint:
        if is_repeat_category:
            category_context = f"IMPORTANT: '{winning_category_hint}'-style topics have historically driven higher engagement. Create a NEW, DIFFERENT scenario within that same theme (e.g. for Payroll: salary increment, bonus processing, tax declaration, revised payslip) - not a repeat of any earlier email. "
        else:
            category_context = f"CONTEXT: '{winning_category_hint}'-style topics have performed well historically; a similarly relevant, routine framing tends to work. "

    if attempt_count <= 1:
        tone = "TONE: Completely routine and legitimate. This should read like an ordinary day-to-day corporate email. Do NOT use words like URGENT, CRITICAL, IMMEDIATE, or FINAL. No pressure, just a normal request."
    elif attempt_count == 2:
        tone = "TONE: Still routine and professional, with a gentle reminder that a response is expected soon. Avoid alarmist words. At most mention a normal due date."
    elif attempt_count == 3:
        tone = "TONE: Professional with mild urgency. You may mention an approaching deadline once. Do not use more than one urgency word."
    elif attempt_count == 4:
        tone = "TONE: Firmer. A short reminder that this is pending and time-sensitive. You may use 'important' or 'time-sensitive', but keep it professional."
    else:
        tone = "TONE: Elevated urgency, still professional and corporate (never spammy). You may reference an approaching deadline and possible follow-up from the relevant team."

    strategy_guidance = ""
    if strategy_context:
        try:
            strat_data = json.loads(strategy_context)
            strategy_guidance = (
                f"\nAI CAMPAIGN ADVISOR STRATEGY TO APPLY:\n"
                f"You MUST align your generated email with the following strategic directives:\n"
                f"- Category: {strat_data.get('category', '')}\n"
                f"- Theme: {strat_data.get('theme', '')}\n"
                f"- Sender Persona: {strat_data.get('persona', '')}\n"
                f"- Psychological Angle: {strat_data.get('psychology', '')}\n"
                f"- Urgency Level: {strat_data.get('urgency', '')}\n"
            )
            if strat_data.get('subject') and strat_data.get('body'):
                strategy_guidance += (
                    f"\nDRAFT TEMPLATE PROVIDED BY ADVISOR:\n"
                    f"- Subject: {strat_data.get('subject')}\n"
                    f"- Body:\n{strat_data.get('body')}\n\n"
                    f"CRITICAL INSTRUCTION: Use the Draft Template above as your baseline copy. "
                    f"Adapt it ONLY to seamlessly inject the specific Recipient Name ({target_name}) and the Current System Date. "
                    f"Maintain the exact psychological tone and ensure the {{{{CTA}}}} token remains."
                )
        except Exception as e:
            strategy_guidance = f"\nAI CAMPAIGN ADVISOR STRATEGY TO APPLY:\n{strategy_context}\n"

    prompt = f"""
You are drafting an internal corporate email for Hawkins Cookers Limited that will be used in an authorised
phishing-awareness simulation. Write it so it reads EXACTLY like a genuine, routine email from the '{sender_team}' team.

RECIPIENT: {target_name}, {designation}, {department} department.

SCENARIO TOPIC: {scenario['title']}
SCENARIO CONTEXT: {scenario['body']}
SENDING TEAM PERSONA: {sender_team}
ATTACK VECTOR (for internal logic only, never mention it): {scenario['payload_type']}

{evolution}{category_context}{memory_block}
{strategy_guidance}

{tone}

STRICT WRITING RULES:
1. Do NOT generate any URLs, web addresses, or markdown links yourself.
2. Insert the EXACT token {{{{CTA}}}} exactly once, naturally inside a sentence, where a clickable link belongs.
   Example sentences: "You can review the details by {{{{CTA}}}}." or "Please {{{{CTA}}}} at your convenience."
   The {{{{CTA}}}} token will be replaced by the system with a real hyperlink - so write the surrounding sentence
   so the link reads naturally, like a normal Outlook/Gmail corporate email. Do NOT make it a big call-to-action line.
3. On a SEPARATE final line, output the hyperlink label text that should appear as the clickable words,
   prefixed exactly with 'LINKTEXT:'. Keep it 2-6 words, matching the scenario
   (e.g. 'review the payroll update', 'access the Hawkins Security Portal', 'complete your MFA enrolment',
   'open the Procurement Portal'). It MUST be different from any previously used phrase.
4. Do NOT use markdown formatting (**bold**, __italic__, #).
5. Do NOT include 'Subject:' or 'Body:' labels.
6. Write 3-5 short paragraphs separated by blank lines. Each paragraph 2-3 sentences.
7. Start with 'Dear {target_name},'.
8. End the body with ONE brief, natural closing line appropriate to the tone (NO signature, NO 'Regards',
   NO name - the system appends the official Hawkins signature automatically).
9. CRITICAL DATE RULE: The current date is {current_time_str}. NEVER use outdated years like 2024 or 2025.
10. Use dynamic, generic timeframes like 'Current Payroll Period', 'Current Month', or '{current_time_str}'.
11. Avoid giving exact past dates. Make the urgency feel immediate and relevant to the current system date.

OUTPUT FORMAT (exactly):
Subject ||| Body
LINKTEXT: <hyperlink label>

"""
    return prompt.strip()

def _extract_linktext(raw: str, default_label: str):
    link_label = default_label
    lines = raw.splitlines()
    kept = []
    for ln in lines:
        stripped = ln.strip()
        if stripped.upper().startswith("LINKTEXT:"):
            candidate = stripped.split(":", 1)[1].strip()
            candidate = candidate.strip('"\'*_`').strip()
            if candidate:
                link_label = candidate
        else:
            kept.append(ln)
    return "\n".join(kept).strip(), link_label
def generate_evolved_email(
    target_name: str,
    department: str,
    has_clicked_before: bool,
    previous_prompt_payload: dict,
    attempt_count: int,
    used_scenario_ids: list = None,
    winning_scenario_ids: list = None,
    winning_category_hint: str = "",
    previous_subjects: list = None,
    previous_ctas: list = None,
    designation: str = "",
    strategy_context: str = None
):
    # LAZY IMPORT (Yahan import karne se Circular Import deadlock toot jayega)
    from app import parse_ai_response, sanitize_ai_subject, sanitize_ai_body, sender_profiles, GEMINI_API_KEY
    used_ids = list(used_scenario_ids) if used_scenario_ids else []
    winning_ids = list(winning_scenario_ids) if winning_scenario_ids else []
    prev_subjects = list(previous_subjects) if previous_subjects else []
    prev_ctas = list(previous_ctas) if previous_ctas else []

    prev_body = None

    if previous_prompt_payload:

        sid = previous_prompt_payload.get("scenario_id")

        if sid and sid not in used_ids:
            used_ids.append(sid)

        ps = previous_prompt_payload.get("ai_subject", "")

        if ps and ps not in prev_subjects:
            prev_subjects.append(ps)

        pc = previous_prompt_payload.get("cta_text", "")

        if pc and pc not in prev_ctas:
            prev_ctas.append(pc)

        prev_body = previous_prompt_payload.get("ai_body", "")

    validation_hint = ""

    for generation_attempt in range(1, 6):

        used_categories = [_category_of(s) for s in used_ids]

        scenario = select_next_scenario(
            department or "Default",
            used_ids,
            used_categories=used_categories,
            preferred_ids=winning_ids
        )

        is_repeat_category = scenario["id"] in used_ids

        sender_identity = resolve_sender_identity(
            scenario,
            department or "Default"
        )

        default_label = f"review the {scenario['title'].lower()}"

        prompt = build_prompt(
            target_name=target_name,
            department=department,
            designation=designation,
            scenario=scenario,
            sender_team=sender_identity["name"],
            has_clicked_before=has_clicked_before,
            previous_subjects=prev_subjects,
            previous_ctas=prev_ctas,
            previous_body_snippet=prev_body or "",
            attempt_count=attempt_count,
            is_repeat_category=is_repeat_category,
            winning_category_hint=winning_category_hint,
            strategy_context=strategy_context
        )

        final_prompt = prompt

        if validation_hint:

            final_prompt += f"""

IMPORTANT

The previous email failed quality validation.

Please regenerate.

Validation Instructions

{validation_hint}

Generate a completely fresh email.
Do NOT repeat previous wording.
"""

            

        try:

            client = genai.Client(api_key=GEMINI_API_KEY)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=final_prompt
            )

            raw = response.text.strip()

            raw_wo_link, cta_text = _extract_linktext(
                raw,
                default_label
            )

            subject, body = parse_ai_response(raw_wo_link)

        except Exception as e:

            print(f"Evolution engine AI generation failed: {e}")

            subject = sanitize_ai_subject(
                scenario["title"]
            )

            cta_text = default_label

            body = sanitize_ai_body(
                f"""
Dear {target_name},

{scenario['body']}

You may {{{{CTA}}}} when convenient.

Thank you.
"""
            )

        if "{{CTA}}" not in body:

            body += (
                '<p style="margin-bottom:12px;line-height:1.6;">'
                'You may {{CTA}} at your convenience.'
                '</p>'
            )

        previous_payloads = []

        if previous_prompt_payload:
            previous_payloads.append(previous_prompt_payload)

        quality = validate_generated_campaign(

            subject=subject,

            body=body,

            cta=cta_text,

            sender_identity=sender_identity,

            scenario_id=scenario["id"],

            previous_subjects=prev_subjects,

            previous_ctas=prev_ctas,

            previous_payloads=previous_payloads,

            used_scenarios=used_ids

        )

        print_validation_report(
            target_name,
            generation_attempt,
            quality
        )

        if quality["passed"]:

            return (
                subject,
                body,
                final_prompt,
                scenario["id"],
                cta_text,
                sender_identity
            )

        validation_hint = quality["hint"]

        if scenario["id"] not in used_ids:
            used_ids.append(
                scenario["id"]
            )

        if subject not in prev_subjects:
            prev_subjects.append(subject)

        if cta_text not in prev_ctas:
            prev_ctas.append(cta_text)

        prev_body = body

        print("\nRegenerating Campaign...\n")


        print("\nMaximum retries reached.")
        print("Using last generated version.\n")
    return (
    subject,
    body,
    final_prompt,
    scenario["id"],
    cta_text,
    sender_identity
)
