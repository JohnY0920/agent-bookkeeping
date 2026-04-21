"""
Bookkeeping engagement flow configuration.
The planner agent reads this to know what checklist items to create
and what agents to run at each engagement mode.
"""

# Required checklist items for a standard bookkeeping engagement
DEFAULT_CHECKLIST_ITEMS = [
    {"item_type": "bank_statement",         "label": "Bank statements (all accounts)",   "required": True},
    {"item_type": "credit_card_statement",  "label": "Credit card statements",            "required": True},
    {"item_type": "cra_authorization",      "label": "CRA My Business Account authorization", "required": True},
    {"item_type": "prior_year_return",      "label": "Prior year tax return",             "required": False},
    {"item_type": "engagement_letter",      "label": "Signed engagement letter",          "required": True},
]

# Agents dispatched per engagement mode (in order, parallel where marked)
FLOW_STEPS = {
    "COLLECTION": [
        {"agent": "document",  "description": "Process uploaded document",        "parallel": True},
        {"agent": "comms",     "description": "Send checklist reminder if needed", "parallel": False},
    ],
    "PROCESSING": [
        {"agent": "transaction",    "description": "Audit transaction categorization",  "parallel": False},
        {"agent": "reconciliation", "description": "Bank reconciliation",               "parallel": False},
        {"agent": "tax_recon",      "description": "GST/HST reconciliation",           "parallel": True},
    ],
    "REVIEW": [
        {"agent": "yearend",    "description": "Year-end adjusting entries",  "parallel": False, "requires_human": True},
        {"agent": "qc",         "description": "Quality control checks",      "parallel": False},
        {"agent": "workpaper",  "description": "Assemble working papers",     "parallel": False},
    ],
}
