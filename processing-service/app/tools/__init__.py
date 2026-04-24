"""
Tool registry: maps Claude API tool names to Python async functions.
BaseAgent._get_tool_function() resolves names from here.
Add every new tool to TOOL_REGISTRY when implemented.
"""

# Phase 0 — always available
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

# Phase 1
from app.tools.storage import upload_file, download_file, get_signed_url, delete_file
from app.tools.checklist import update_checklist_item, check_completeness
from app.tools.workpaper import write_workpaper_entry
from app.tools.plan import create_plan_step, update_plan_step
from app.tools.review import create_review_item, update_review_item
from app.tools.ocr import extract_document
from app.tools.lesson import get_lessons, save_lesson
from app.tools.dispatch import dispatch_agent

# Phase 2
from app.tools.xero import pull_transactions, pull_chart_of_accounts, pull_bank_balances
from app.tools.knowledge import search_knowledge_base

# Phase 3 (uncomment as implemented)
# from app.tools.email import send_email

TOOL_REGISTRY: dict = {
    # Calculations (deterministic — never use LLM for these)
    "calculate_cca": calculate_cca,
    "calculate_amortization": calculate_amortization,
    "calculate_gst": calculate_gst,
    "calculate_itc": calculate_itc,
    "calculate_tax_payable": calculate_tax_payable,
    "calculate_sbd": calculate_sbd,
    # GL writer — always use this, never insert gl_entries directly
    "write_gl_entry": write_gl_entry,
    # DB helpers
    "query_db": query_db,
    "write_db": write_db,
    # Storage (S3)
    "upload_file": upload_file,
    "download_file": download_file,
    "get_signed_url": get_signed_url,
    "delete_file": delete_file,
    # Checklist
    "update_checklist_item": update_checklist_item,
    "check_completeness": check_completeness,
    # Working papers
    "write_workpaper_entry": write_workpaper_entry,
    # Task plan
    "create_plan_step": create_plan_step,
    "update_plan_step": update_plan_step,
    # Review queue
    "create_review_item": create_review_item,
    "update_review_item": update_review_item,
    # Document extraction via Claude Sonnet vision (replaces Mistral OCR)
    "extract_document": extract_document,
    # Lessons
    "get_lessons": get_lessons,
    "save_lesson": save_lesson,
    # Agent dispatch (planner only)
    "dispatch_agent": dispatch_agent,
    # Xero integration
    "pull_transactions": pull_transactions,
    "pull_chart_of_accounts": pull_chart_of_accounts,
    "pull_bank_balances": pull_bank_balances,
    # CRA knowledge base
    "search_knowledge_base": search_knowledge_base,
}
