"""Tests for simple_rag.tools.add_document MCP tool.

Covers:
- Success path with mocked pipeline result
- Invalid datasource_id error (ValueError from schema_loader)
- Pipeline error handling (exception propagation)
- Tags/source default handling
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_pipeline_result(
    entities_count: int = 5,
    relationships_count: int = 8,
    communities_count: int = 2,
) -> MagicMock:
    """Create a mock pipeline run result with entity/relationship/community counts."""
    result = MagicMock()
    result.entities_count = entities_count
    result.relationships_count = relationships_count
    result.communities_count = communities_count
    return result


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


class TestAddDocumentSuccess:
    def test_add_document_returns_success_dict(self) -> None:
        """Success path returns status='success' with entity/relationship counts."""
        from simple_rag.tools.add_document import add_document

        mock_result = _make_mock_pipeline_result(
            entities_count=5,
            relationships_count=8,
            communities_count=2,
        )
        mock_pipeline = MagicMock()
        mock_pipeline.run_async = AsyncMock(return_value=mock_result)

        with patch(
            "simple_rag.tools.add_document._get_kg_pipeline",
            return_value=mock_pipeline,
        ):
            result = asyncio.run(
                add_document(
                    datasource_id="tech-architecture",
                    content="Test document content",
                    title="Test Doc",
                    source="https://example.com",
                    tags=["test"],
                )
            )

        assert result["status"] == "success"
        assert result["entities_extracted"] == 5
        assert result["relationships_extracted"] == 8
        assert result["communities_found"] == 2
        assert result["source"] == "https://example.com"
        assert result["tags"] == ["test"]
        assert result["title"] == "Test Doc"

    def test_add_document_calls_pipeline_with_content(self) -> None:
        """Pipeline is called with the document content via run_async(text=...)."""
        from simple_rag.tools.add_document import add_document

        mock_result = _make_mock_pipeline_result()
        mock_pipeline = MagicMock()
        mock_pipeline.run_async = AsyncMock(return_value=mock_result)

        with patch(
            "simple_rag.tools.add_document._get_kg_pipeline",
            return_value=mock_pipeline,
        ):
            asyncio.run(
                add_document(
                    datasource_id="tech-architecture",
                    content="Hello world",
                    title="Hello",
                )
            )

        mock_pipeline.run_async.assert_awaited_once_with(text="Hello world")

    def test_add_document_default_tags_is_empty_list(self) -> None:
        """When tags is None, the result defaults to an empty list."""
        from simple_rag.tools.add_document import add_document

        mock_result = _make_mock_pipeline_result()
        mock_pipeline = MagicMock()
        mock_pipeline.run_async = AsyncMock(return_value=mock_result)

        with patch(
            "simple_rag.tools.add_document._get_kg_pipeline",
            return_value=mock_pipeline,
        ):
            result = asyncio.run(
                add_document(
                    datasource_id="tech-architecture",
                    content="content",
                    title="Doc",
                    tags=None,
                )
            )

        assert result["tags"] == []

    def test_add_document_default_source_is_none(self) -> None:
        """When source is None, it remains None in the result."""
        from simple_rag.tools.add_document import add_document

        mock_result = _make_mock_pipeline_result()
        mock_pipeline = MagicMock()
        mock_pipeline.run_async = AsyncMock(return_value=mock_result)

        with patch(
            "simple_rag.tools.add_document._get_kg_pipeline",
            return_value=mock_pipeline,
        ):
            result = asyncio.run(
                add_document(
                    datasource_id="tech-architecture",
                    content="content",
                    title="Doc",
                    source=None,
                )
            )

        assert result["source"] is None


# ---------------------------------------------------------------------------
# Invalid datasource_id
# ---------------------------------------------------------------------------


class TestAddDocumentInvalidDatasource:
    def test_add_document_invalid_datasource_returns_error(self) -> None:
        """Invalid datasource_id raises ValueError which is caught and returned as error."""
        from simple_rag.tools.add_document import add_document

        with patch(
            "simple_rag.tools.add_document._get_kg_pipeline",
            side_effect=ValueError("Schema 'nonexistent' not found"),
        ):
            result = asyncio.run(
                add_document(
                    datasource_id="nonexistent",
                    content="content",
                    title="Doc",
                )
            )

        assert result["status"] == "error"
        assert "nonexistent" in result["error"]

    def test_add_document_invalid_datasource_does_not_call_pipeline(self) -> None:
        """Pipeline should not be called when datasource_id is invalid."""
        from simple_rag.tools.add_document import add_document

        mock_pipeline = MagicMock()
        mock_pipeline.run_async = AsyncMock()

        with patch(
            "simple_rag.tools.add_document._get_kg_pipeline",
            side_effect=ValueError("Schema 'nonexistent' not found"),
        ):
            asyncio.run(
                add_document(
                    datasource_id="nonexistent",
                    content="content",
                    title="Doc",
                )
            )

        mock_pipeline.run_async.assert_not_called()


# ---------------------------------------------------------------------------
# Pipeline error handling
# ---------------------------------------------------------------------------


class TestAddDocumentPipelineError:
    def test_add_document_pipeline_exception_returns_error(self) -> None:
        """Pipeline errors are caught and returned as error dict."""
        from simple_rag.tools.add_document import add_document

        mock_pipeline = MagicMock()
        mock_pipeline.run_async = AsyncMock(
            side_effect=RuntimeError("Neo4j connection failed")
        )

        with patch(
            "simple_rag.tools.add_document._get_kg_pipeline",
            return_value=mock_pipeline,
        ):
            result = asyncio.run(
                add_document(
                    datasource_id="tech-architecture",
                    content="content",
                    title="Doc",
                )
            )

        assert result["status"] == "error"
        assert "Neo4j connection failed" in result["error"]
        assert result["title"] == "Doc"

    def test_add_document_generic_exception_returns_error(self) -> None:
        """Any exception during pipeline run is caught."""
        from simple_rag.tools.add_document import add_document

        mock_pipeline = MagicMock()
        mock_pipeline.run_async = AsyncMock(side_effect=Exception("unexpected"))

        with patch(
            "simple_rag.tools.add_document._get_kg_pipeline",
            return_value=mock_pipeline,
        ):
            result = asyncio.run(
                add_document(
                    datasource_id="tech-architecture",
                    content="content",
                    title="Doc",
                )
            )

        assert result["status"] == "error"
        assert "unexpected" in result["error"]


# ---------------------------------------------------------------------------
# Integration: pipeline selection by datasource_id
# ---------------------------------------------------------------------------


class TestAddDocumentDatasourceSelection:
    def test_add_document_passes_datasource_to_pipeline_factory(self) -> None:
        """_get_kg_pipeline is called with the correct datasource_id."""
        from simple_rag.tools.add_document import add_document

        mock_result = _make_mock_pipeline_result()
        mock_pipeline = MagicMock()
        mock_pipeline.run_async = AsyncMock(return_value=mock_result)

        with patch(
            "simple_rag.tools.add_document._get_kg_pipeline",
            return_value=mock_pipeline,
        ) as mock_factory:
            asyncio.run(
                add_document(
                    datasource_id="research-paper",
                    content="content",
                    title="Doc",
                )
            )

        mock_factory.assert_called_once_with("research-paper")
