"""
Tool registry: maps Claude API tool names to Python async functions.
BaseAgent._get_tool_function() resolves names from here.
Add every new tool to TOOL_REGISTRY when implemented.
"""

from app.tools.calculations import (
    calculate_cca,
    calculate_amortization,
    calculate_gst,
    calculate_itc,
    calculate_tax_payable,
    calculate_sbd,
)
from app.tools.gl_writer import write_gl_entry
from app.tools.db import query_db, write_db

# Phase 1 tools (uncomment as implemented)
# from app.tools.storage import upload_file, download_file, get_signed_url
# from app.tools.checklist import update_checklist_item, check_completeness
# from app.tools.workpaper import write_workpaper_entry
# from app.tools.plan import create_plan_step, update_plan_step
# from app.tools.review import create_review_item, update_review_item
# from app.tools.ocr import mistral_ocr
# from app.tools.lesson import get_lessons, save_lesson

# Phase 2 tools
# from app.tools.xero import pull_transactions, pull_chart_of_accounts, pull_bank_balances
# from app.tools.knowledge import search_knowledge_base

# Phase 3 tools
# from app.tools.email import send_email

TOOL_REGISTRY: dict = {
    # Calculations (deterministic — never use LLM for these)
    "calculate_cca": calculate_cca,
    "calculate_amortization": calculate_amortization,
    "calculate_gst": calculate_gst,
    "calculate_itc": calculate_itc,
    "calculate_tax_payable": calculate_tax_payable,
    "calculate_sbd": calculate_sbd,
    # GL writer (always use this — never insert gl_entries directly)
    "write_gl_entry": write_gl_entry,
    # DB helpers
    "query_db": query_db,
    "write_db": write_db,
}
