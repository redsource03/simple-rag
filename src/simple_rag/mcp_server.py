"""MCP server bootstrap for simple_rag.

Creates the ``FastMCP`` server, registers all tools, and provides
the ``create_mcp_server(config)`` factory used by ``__main__.py``.
"""

from fastmcp import FastMCP

from simple_rag.config import AppConfig
from simple_rag.tools import add_document, list_schemas, search


def create_mcp_server(config: AppConfig) -> FastMCP:
    """Create and configure the MCP server.

    Args:
        config: Application configuration from environment variables.

    Returns:
        A configured ``FastMCP`` instance with all tools registered.
    """
    server = FastMCP(
        name=config.mcp.server_name,
        instructions=(
            "This MCP server provides GraphRAG capabilities using Neo4j and "
            "SimpleKGPipeline. Available tools: add_document, search, list_schemas."
        ),
    )

    # Inject the server instance so tool modules can register themselves
    add_document.set_mcp_server(server)
    search.set_mcp_server(server)
    list_schemas.set_mcp_server(server)

    return server
