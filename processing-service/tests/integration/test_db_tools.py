"""
Integration tests: DB helpers, GL writer, checklist, workpaper, plan, review.
All run against a real PostgreSQL database.
Requires: docker compose -f docker-compose.dev.yml up -d  (from repo root)
"""
import pytest
import os

os.environ.setdefault("DATABASE_URL", "postgresql://dev:dev@localhost:5432/architect_ledger")
os.environ.setdefault("CLAUDE_API_KEY", "placeholder")
os.environ.setdefault("MISTRAL_API_KEY", "placeholder")


class TestDBHelpers:
    async def test_write_and_query(self, db_pool, seed_firm):
        from app.tools.db import write_db, query_db

        row = await write_db("audit_logs", {
            "firm_id": seed_firm,
            "action": "integration_test",
            "entity_type": "test",
        })
        assert row["id"] is not None
        assert row["action"] == "integration_test"

        rows = await query_db(
            "SELECT * FROM audit_logs WHERE id = $1", [row["id"]]
        )
        assert len(rows) == 1
        assert rows[0]["action"] == "integration_test"

    async def test_update_db(self, db_pool, seed_firm):
        from app.tools.db import write_db, update_db, query_db

        row = await write_db("audit_logs", {
            "firm_id": seed_firm,
            "action": "before_update",
        })

        updated = await update_db(
            "audit_logs",
            {"action": "after_update"},
            {"id": str(row["id"])},
        )
        assert updated["action"] == "after_update"


class TestGLWriter:
    async def test_write_gl_entry_with_source_chain(self, db_pool, seed_engagement):
        from app.tools.gl_writer import write_gl_entry

        result = await write_gl_entry(
            engagement_id=seed_engagement,
            account_code="4000",
            account_name="Revenue",
            amount=1500.00,
            entry_date="2025-01-15",
            description="Test revenue entry",
            source_transaction={
                "xero_id": "xero-test-001",
                "description": "CLIENT PAYMENT",
                "date": "2025-01-15",
                "amount": 1500.00,
            },
            categorization_method="integration_test",
            categorization_confidence=0.95,
            agent_type="transaction",
        )

        assert result["status"] == "written"
        assert result["gl_entry_id"] is not None
        assert "transaction" in result["source_chain"]
        assert result["source_chain"]["transaction"]["xero_id"] == "xero-test-001"

        # Verify it's actually in the DB with source_chain intact
        rows = await db_pool.fetch(
            "SELECT * FROM gl_entries WHERE id = $1", result["gl_entry_id"]
        )
        assert len(rows) == 1
        assert rows[0]["created_by"] == "AGENT"
        assert rows[0]["source_chain"]["transaction"]["xero_id"] == "xero-test-001"

    async def test_gl_entry_amount_precision(self, db_pool, seed_engagement):
        from app.tools.gl_writer import write_gl_entry

        result = await write_gl_entry(
            engagement_id=seed_engagement,
            account_code="5000",
            account_name="Expenses",
            amount=33.33,
            entry_date="2025-01-15",
            description="Precision test",
        )
        rows = await db_pool.fetch(
            "SELECT amount FROM gl_entries WHERE id = $1", result["gl_entry_id"]
        )
        assert float(rows[0]["amount"]) == pytest.approx(33.33)


class TestChecklistTools:
    @pytest.fixture
    async def checklist_item(self, db_pool, seed_engagement):
        row = await db_pool.fetchrow(
            """INSERT INTO checklist_items (engagement_id, item_type, label, required, status)
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            seed_engagement, "bank_statement", "Bank Statement — Jan 2025", True, "PENDING"
        )
        return str(row["id"])

    async def test_update_to_received(self, db_pool, checklist_item, seed_engagement):
        from app.tools.checklist import update_checklist_item, check_completeness

        result = await update_checklist_item(checklist_item, "RECEIVED")
        assert result["updated"] is True

        rows = await db_pool.fetch(
            "SELECT status, received_at FROM checklist_items WHERE id = $1", checklist_item
        )
        assert rows[0]["status"] == "RECEIVED"
        assert rows[0]["received_at"] is not None

    async def test_check_completeness_partial(self, db_pool, seed_engagement):
        from app.tools.checklist import check_completeness

        result = await check_completeness(seed_engagement)
        assert "total_required" in result
        assert "completion_percentage" in result
        assert isinstance(result["is_complete"], bool)


class TestWorkpaperTools:
    async def test_write_workpaper_entry(self, db_pool, seed_engagement):
        from app.tools.workpaper import write_workpaper_entry

        result = await write_workpaper_entry(
            engagement_id=seed_engagement,
            entry_type="document_processed",
            title="Bank Statement — Jan 2025",
            content="Processed TD bank statement. 87 transactions found. Closing balance: $12,450.00.",
            source_event={"document_id": "doc-test-001", "action": "uploaded"},
        )

        assert result["status"] == "written"
        assert result["workpaper_entry_id"] is not None

        rows = await db_pool.fetch(
            "SELECT * FROM workpaper_entries WHERE id = $1", result["workpaper_entry_id"]
        )
        assert rows[0]["created_by"] == "AGENT"
        assert rows[0]["source_event"]["document_id"] == "doc-test-001"


class TestPlanTools:
    @pytest.fixture
    async def plan(self, db_pool, seed_engagement):
        row = await db_pool.fetchrow(
            "INSERT INTO task_plans (engagement_id, status) VALUES ($1, $2) RETURNING id",
            seed_engagement, "ACTIVE"
        )
        return str(row["id"])

    async def test_create_and_update_plan_step(self, db_pool, plan):
        from app.tools.plan import create_plan_step, update_plan_step

        step = await create_plan_step(
            plan_id=plan,
            agent_type="document",
            description="Process bank statement",
            sort_order=1,
        )
        assert step["status"] == "PENDING"

        updated = await update_plan_step(
            step["plan_step_id"], "COMPLETE",
            result_summary="Processed 87 transactions"
        )
        assert updated["status"] == "COMPLETE"

        rows = await db_pool.fetch(
            "SELECT status, result_summary, completed_at FROM plan_steps WHERE id = $1",
            step["plan_step_id"]
        )
        assert rows[0]["status"] == "COMPLETE"
        assert rows[0]["result_summary"] == "Processed 87 transactions"
        assert rows[0]["completed_at"] is not None

    async def test_human_required_step(self, db_pool, plan):
        from app.tools.plan import create_plan_step

        step = await create_plan_step(
            plan_id=plan,
            agent_type="yearend",
            description="CCA adjustments — CPA approval required",
            sort_order=5,
            requires_human=True,
        )
        rows = await db_pool.fetch(
            "SELECT requires_human FROM plan_steps WHERE id = $1",
            step["plan_step_id"]
        )
        assert rows[0]["requires_human"] is True


class TestReviewTools:
    async def test_create_and_resolve_review_item(self, db_pool, seed_engagement):
        from app.tools.review import create_review_item, update_review_item

        item = await create_review_item(
            engagement_id=seed_engagement,
            item_type="classification_uncertain",
            description="Document could not be classified with confidence >= 0.80 (score: 0.71)",
            severity="medium",
            confidence_score=0.71,
            agent_reasoning={"top_candidates": ["bank_statement", "cra_correspondence"], "features": ["table", "CRA logo"]},
        )
        assert item["status"] == "PENDING"

        resolved = await update_review_item(
            item["review_item_id"],
            "APPROVED",
            resolution_note="Confirmed as bank_statement after manual review",
        )
        assert resolved["status"] == "APPROVED"

        rows = await db_pool.fetch(
            "SELECT status, resolution_note, agent_reasoning FROM review_items WHERE id = $1",
            item["review_item_id"]
        )
        assert rows[0]["status"] == "APPROVED"
        assert rows[0]["agent_reasoning"]["top_candidates"][0] == "bank_statement"
