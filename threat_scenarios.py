# threat_scenarios.py

# Enterprise Threat Intelligence Repository (Phase 1, Phase 2 & Enterprise Expansion)
# Total Scenarios: 57 (Covers Deepfakes, BEC, Supply Chain, Core Phishing & Departmental Traps)

THREAT_SCENARIOS = {
    "HR": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "hr_payroll_policy",
            "title": "Revised Payroll & Leave Policy",
            "body": "Our annual compliance review has updated the Payroll Structure and Leave Deduction Policy effective January 1, 2026. All employees must review the changes to avoid delays in salary processing. Key updates include new HRA calculations, leave encashment rules, and tax code changes.",
            "payload_type": "LINK"
        },
        {
            "id": "hr_attendance_correction",
            "title": "Monthly Attendance Correction Required",
            "body": "Timekeeping records show discrepancies in your attendance logs for December 2025. To ensure accurate payroll, please verify and correct your clock-in and clock-out entries before EOD.",
            "payload_type": "LINK"
        },
        {
            "id": "hr_benefits_enrollment",
            "title": "Open Enrollment for Employee Benefits",
            "body": "The Open Enrollment window for health and wellness benefits closes on December 31, 2025. Review your current selections and confirm any changes to avoid default coverage settings.",
            "payload_type": "LINK"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "hr_ai_hr_notification",
            "title": "AI-Generated HR Policy Notification",
            "body": "The HR Operations platform has generated a personalized policy notification requiring your acknowledgement. Review the updated policy information and confirm receipt to remain compliant.",
            "payload_type": "LINK"
        },
        {
            "id": "hr_salary_revision",
            "title": "Annual Salary Revision Notice",
            "body": "The Compensation Committee has finalized the annual salary revision cycle. Review your revised compensation letter and acknowledge acceptance before payroll processing begins.",
            "payload_type": "LINK"
        },
        {
            "id": "hr_leave_approval",
            "title": "Pending Leave Approval Notification",
            "body": "A pending leave request requires your confirmation before it can be processed. Review the leave details and approve or update your request before the deadline.",
            "payload_type": "LINK"
        },
        {
            "id": "hr_recruitment_interview",
            "title": "Interview Schedule Confirmation",
            "body": "Your interview schedule has been updated by the Talent Acquisition Team. Review the interview details and confirm your availability to avoid cancellation.",
            "payload_type": "LINK"
        }
    ],

    "Finance": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "fin_invoice_payment",
            "title": "Overdue Vendor Invoice Alert",
            "body": "Our accounts payable system flagged invoice INV-2026-1123 for Precision Engineering Pvt. Ltd. Amount: ₹320,000. Payment is due by December 28, 2025 to avoid service suspension.",
            "payload_type": "LINK"
        },
        {
            "id": "fin_expense_reimbursement",
            "title": "Expense Reimbursement Pending Approval",
            "body": "Your Q4 expense report has been routed back for missing receipts. Please upload scanned copies of all invoices and receipts by EOD to process your reimbursement.",
            "payload_type": "LINK"
        },
        {
            "id": "fin_tax_clearance",
            "title": "Year-End Tax Clearance Certificate Needed",
            "body": "To finalize your tax documents for FY2025-26, upload your Form 16 and TDS certificates before December 29, 2025. Failure to do so may delay salary processing.",
            "payload_type": "LINK"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "fin_ai_procurement_request",
            "title": "AI-Generated Procurement Request",
            "body": "An automatically generated procurement request has been submitted for urgent vendor processing. Review the purchase requirements and complete the approval workflow before procurement deadlines.",
            "payload_type": "LINK"
        },
        {
            "id": "fin_purchase_order_approval",
            "title": "Purchase Order Approval Required",
            "body": "A new purchase order has been submitted for approval before vendor processing can begin. Review the procurement details and approve the request before the daily cutoff.",
            "payload_type": "LINK"
        },
        {
            "id": "fin_bank_detail_change",
            "title": "Vendor Banking Details Updated",
            "body": "One of our registered vendors has submitted updated banking information for future payments. Please verify the revised account details before the next payment cycle.",
            "payload_type": "LINK"
        },
        {
            "id": "fin_payment_release",
            "title": "Urgent Payment Release Request",
            "body": "A high-priority payment request is awaiting your approval before today's banking cutoff. Review the payment details and authorize the transaction immediately.",
            "payload_type": "LINK"
        }
    ],

    "IT": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "it_m365_password",
            "title": "Microsoft 365 Password Expiration Notice",
            "body": "Your Microsoft 365 account password will expire within 2 hours. Reset your password now to maintain uninterrupted access to Outlook, Teams, and OneDrive.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "it_vpn_certificate",
            "title": "VPN Security Certificate Renewal",
            "body": "Your VPN security certificate on device has expired. To avoid connectivity loss, download and install the new certificate package through the secure portal.",
            "payload_type": "LINK"
        },
        {
            "id": "it_software_license",
            "title": "Software License Renewal Required",
            "body": "The license for your SAP Business One client will expire on December 31, 2025. Renew now to prevent service interruption.",
            "payload_type": "LINK"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "it_password_reset",
            "title": "Password Reset Verification",
            "body": "A password reset request has been initiated for your corporate account. Verify your identity to complete the reset process and retain access to company services.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "it_device_registration",
            "title": "Corporate Device Registration Required",
            "body": "Your workstation has not yet been registered under the latest endpoint compliance policy. Complete device registration to maintain secure access to internal systems.",
            "payload_type": "LINK"
        },
        {
            "id": "it_helpdesk_ticket",
            "title": "IT Helpdesk Ticket Assigned",
            "body": "A new support ticket has been assigned to your account regarding workstation configuration. Review the ticket details and acknowledge the request.",
            "payload_type": "LINK"
        },
        {
            "id": "it_security_alert",
            "title": "Suspicious Login Activity Detected",
            "body": "Our Security Operations Center detected an unusual sign-in attempt associated with your account. Review the activity and verify whether it was initiated by you.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "it_remote_access_approval",
            "title": "Remote Access Approval Required",
            "body": "A request has been submitted to enable remote access for your corporate account. Review and approve the request to continue using remote connectivity services.",
            "payload_type": "CREDENTIAL"
        }
    ],

    "Cyber Security": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "cs_zero_day_alert",
            "title": "Zero-Day Vulnerability Detected",
            "body": "Splunk SIEM has alerted a possible zero-day exploit attempt on firewall FW-PRD-01. Log in to the Emergency Admin Portal to review packet captures and initiate containment.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "cs_incident_report",
            "title": "Security Incident Report Required",
            "body": "Anomalous outbound DNS queries have been flagged from your workstation. Submit a detailed incident report via the SOC portal immediately.",
            "payload_type": "LINK"
        },
        {
            "id": "cs_mfa_enrollment",
            "title": "Multi-Factor Authentication Enrollment",
            "body": "To comply with our ISO27001 standard, enable MFA on your corporate account today. Follow the enrollment steps in the Threat Intelligence portal.",
            "payload_type": "LINK"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "cs_azure_ad_authentication",
            "title": "Azure Active Directory Sign-In Verification",
            "body": "Your Azure Active Directory account requires identity verification following a recent security policy update. Complete the verification process to maintain uninterrupted access to Microsoft 365 services.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "cs_oauth_consent",
            "title": "Microsoft 365 Application Permission Request",
            "body": "A newly deployed productivity application requires permission to access your Microsoft 365 account. Review and approve the requested permissions to activate the application.",
            "payload_type": "LINK"
        },
        {
            "id": "cs_device_code_auth",
            "title": "Device Authentication Request",
            "body": "A secure corporate device is waiting to be linked with your Microsoft account. Enter the verification code shown on the device to complete authentication.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "cs_mfa_approval",
            "title": "Unexpected Multi-Factor Authentication Request",
            "body": "A sign-in attempt to your corporate account requires immediate MFA approval. Approve the authentication request to prevent account access interruption.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "cs_mfa_reset",
            "title": "MFA Recovery Process Initiated",
            "body": "A request has been received to reset your Multi-Factor Authentication settings. Verify your identity to complete the recovery process.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "cs_qr_security_notice",
            "title": "Secure QR Verification",
            "body": "To complete the rollout of our new security platform, scan the secure QR code provided in this notification. Verification must be completed before continued access is granted.",
            "payload_type": "LINK"
        }
    ],

    "Management": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "mgmt_board_materials",
            "title": "Board Meeting Materials Review",
            "body": "The Audit Committee has requested your review of the Q4 Employee Master Sheet. Access the secure Board Document Portal and confirm your acknowledgment.",
            "payload_type": "LINK"
        },
        {
            "id": "mgmt_confidential_request",
            "title": "Confidential: Executive Expense Summary",
            "body": "Please upload the executive travel and expense summary for December 2025 to the secure portal for final approval by the CFO.",
            "payload_type": "LINK"
        },
        {
            "id": "mgmt_strategy_feedback",
            "title": "Strategic Plan Feedback Request",
            "body": "Your input is needed on the 2026 strategic roadmap draft. Review the document and share your comments before the end-of-day session.",
            "payload_type": "LINK"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "mgmt_deepfake_voice_request",
            "title": "Urgent Voice Request from Executive",
            "body": "You have received a voice message that appears to be from a senior executive requesting immediate action on a confidential financial matter. Review the request and follow the provided instructions before the end of the day.",
            "payload_type": "LINK"
        },
        {
            "id": "mgmt_deepfake_video_meeting",
            "title": "Executive Video Conference Invitation",
            "body": "You have been invited to an urgent executive video conference regarding a confidential business matter. Join the meeting using the secure corporate conference portal.",
            "payload_type": "LINK"
        },
        {
            "id": "mgmt_compliance_audit",
            "title": "Internal Compliance Audit Notification",
            "body": "The Internal Audit team has initiated a compliance review for your department. Please review the requested documentation and submit the required records before the audit deadline.",
            "payload_type": "LINK"
        },
        {
            "id": "mgmt_confidential_memo",
            "title": "Executive Confidential Memorandum",
            "body": "A confidential memorandum from senior leadership has been shared for immediate review. Access the executive document portal and acknowledge receipt.",
            "payload_type": "LINK"
        },
        {
            "id": "mgmt_legal_notice",
            "title": "Confidential Legal Document Review",
            "body": "The Legal Department has uploaded confidential documents requiring executive review. Please access the secure portal and confirm your acknowledgement.",
            "payload_type": "LINK"
        }
    ],

   # =========================================================
    # NEW ENTERPRISE DEPARTMENTS (WITH CORE & ADVANCED SPLIT)
    # =========================================================
    
    "Sales": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "sales_crm_update",
            "title": "Salesforce CRM Urgent Re-authentication",
            "body": "Due to a recent security patch, your Salesforce CRM session has been terminated. Please re-authenticate immediately to ensure your current pipeline and Q4 leads are not lost.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "sales_commission_dispute",
            "title": "Discrepancy in Q3 Commission Payout",
            "body": "The Finance team has flagged a discrepancy in your recent sales commission calculation. Please review the attached adjustment sheet and confirm your final numbers before the payout freeze.",
            "payload_type": "LINK"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "sales_bec_contract",
            "title": "Action Required: Enterprise Client Contract via DocuSign",
            "body": "A major enterprise client has submitted the final MSA (Master Service Agreement) with custom pricing modifications. Review and sign the contract securely via the DocuSign portal before the quarter ends.",
            "payload_type": "LINK"
        },
        {
            "id": "sales_executive_discount",
            "title": "Confidential: VP Approved Extreme Discount",
            "body": "I have just stepped into a board meeting but I am approving the 40% discount for the pending enterprise deal to close it today. Log in to the approval portal immediately to push this through before EOD.",
            "payload_type": "CREDENTIAL"
        }
    ],

    "Marketing": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "mktg_social_media_alert",
            "title": "Suspicious Login on Corporate Social Media",
            "body": "Meta Business Manager has detected an unauthorized login attempt on our corporate ad account. Please verify your access immediately to prevent active campaigns from being paused.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "mktg_budget_approval",
            "title": "URGENT: Q4 Campaign Budget Rejection",
            "body": "Your proposed marketing budget for the upcoming Q4 campaign has been temporarily rejected by the Management Board. Please review the highlighted cuts in the attached document and submit a revised version by EOD.",
            "payload_type": "LINK"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "mktg_influencer_invoice",
            "title": "Overdue Agency Invoice - Campaign Halt",
            "body": "Our PR agency partner has flagged an overdue payment of ₹4,50,000 for the recent influencer campaign. They have threatened to pull down all live assets. Review the attached invoice immediately.",
            "payload_type": "LINK"
        },
        {
            "id": "mktg_brand_crisis",
            "title": "CRITICAL: Brand Reputation Alert",
            "body": "Our AI monitoring tool has detected a rapidly trending negative PR incident mentioning Hawkins on X (formerly Twitter). Log in to the Media Monitoring dashboard immediately to assess the damage and prepare a statement.",
            "payload_type": "CREDENTIAL"
        }
    ],

    "Supply Chain": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "supply_vendor_delay",
            "title": "URGENT: Raw Material Shipment Held at Customs",
            "body": "A critical shipment of aluminum for the manufacturing plant has been held at customs due to documentation mismatch. Please review the attached manifest clearance form immediately to avoid production delays.",
            "payload_type": "LINK"
        },
        {
            "id": "supply_logistics_portal",
            "title": "Logistics Portal Password Expiry",
            "body": "Your access to the Global Logistics & Freight tracking portal expires today. Please re-authenticate your credentials to continue tracking inbound manufacturing shipments.",
            "payload_type": "CREDENTIAL"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "supply_bec_bank_change",
            "title": "Supplier Bank Account Modification",
            "body": "Our primary steel supplier has submitted an urgent request to change their remittance bank details for the upcoming bulk payment. Please verify the new banking coordinates through the secure vendor portal.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "supply_ai_disruption",
            "title": "Supply Chain Disruption Warning",
            "body": "An AI-generated forecast indicates a severe weather disruption affecting our primary shipping route. Review the automated contingency plan and approve the alternate freight budget.",
            "payload_type": "LINK"
        }
    ],

    "Legal": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "legal_nda_signature",
            "title": "Action Required: Updated Corporate NDA",
            "body": "As part of our Q1 compliance audit, all employees must sign the updated Non-Disclosure Agreement (NDA). Please access the legal document portal to review and electronically sign the agreement.",
            "payload_type": "LINK"
        },
        {
            "id": "legal_policy_violation",
            "title": "Notice of Internal Policy Violation",
            "body": "The compliance team has flagged a potential violation of the corporate IT usage policy originating from your department. Please review the incident report attached.",
            "payload_type": "LINK"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "legal_court_summons",
            "title": "URGENT: Electronic Subpoena Received",
            "body": "The corporate legal desk has received an electronic subpoena requiring immediate discovery of internal communications. Access the secure e-discovery portal using your executive credentials to review the summons.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "legal_exec_contract_bypass",
            "title": "Confidential: Expedited Contract Review",
            "body": "I am in a negotiation with a new joint venture partner and need you to review this draft agreement immediately. Bypass the standard intake queue and upload your notes directly to my secure drive.",
            "payload_type": "LINK"
        }
    ],

    "Customer Support": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "support_escalated_complaint",
            "title": "ESCALATION: Legal Notice from Consumer Forum",
            "body": "A severe customer complaint regarding a defective product has been escalated to a legal notice. Please log in to the Customer Success portal to review the attached evidence video and legal draft.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "support_sla_breach",
            "title": "Warning: SLA Breach on VIP Client Tickets",
            "body": "Your recent ticket resolution times have fallen below the mandatory 24-hour SLA for Tier-1 clients. Review the flagged tickets in the QA dashboard immediately.",
            "payload_type": "LINK"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "support_gdpr_violation",
            "title": "CRITICAL: Data Privacy Violation Notice",
            "body": "A customer has filed a formal GDPR/DPDP data deletion request that was mishandled by our team. You must log in to the compliance portal and execute the data purge manually.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "support_weaponized_pdf",
            "title": "Re: Defective Cooker - Photographic Evidence",
            "body": "I am highly disappointed with my recent purchase. It exploded on the first use. I have attached the high-resolution images and my medical bills. If this is not resolved today, I am going to the press.",
            "payload_type": "LINK"
        }
    ],

    "R&D": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "rnd_patent_issue",
            "title": "Confidential: Intellectual Property Alert",
            "body": "Our legal monitoring tools have flagged a potential patent infringement regarding your recent design submission. Please review the highlighted blueprints in the secure R&D vault before our meeting.",
            "payload_type": "LINK"
        },
        {
            "id": "rnd_design_review",
            "title": "Action Required: Prototype V3 Design Approval",
            "body": "The manufacturing team has requested final approval on the V3 Cooktop prototype specifications before tooling begins. Review the CAD files in the shared repository.",
            "payload_type": "CREDENTIAL"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "rnd_ip_theft",
            "title": "SECURITY ALERT: Unauthorized Access to Vault",
            "body": "The system detected an unauthorized download of the 2026 Product Roadmap blueprints. Please verify your identity and confirm if you initiated this massive data transfer.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "rnd_fake_collaboration",
            "title": "Research Collaboration: Material Science Institute",
            "body": "Our research institute is interested in partnering with Hawkins on a new thermal efficiency study. I have attached our preliminary proposal and non-disclosure terms for your technical review.",
            "payload_type": "LINK"
        }
    ],

    "Administration": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "admin_office_policy",
            "title": "Mandatory Office Access Card Renewal",
            "body": "The physical security system is being upgraded this weekend. All employees must register their details in the new portal to ensure their ID cards work for building access starting Monday.",
            "payload_type": "LINK"
        },
        {
            "id": "admin_parking_allocation",
            "title": "Update: New Parking Allocation System",
            "body": "Due to recent construction, employee parking spots have been reallocated. Please review your new designated parking bay in the attached facility management memo.",
            "payload_type": "LINK"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "admin_bec_vendor_invoice",
            "title": "Overdue Payment: Office Facilities Maintenance",
            "body": "Our facility maintenance contractor has submitted their quarterly invoice which is currently 15 days past due. Please approve this expense via the admin portal to avoid service disruption.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "admin_safety_compliance",
            "title": "ACTION REQUIRED: Fire Safety Certification",
            "body": "According to municipal regulations, your mandatory annual fire safety module is incomplete. Log in to the compliance portal and complete the certification by EOD to avoid a penalty.",
            "payload_type": "LINK"
        }
    ],
    
    "Default": [
        # --- PHASE 1: Core Scenarios ---
        {
            "id": "def_general_update",
            "title": "Important System Update Notification",
            "body": "A critical system update will occur tonight at 11:00 PM. Please save all work and log off before the maintenance window.",
            "payload_type": "LINK"
        },
        {
            "id": "def_profile_review",
            "title": "Update Your Corporate Profile",
            "body": "Your employee profile is missing key information. Please log in to the HR portal and complete your personal and emergency contact details.",
            "payload_type": "LINK"
        },
        # --- PHASE 2: Advanced AI/BEC Scenarios ---
        {
            "id": "def_teams_invitation",
            "title": "Microsoft Teams Meeting Invitation",
            "body": "You have been invited to join a Microsoft Teams meeting regarding an important business update. Review the invitation details and confirm your attendance.",
            "payload_type": "LINK"
        },
        {
            "id": "def_sharepoint_document",
            "title": "Shared SharePoint Document",
            "body": "A colleague has shared an important business document with you through Microsoft SharePoint. Review the document before the scheduled meeting.",
            "payload_type": "LINK"
        },
        {
            "id": "def_onedrive_share",
            "title": "OneDrive File Shared With You",
            "body": "A confidential project document has been shared through OneDrive. Open the shared file to review the latest version.",
            "payload_type": "LINK"
        },
        {
            "id": "def_google_drive_share",
            "title": "Google Drive Document Shared",
            "body": "A project collaborator has shared a document with you via Google Drive. Review the shared file and provide your feedback.",
            "payload_type": "LINK"
        },
        {
            "id": "def_zoom_invitation",
            "title": "Zoom Meeting Invitation",
            "body": "You have received a Zoom meeting invitation for an upcoming project discussion. Join the meeting using the secure invitation link.",
            "payload_type": "LINK"
        },
        {
            "id": "def_docusign_request",
            "title": "Document Signature Required",
            "body": "A document requiring your electronic signature has been sent through DocuSign. Review and sign the document to complete the approval process.",
            "payload_type": "LINK"
        },
        {
            "id": "def_adobe_sign_request",
            "title": "Adobe Sign Approval Request",
            "body": "An agreement requiring your approval has been shared through Adobe Sign. Review the document and complete the signing process.",
            "payload_type": "LINK"
        },
        {
            "id": "def_cloud_storage_access",
            "title": "Cloud Storage Access Request",
            "body": "Additional access has been granted to a shared cloud storage folder containing project documents. Verify your access permissions before collaborating.",
            "payload_type": "LINK"
        },
        {
            "id": "def_collaboration_invite",
            "title": "Business Collaboration Workspace Invitation",
            "body": "You have been invited to join a shared collaboration workspace for an upcoming business initiative. Accept the invitation to access project resources.",
            "payload_type": "LINK"
        },
        {
            "id": "def_vendor_portal_login",
            "title": "Third-Party Vendor Portal Access",
            "body": "A trusted business partner has invited you to access their supplier portal to review procurement documents. Sign in using your corporate credentials to continue.",
            "payload_type": "CREDENTIAL"
        },
        {
            "id": "def_ai_executive_email",
            "title": "Executive Priority Request",
            "body": "An urgent message from senior management requests your immediate assistance on a confidential business matter. Review the instructions and respond before the end of the day.",
            "payload_type": "LINK"
        }
    ]
}