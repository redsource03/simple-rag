"""Tests for simple_rag.tools.search MCP tool.

Covers:
- Success path with mocked VectorCypherRetriever
- max_hops clamping (1, 2, 4, 5→4)
- datasource_id passed to pipeline
- Error handling
- Cypher query is a module-level constant
"""

import asyncio
from unittest.mock import MagicMock, patch


def _make_mock_search_response(items: list[dict]) -> MagicMock:
    """Create a mock search response with items."""
    mock_resp = MagicMock()
    mock_items = []
    for item in items:
        mock_item = MagicMock()
        mock_item.content = item.get("content", "")
        mock_item.metadata = item.get("metadata")
        mock_items.append(mock_item)
    mock_resp.items = mock_items
    return mock_resp


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


class TestSearchSuccess:
    def test_search_returns_success_dict(self) -> None:
        """Success path returns status='success' with results and total_count."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([
            {"content": "chunk1", "metadata": {"score": 0.9}},
            {"content": "chunk2", "metadata": {"score": 0.8}},
        ])

        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ):
            result = asyncio.run(search(query="test query"))

        assert result["status"] == "success"
        assert result["total_count"] == 2
        assert len(result["results"]) == 2
        assert result["results"][0]["content"] == "chunk1"
        assert result["results"][1]["content"] == "chunk2"

    def test_search_passes_query_to_retriever(self) -> None:
        """The query string is passed to VectorCypherRetriever.search."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([])
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ):
            asyncio.run(search(query="my search query"))

        mock_retriever.search.assert_called_once()
        call_kwargs = mock_retriever.search.call_args.kwargs
        assert call_kwargs["query_text"] == "my search query"

    def test_search_default_max_hops(self) -> None:
        """Default max_hops is 2."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([])
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ) as mock_class:
            asyncio.run(search(query="test"))

        # Check the Cypher query contains the expected hop count
        # retrieval_query is the 3rd positional arg to VectorCypherRetriever constructor
        call_args = mock_class.call_args.args
        query = call_args[2]
        assert "1..2" in query

    def test_search_max_hops_4(self) -> None:
        """max_hops=4 produces 1..4 in the Cypher query."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([])
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ) as mock_class:
            asyncio.run(search(query="test", max_hops=4))

        call_args = mock_class.call_args.args
        query = call_args[2]
        assert "1..4" in query

    def test_search_max_hops_5_clamped_to_4(self) -> None:
        """max_hops=5 is clamped to 4."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([])
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ) as mock_class:
            asyncio.run(search(query="test", max_hops=5))

        call_args = mock_class.call_args.args
        query = call_args[2]
        assert "1..4" in query
        assert "1..5" not in query

    def test_search_max_hops_1(self) -> None:
        """max_hops=1 produces 1..1 in the Cypher query."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([])
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ) as mock_class:
            asyncio.run(search(query="test", max_hops=1))

        call_args = mock_class.call_args.args
        query = call_args[2]
        assert "1..1" in query

    def test_search_max_hops_0_clamped_to_1(self) -> None:
        """max_hops=0 is clamped to 1 (minimum)."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([])
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ) as mock_class:
            asyncio.run(search(query="test", max_hops=0))

        call_args = mock_class.call_args.args
        query = call_args[2]
        assert "1..1" in query

    def test_search_with_datasource_id(self) -> None:
        """datasource_id is passed to _get_kg_pipeline."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([])
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ), patch(
            "simple_rag.tools.search._get_kg_pipeline",
            return_value=MagicMock(),
        ) as mock_pipeline:
            asyncio.run(search(query="test", datasource_id="tech-architecture"))

        mock_pipeline.assert_called_once_with("tech-architecture")

    def test_search_with_entity_types(self) -> None:
        """entity_types filter is passed to the retriever."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([])
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ):
            asyncio.run(search(query="test", entity_types=["Person", "Organization"]))

        call_kwargs = mock_retriever.search.call_args.kwargs
        assert call_kwargs["query_params"]["entity_types"] == ["Person", "Organization"]

    def test_search_with_top_k(self) -> None:
        """top_k is passed to the retriever."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([])
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ):
            asyncio.run(search(query="test", top_k=10))

        call_kwargs = mock_retriever.search.call_args.kwargs
        assert call_kwargs["top_k"] == 10

    def test_search_with_limit(self) -> None:
        """limit is passed to the retriever."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([])
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ):
            asyncio.run(search(query="test", limit=50))

        call_kwargs = mock_retriever.search.call_args.kwargs
        assert call_kwargs["query_params"]["limit"] == 50

    def test_search_filters_in_response(self) -> None:
        """Response includes filters dict with applied parameters."""
        from simple_rag.tools.search import search

        mock_response = _make_mock_search_response([])
        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(return_value=mock_response)

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ):
            result = asyncio.run(search(query="test q", max_hops=3, top_k=7, limit=30))

        assert result["filters"]["query_text"] == "test q"
        assert result["filters"]["max_hops"] == 3
        assert result["filters"]["top_k"] == 7
        assert result["filters"]["limit"] == 30


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestSearchError:
    def test_search_retriever_exception_returns_error(self) -> None:
        """VectorCypherRetriever exceptions are caught."""
        from simple_rag.tools.search import search

        mock_retriever = MagicMock()
        mock_retriever.search = MagicMock(side_effect=RuntimeError("Neo4j timeout"))

        with patch(
            "simple_rag.tools.search._get_driver",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search._get_embedder",
            return_value=MagicMock(),
        ), patch(
            "simple_rag.tools.search.VectorCypherRetriever",
            return_value=mock_retriever,
        ):
            result = asyncio.run(search(query="test"))

        assert result["status"] == "error"
        assert "Neo4j timeout" in result["error"]
        assert result["results"] == []
        assert result["total_count"] == 0


# ---------------------------------------------------------------------------
# Module-level Cypher query
# ---------------------------------------------------------------------------


class TestCypherQueryConstant:
    def test_cypher_query_is_module_constant(self) -> None:
        """CYPHER_QUERY is defined at module level."""
        from simple_rag.tools import search as search_module

        assert hasattr(search_module, "CYPHER_QUERY")

    def test_cypher_query_contains_entity_traversal(self) -> None:
        """Cypher query contains Entity traversal pattern."""
        from simple_rag.tools import search as search_module

        assert "Entity" in search_module.CYPHER_QUERY

    def test_cypher_query_contains_community(self) -> None:
        """Cypher query contains Community traversal."""
        from simple_rag.tools import search as search_module

        assert "Community" in search_module.CYPHER_QUERY

    def test_cypher_query_contains_chunk(self) -> None:
        """Cypher query contains Chunk traversal."""
        from simple_rag.tools import search as search_module

        assert "Chunk" in search_module.CYPHER_QUERY

    def test_cypher_query_contains_entity_types_filter(self) -> None:
        """Cypher query contains entity_types parameter filter."""
        from simple_rag.tools import search as search_module

        assert "entity_types" in search_module.CYPHER_QUERY
