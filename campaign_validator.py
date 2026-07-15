"""
campaign_validator.py

Enterprise Campaign Validator
----------------------------------
Checks:
1. Subject Similarity
2. Body Similarity
3. CTA Similarity
4. Sender Diversity
5. Scenario Reuse

Author:
Hawkins Cybersecurity Awareness Platform
"""

import re
from difflib import SequenceMatcher


SUBJECT_THRESHOLD = 0.72
BODY_THRESHOLD = 0.68
CTA_THRESHOLD = 0.80
JACCARD_THRESHOLD = 0.60




STOP_WORDS = {
    "the","a","an","to","for","of","in","on","at",
    "your","our","please","kindly","review",
    "required","update","new","important",
    "and","or","is","are","be","this","that",
    "you","we","with","from","by"
}


def clean_text(text):

    if not text:
        return ""

    text = text.lower()

    text = re.sub(r"<.*?>", " ", text)

    text = re.sub(r"[^a-z0-9 ]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def tokenize(text):

    text = clean_text(text)

    return {
        word
        for word in text.split()
        if word not in STOP_WORDS
    }


def jaccard_similarity(a, b):

    sa = tokenize(a)
    sb = tokenize(b)

    if not sa or not sb:
        return 0

    return len(sa & sb) / len(sa | sb)


def sequence_similarity(a, b):

    return SequenceMatcher(
        None,
        clean_text(a),
        clean_text(b)
    ).ratio()


def overall_similarity(a, b):

    seq = sequence_similarity(a, b)
    jac = jaccard_similarity(a, b)

    return (seq * 0.40) + (jac * 0.60)




def validate_subject(subject, previous_subjects):

    highest = 0

    for old in previous_subjects:

        score = overall_similarity(subject, old)

        highest = max(highest, score)

        if score >= SUBJECT_THRESHOLD:

            return (
                False,
                f"Subject too similar ({round(score*100)}%)"
            )

    return True, "PASS"


def validate_cta(cta, previous_ctas):

    if not cta:
        return True, "PASS"

    highest = 0

    for old in previous_ctas:

        score = overall_similarity(cta, old)

        highest = max(highest, score)

        if score >= CTA_THRESHOLD:

            return (
                False,
                f"CTA too similar ({round(score*100)}%)"
            )

    return True, "PASS"


def validate_body(body, previous_payloads):

    highest = 0

    for payload in previous_payloads:

        old_body = payload.get("ai_body", "")

        score = overall_similarity(body, old_body)

        highest = max(highest, score)

        if score >= BODY_THRESHOLD:

            return (
                False,
                f"Body too similar ({round(score*100)}%)"
            )

    return True, "PASS"


def validate_sender(sender_identity, previous_payloads):

    if sender_identity is None:
        return True, "PASS"

    sender = sender_identity.get("name","")

    recent = previous_payloads[:3]

    for payload in recent:

        if payload.get("sender_name") == sender:

            return (
                False,
                "Sender recently used"
            )

    return True, "PASS"


def validate_scenario(scenario_id, used_scenarios):

    if scenario_id in used_scenarios:

        return (
            False,
            "Scenario already used"
        )

    return True, "PASS"




def validate_campaign(
    subject,
    body,
    cta,
    sender_identity,
    scenario_id,
    previous_subjects,
    previous_ctas,
    previous_payloads,
    used_scenarios
):

    report = {}

    report["Subject"] = validate_subject(
        subject,
        previous_subjects
    )

    report["Body"] = validate_body(
        body,
        previous_payloads
    )

    report["CTA"] = validate_cta(
        cta,
        previous_ctas
    )

    report["Sender"] = validate_sender(
        sender_identity,
        previous_payloads
    )

    report["Scenario"] = validate_scenario(
        scenario_id,
        used_scenarios
    )

    reasons = []

    novelty = 100

    for key, value in report.items():

        if value[0] is False:

            reasons.append(value[1])

            novelty -= 20

    novelty = max(0, novelty)

    passed = len(reasons) == 0

    return passed, reasons, novelty, report