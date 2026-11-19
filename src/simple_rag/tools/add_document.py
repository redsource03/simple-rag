"""add_document MCP tool.

Adds a document to the knowledge graph using the SimpleKGPipeline for the
given datasource_id. Uses schema_loader for datasource validation.

Returns a structured result with entity/relationship/community counts on
success, or an error dict on failure.
"""

from typing import Any, Optional

from fastmcp import FastMCP

from simple_rag.graph.pipeline import _get_kg_pipeline

# The MCP server instance is injected by the caller (main.py or mcp_server.py).
# This module is imported after the server is created so the decorator works.
# We use a module-level variable that gets set by the server bootstrap.
_mcp_server: Optional[FastMCP] = None


def set_mcp_server(server: FastMCP) -> None:
    """Inject the MCP server instance for decorator registration."""
    global _mcp_server
    _mcp_server = server


async def add_document(
    datasource_id: str,
    content: str,
    title: str,
    source: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Add a document to the knowledge graph via SimpleKGPipeline.

    Args:
        datasource_id: The schema identifier (e.g., ``"tech-architecture"``).
        content: The full document content to process.
        title: A descriptive title for the document.
        source: Optional source of the document (URL, file path, author).
        tags: Optional tags for categorizing the document.

    Returns:
        On success:
            {
                "status": "success",
                "title": str,
                "entities_extracted": int,
                "relationships_extracted": int,
                "communities_found": int,
                "source": str | None,
                "tags": list[str],
                "message": str,
            }
        On failure:
            {
                "status": "error",
                "title": str,
                "error": str,
            }
    """
    try:
        # _get_kg_pipeline validates datasource_id via schema_loader internally
        kg_pipeline = _get_kg_pipeline(datasource_id)

        # Run the knowledge graph pipeline on the text
        result = await kg_pipeline.run_async(text=content)

        return {
            "status": "success",
            "title": title,
            "entities_extracted": result.entities_count if hasattr(result, "entities_count") else 0,
            "relationships_extracted": result.relationships_count if hasattr(result, "relationships_count") else 0,
            "communities_found": result.communities_count if hasattr(result, "communities_count") else 0,
            "source": source,
            "tags": tags or [],
            "message": "Extracted entities and relationships, built community summaries",
        }

    except ValueError as exc:
        # Invalid datasource_id — schema not found
        return {
            "status": "error",
            "title": title,
            "error": str(exc),
        }

    except Exception as exc:
        # Any pipeline error (Neo4j connection, LLM failure, etc.)
        return {
            "status": "error",
            "title": title,
            "error": str(exc),
        }


# Register the tool if the MCP server is available
if _mcp_server is not None:
    _mcp_server.tool()(add_document)
