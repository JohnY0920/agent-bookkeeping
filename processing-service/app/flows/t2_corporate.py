"""
T2 corporate tax return flow.
Full pipeline: document collection → transaction processing → year-end → tax → filing.
"""

T2_CHECKLIST_ITEMS = [
    {"item_type": "bank_statement",          "label": "Bank statements (all accounts)",          "required": True},
    {"item_type": "credit_card_statement",   "label": "Credit card statements",                  "required": True},
    {"item_type": "cra_authorization",       "label": "CRA My Business Account authorization",  "required": True},
    {"item_type": "prior_year_return",       "label": "Prior year T2 return",                   "required": False},
    {"item_type": "engagement_letter",       "label": "Signed engagement letter",                "required": True},
    {"item_type": "articles_of_incorporation","label": "Articles of incorporation",              "required": False},
    {"item_type": "minute_book",             "label": "Corporate minute book (for dividends)",   "required": False},
]

T2_FLOW_STEPS = [
    # COLLECTION phase
    {"agent": "document",       "description": "Process all uploaded corporate documents",                   "mode": "COLLECTION", "parallel": True},
    {"agent": "comms",          "description": "Request missing documents from client",                      "mode": "COLLECTION", "parallel": False},
    # PROCESSING phase
    {"agent": "transaction",    "description": "Categorize all Xero transactions",                          "mode": "PROCESSING", "parallel": False},
    {"agent": "reconciliation", "description": "Bank reconciliation for all accounts",                      "mode": "PROCESSING", "parallel": False},
    {"agent": "tax_recon",      "description": "GST/HST reconciliation and ITC audit",                     "mode": "PROCESSING", "parallel": True},
    # REVIEW phase
    {"agent": "yearend",        "description": "CCA schedule and year-end adjustments",                     "mode": "REVIEW",     "parallel": False, "requires_human": True},
    {"agent": "financial_stmt", "description": "Income statement and balance sheet",                        "mode": "REVIEW",     "parallel": False},
    {"agent": "tax",            "description": "T2 return computation with SBD",                            "mode": "REVIEW",     "parallel": False, "requires_human": True},
    {"agent": "qc",             "description": "Pre-filing quality control",                                "mode": "REVIEW",     "parallel": False},
    {"agent": "workpaper",      "description": "Assemble complete working paper package",                   "mode": "REVIEW",     "parallel": False},
    {"agent": "filing",         "description": "E-filing package, invoice, and engagement archival",        "mode": "REVIEW",     "parallel": False, "requires_human": True},
]
