"""
Phase 2 integration tests: transactions, knowledge base, Xero connection.
All run against a real PostgreSQL database.
Requires: docker compose -f docker-compose.dev.yml up -d
"""
import pytest
import os

os.environ.setdefault("DATABASE_URL", "postgresql://dev:dev@localhost:5432/architect_ledger")
os.environ.setdefault("CLAUDE_API_KEY", "placeholder")
os.environ.setdefault("MISTRAL_API_KEY", "placeholder")


class TestTransactionDB:
    async def test_write_and_query_transaction(self, db_pool, seed_engagement, seed_firm):
        from app.tools.db import write_db, query_db

        row = await write_db("transactions", {
            "engagement_id": seed_engagement,
            "firm_id": seed_firm,
            "date": "2025-01-15",
            "amount": -250.00,
            "description": "Office Depot — office supplies",
            "contact_name": "Office Depot",
            "xero_id": "xero-integ-001",
            "categorization_status": "PENDING",
            "source_chain": {"xero_id": "xero-integ-001", "type": "SPEND"},
        })
        assert row["id"] is not None
        assert float(row["amount"]) == pytest.approx(-250.00)

        rows = await query_db(
            "SELECT * FROM transactions WHERE xero_id = $1", ["xero-integ-001"]
        )
        assert len(rows) == 1
        assert rows[0]["source_chain"]["xero_id"] == "xero-integ-001"

    async def test_update_categorization_status(self, db_pool, seed_engagement, seed_firm):
        from app.tools.db import write_db, update_db, query_db

        row = await write_db("transactions", {
            "engagement_id": seed_engagement,
            "firm_id": seed_firm,
            "date": "2025-01-20",
            "amount": -150.00,
            "description": "Rogers Communications",
            "categorization_status": "PENDING",
            "source_chain": {"xero_id": "xero-integ-002"},
        })

        updated = await update_db(
            "transactions",
            {"categorization_status": "AUTO_APPROVED", "confidence_score": 0.92, "account_code": "5500"},
            {"id": str(row["id"])},
        )
        assert updated["categorization_status"] == "AUTO_APPROVED"
        assert float(updated["confidence_score"]) == pytest.approx(0.92)


class TestKnowledgeBaseDB:
    async def test_add_and_search_entry(self, db_pool):
        """Test that knowledge entries can be written and retrieved by similarity."""
        from unittest.mock import patch, AsyncMock

        # Use a deterministic mock embedding (real pgvector search)
        mock_embedding = [0.1] * 512 + [0.9] * 512

        with patch("app.models.llm.get_embedding", AsyncMock(return_value=mock_embedding)):
            from app.tools.knowledge import add_knowledge_entry, search_knowledge_base

            result = await add_knowledge_entry(
                source="ITA",
                title="Test entry — meals restriction",
                content="Only 50% of meals expenses are deductible.",
                section="s.67.1",
            )
            assert result["status"] == "added"

            results = await search_knowledge_base("meals entertainment deductible", top_k=5)
            # At least our entry should come back
            assert any("meals" in r["title"].lower() or "meals" in r["content"].lower() for r in results)


class TestProcessingRunsDB:
    async def test_create_and_complete_run(self, db_pool, seed_engagement, seed_firm):
        from app.state_machine import create_processing_run, complete_processing_run
        from app.tools.db import query_db

        run_id = await create_processing_run(
            engagement_id=seed_engagement,
            firm_id=seed_firm,
            agent_type="transaction",
            task_description="Integration test run",
            prompt_version="1.0.0",
        )
        assert run_id is not None

        rows = await query_db("SELECT * FROM processing_runs WHERE id = $1", [run_id])
        assert len(rows) == 1
        assert rows[0]["status"] == "RUNNING"
        assert rows[0]["prompt_version"] == "1.0.0"

        await complete_processing_run(run_id, result_summary="Done: 50 transactions processed")

        rows = await query_db("SELECT * FROM processing_runs WHERE id = $1", [run_id])
        assert rows[0]["status"] == "COMPLETE"
        assert rows[0]["completed_at"] is not None

    async def test_fail_run(self, db_pool, seed_engagement, seed_firm):
        from app.state_machine import create_processing_run, fail_processing_run
        from app.tools.db import query_db

        run_id = await create_processing_run(
            engagement_id=seed_engagement,
            firm_id=seed_firm,
            agent_type="document",
            task_description="Will fail",
        )
        await fail_processing_run(run_id, error_message="File not found: doc.pdf")

        rows = await query_db("SELECT * FROM processing_runs WHERE id = $1", [run_id])
        assert rows[0]["status"] == "FAILED"
        assert rows[0]["error_message"] == "File not found: doc.pdf"

    async def test_human_evaluation_event(self, db_pool, seed_engagement, seed_firm):
        from app.state_machine import record_human_evaluation
        from app.tools.db import query_db

        result = await record_human_evaluation(
            engagement_id=seed_engagement,
            firm_id=seed_firm,
            pipeline_stage="classification_uncertain",
            decision="APPROVED",
            decision_note="Confirmed as bank_statement after review",
        )
        assert "human_evaluation_id" in result
        assert result["decision"] == "APPROVED"

        rows = await query_db(
            "SELECT * FROM human_evaluation_events WHERE id = $1", [result["human_evaluation_id"]]
        )
        assert rows[0]["decision"] == "APPROVED"
        assert rows[0]["pipeline_stage"] == "classification_uncertain"
