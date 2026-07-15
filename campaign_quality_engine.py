"""
campaign_quality_engine.py

Enterprise Campaign Quality Engine

Acts as an intelligent layer between
AI generation and email delivery.

Author: Hawkins Cybersecurity Awareness Platform
"""

from campaign_validator import validate_campaign


MAX_RETRIES = 5


def build_regeneration_hint(reasons):
    """
    Converts validation failures into
    instructions that the AI can understand.
    """

    hint = []

    for reason in reasons:

        reason = reason.lower()

        if "subject" in reason:
            hint.append(
                "- Generate a completely different subject."
            )

        elif "body" in reason:
            hint.append(
                "- Rewrite the email body using a different storyline."
            )

        elif "cta" in reason:
            hint.append(
                "- Use a different Call-To-Action."
            )

        elif "sender" in reason:
            hint.append(
                "- Use another internal sender/team."
            )

        elif "scenario" in reason:
            hint.append(
                "- Select another phishing scenario."
            )

    if not hint:
        hint.append("- Generate a fresh campaign.")

    return "\n".join(hint)


def validate_generated_campaign(
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

    passed, reasons, novelty, validation_report = validate_campaign(
        subject,
        body,
        cta,
        sender_identity,
        scenario_id,
        previous_subjects,
        previous_ctas,
        previous_payloads,
        used_scenarios
    )

    report = {
        "passed": passed,
        "reasons": reasons,
        "novelty": novelty,
        "validation_report": validation_report,
        "hint": build_regeneration_hint(reasons)
    }

    return report

def print_validation_report(
        employee_name,
        attempt,
        report
):

    print("\n" + "=" * 70)
    print(f"Employee : {employee_name}")
    print(f"Generation Attempt : {attempt}")

    if report["passed"]:
        print("STATUS : PASSED")
    else:
        print("STATUS : FAILED")

    for check, result in report["validation_report"].items():

        status = "PASS" if result[0] else "FAIL"

        print(f"{check:<10} : {status}")

    if not report["passed"]:

        print("\nReasons:")

        for r in report["reasons"]:
            print(f"  • {r}")

        print(f"\nNovelty Score : {report['novelty']}/100")

        print("\nAI Hint")
        print(report["hint"])

    print("=" * 70)