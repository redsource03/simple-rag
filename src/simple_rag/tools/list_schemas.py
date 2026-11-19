"""list_schemas MCP tool — list available predefined schemas.

Returns the list of datasource identifiers (schema names) that are
available for use with ``add_document`` and ``search`` tools.
"""

from typing import Any, Optional

from fastmcp import FastMCP

from simple_rag.schema_loader import list_schemas as _list_schemas


# The MCP server instance is injected by the caller (mcp_server.py).
_mcp_server: Optional[FastMCP] = None


def set_mcp_server(server: FastMCP) -> None:
    """Inject the MCP server instance for decorator registration."""
    global _mcp_server
    _mcp_server = server


async def list_schemas() -> dict[str, Any]:
    """List all available predefined knowledge-graph schemas.

    Returns:
        On success:
            {
                "status": "success",
                "schemas": [
                    {"id": "tech-architecture", "name": "Tech Architecture"},
                    ...
                ],
            }
        On failure:
            {
                "status": "error",
                "schemas": [],
                "error": str,
            }
    """
    try:
        schema_list = _list_schemas()
        return {
            "status": "success",
            "schemas": schema_list,
        }

    except Exception as exc:
        return {
            "status": "error",
            "schemas": [],
            "error": str(exc),
        }


# Register the tool if the MCP server is available
if _mcp_server is not None:
    _mcp_server.tool()(list_schemas)
