import pytest
from unittest.mock import patch, AsyncMock


class TestSearchKnowledgeBase:
    async def test_returns_ranked_results(self):
        mock_embedding = [0.1] * 1024
        mock_rows = [
            {"id": "kb-001", "source": "ETA", "section": "s.169(1)", "title": "ITC eligibility", "content": "An ITC may be claimed...", "similarity": 0.92},
            {"id": "kb-002", "source": "ETA", "section": "s.67.1", "title": "Meals 50% rule", "content": "50% of meal expenses...", "similarity": 0.88},
        ]

        with patch("app.models.llm.get_embedding", AsyncMock(return_value=mock_embedding)), \
             patch("app.tools.knowledge.query_db", AsyncMock(return_value=mock_rows)):

            from app.tools.knowledge import search_knowledge_base
            results = await search_knowledge_base("ITC meals restriction", top_k=2)

        assert len(results) == 2
        assert results[0]["similarity"] == 0.92
        assert results[0]["source"] == "ETA"
        assert "id" in results[0]

    async def test_filters_by_source(self):
        mock_embedding = [0.0] * 1024
        with patch("app.models.llm.get_embedding", AsyncMock(return_value=mock_embedding)), \
             patch("app.tools.knowledge.query_db", AsyncMock(return_value=[])) as mock_qdb:

            from app.tools.knowledge import search_knowledge_base
            await search_knowledge_base("CCA class 10", source="ITA", top_k=3)

        call_args = mock_qdb.call_args[0]
        assert "$2" in call_args[0]  # source filter in query
        assert call_args[1][1] == "ITA"

    async def test_no_source_filter(self):
        mock_embedding = [0.0] * 1024
        with patch("app.models.llm.get_embedding", AsyncMock(return_value=mock_embedding)), \
             patch("app.tools.knowledge.query_db", AsyncMock(return_value=[])) as mock_qdb:

            from app.tools.knowledge import search_knowledge_base
            await search_knowledge_base("GST remittance")

        call_args = mock_qdb.call_args[0]
        # Without source filter, second param is top_k (int)
        assert isinstance(call_args[1][1], int)


class TestAddKnowledgeEntry:
    async def test_adds_entry_with_embedding(self):
        mock_embedding = [0.5] * 1024
        mock_row = {"id": "kb-new"}

        with patch("app.models.llm.get_embedding", AsyncMock(return_value=mock_embedding)), \
             patch("app.tools.knowledge.write_db", AsyncMock(return_value=mock_row)) as mock_write:

            from app.tools.knowledge import add_knowledge_entry
            result = await add_knowledge_entry(
                source="ITA",
                title="Small business deduction",
                content="ITA s.125 allows...",
                section="s.125",
            )

        assert result["id"] == "kb-new"
        assert result["status"] == "added"
        call_data = mock_write.call_args[0][1]
        assert call_data["source"] == "ITA"
        assert call_data["embedding"] == mock_embedding
        assert call_data["section"] == "s.125"
