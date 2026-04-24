"""
T1 personal tax return flow.
Extends the bookkeeping flow with tax-specific steps.
"""

T1_CHECKLIST_ITEMS = [
    {"item_type": "t4_slip",          "label": "T4 slip(s) — employment income",         "required": True},
    {"item_type": "t5_slip",          "label": "T5 slip(s) — investment income",          "required": False},
    {"item_type": "t3_slip",          "label": "T3 slip(s) — trust income",               "required": False},
    {"item_type": "rrsp_receipt",     "label": "RRSP contribution receipts",              "required": False},
    {"item_type": "medical_receipt",  "label": "Medical expense receipts",                "required": False},
    {"item_type": "donation_receipt", "label": "Charitable donation receipts",            "required": False},
    {"item_type": "childcare_receipt","label": "Child care expense receipts",             "required": False},
    {"item_type": "prior_year_return","label": "Prior year T1 return",                   "required": False},
    {"item_type": "cra_authorization","label": "CRA authorization (T1013)",              "required": True},
]

T1_FLOW_STEPS = [
    # COLLECTION phase
    {"agent": "document",       "description": "Process all uploaded T-slips and receipts",   "mode": "COLLECTION", "parallel": True},
    {"agent": "comms",          "description": "Request any missing required slips",           "mode": "COLLECTION", "parallel": False},
    # PROCESSING phase
    {"agent": "tax_recon",      "description": "Verify RRSP limits and deduction eligibility", "mode": "PROCESSING", "parallel": False},
    # REVIEW phase
    {"agent": "financial_stmt", "description": "Compile income summary from T-slips",          "mode": "REVIEW",     "parallel": False},
    {"agent": "tax",            "description": "Prepare T1 return computation",                "mode": "REVIEW",     "parallel": False, "requires_human": True},
    {"agent": "qc",             "description": "Pre-filing QC check",                          "mode": "REVIEW",     "parallel": False},
    {"agent": "workpaper",      "description": "Assemble T1 working paper",                    "mode": "REVIEW",     "parallel": False},
    # Filing (triggered after CPA approves tax return plan_step)
    {"agent": "filing",         "description": "E-filing package generation and archival",     "mode": "REVIEW",     "parallel": False, "requires_human": True},
]
