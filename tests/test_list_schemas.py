"""Tests for simple_rag.tools.list_schemas MCP tool.

Covers:
- Success path returns schema list
- Error handling
- Tool registration pattern
"""

import asyncio
from unittest.mock import patch


class TestListSchemasSuccess:
    def test_list_schemas_returns_success(self) -> None:
        """Success path returns status='success' with schemas list."""
        from simple_rag.tools.list_schemas import list_schemas

        mock_schema_list = [
            {"id": "tech-architecture", "name": "Tech Architecture"},
            {"id": "product-docs", "name": "Product Docs"},
        ]

        with patch(
            "simple_rag.tools.list_schemas._list_schemas",
            return_value=mock_schema_list,
        ):
            result = asyncio.run(list_schemas())

        assert result["status"] == "success"
        assert result["schemas"] == mock_schema_list
        assert len(result["schemas"]) == 2

    def test_list_schemas_empty_dir(self) -> None:
        """Empty schemas directory returns empty list."""
        from simple_rag.tools.list_schemas import list_schemas

        with patch(
            "simple_rag.tools.list_schemas._list_schemas",
            return_value=[],
        ):
            result = asyncio.run(list_schemas())

        assert result["status"] == "success"
        assert result["schemas"] == []
        assert len(result["schemas"]) == 0


class TestListSchemasError:
    def test_list_schemas_error_returns_error_dict(self) -> None:
        """Errors are caught and returned as error dict."""
        from simple_rag.tools.list_schemas import list_schemas

        with patch(
            "simple_rag.tools.list_schemas._list_schemas",
            side_effect=RuntimeError("Schema dir not found"),
        ):
            result = asyncio.run(list_schemas())

        assert result["status"] == "error"
        assert result["schemas"] == []
        assert "Schema dir not found" in result["error"]


class TestListSchemasToolRegistration:
    def test_list_schemas_has_set_mcp_server(self) -> None:
        """list_schemas module supports MCP server injection."""
        from simple_rag.tools import list_schemas as ls_module

        assert hasattr(ls_module, "set_mcp_server")
        assert callable(ls_module.set_mcp_server)

    def test_list_schemas_is_async(self) -> None:
        """list_schemas is an async function."""
        import inspect

        from simple_rag.tools.list_schemas import list_schemas

        assert inspect.iscoroutinefunction(list_schemas)
