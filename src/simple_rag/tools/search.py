"""search MCP tool — semantic vector search with graph traversal.

Uses VectorCypherRetriever to find relevant chunks, then traverses
Chunk → Entity → Community → Entity relationships with configurable hops.

The Cypher query is defined as a module-level constant for testability.
"""

from typing import Any, Optional

from fastmcp import FastMCP
from neo4j_graphrag.retrievers import VectorCypherRetriever

from simple_rag.graph.driver import _get_driver
from simple_rag.graph.pipeline import _get_kg_pipeline
from simple_rag.llm.factory import _get_embedder

# Module-level Cypher query constant (not inline in function)
CYPER_QUERY = """
// 1. Get parent Document metadata
OPTIONAL MATCH (node)-[:PART_OF]->(doc:Document)

// 2. Traverse from matched Chunk (`node`) -> Entity
OPTIONAL MATCH (node)-[:HAS_ENTITY]->(e:Entity)
WHERE ($entity_types IS NULL OR e.entity_type IN $entity_types)

// 3. Get Entity's Community summary (if present)
OPTIONAL MATCH (e)-[:IN_COMMUNITY]->(comm:Community)

// 4. Traverse Entity -> Entity relationships up to safe_hops
OPTIONAL MATCH path = (e)-[:RELATES_TO*1..{safe_hops}]-(neighbor:Entity)

WITH node, score, doc, e, comm,
     collect(DISTINCT {{
         name: neighbor.name,
         type: neighbor.entity_type,
         hops: length(path)
     }}) AS raw_connections

// Filter out null placeholder entries when no neighbors exist
WITH node, score, doc, e, comm,
     [c IN raw_connections WHERE c.name IS NOT NULL] AS connections

RETURN node.text AS chunk_text,
       doc.title AS document_title,
       e.name AS entity_name,
       e.entity_type AS entity_type,
       e.description AS entity_description,
       comm.summary AS community_summary,
       connections,
       score
ORDER BY score DESC
LIMIT $limit
"""

# Max hops constant
_MAX_HOPS = 4
_MIN_HOPS = 1


def _clamp_hops(max_hops: int) -> int:
    """Clamp max_hops to [1, 4] to prevent runaway traversals."""
    return max(_MIN_HOPS, min(int(max_hops), _MAX_HOPS))


_mcp_server: Optional[FastMCP] = None


def set_mcp_server(server: FastMCP) -> None:
    """Inject the MCP server instance for decorator registration."""
    global _mcp_server
    _mcp_server = server


async def search(
    query: str,
    datasource_id: Optional[str] = None,
    max_hops: int = 2,
    top_k: int = 5,
    limit: int = 20,
    entity_types: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Search the knowledge graph using semantic vector search and graph traversal.

    Finds the most relevant text chunks for a natural language query, then traverses
    connected Documents, Entities, Communities, and related Entities up to `max_hops`.

    Args:
        query: Natural language question or search query.
        datasource_id: Optional datasource schema identifier (passed to pipeline).
        max_hops: Number of relationship hops to traverse (default: 2, clamped to [1, 4]).
        top_k: Number of initial text chunks to retrieve via vector similarity (default: 5).
        limit: Maximum number of graph result records to return (default: 20).
        entity_types: Optional list of entity types to filter by (e.g., ["Person", "Organization"]).

    Returns:
        On success:
            {
                "status": "success",
                "results": [...],
                "total_count": int,
                "filters": {...},
            }
        On failure:
            {
                "status": "error",
                "results": [],
                "total_count": 0,
                "error": str,
            }
    """
    try:
        # Get driver and embedder
        driver = _get_driver()
        embedder = _get_embedder()

        # Clamp max_hops to prevent runaway traversals
        safe_hops = _clamp_hops(max_hops)

        # Build the Cypher query with the clamped hop count
        retrieval_query = CYPER_QUERY.format(safe_hops=safe_hops)

        # Use datasource_id for schema-aware indexing if provided
        index_name = "chunk_index"
        if datasource_id is not None:
            # Validate datasource exists via schema_loader
            schema_config = _get_kg_pipeline(datasource_id)
            # In future: switch index_name based on datasource schema
            # For now, use the validated datasource_id as an identifier
            # (schema validation prevents invalid datasource IDs)

        # Create the retriever
        retriever = VectorCypherRetriever(
            driver,
            index_name,
            retrieval_query,
            embedder,
        )

        # Execute the search
        search_response = retriever.search(
            query_text=query,
            top_k=top_k,
            query_params={
                "entity_types": entity_types if entity_types else None,
                "limit": limit,
            },
        )

        # Format RetrieverResult items into clean JSON-serializable dicts
        formatted_results = []
        for item in search_response.items:
            formatted_results.append({
                "content": item.content,
                "metadata": item.metadata or {},
            })

        return {
            "status": "success",
            "results": formatted_results,
            "total_count": len(formatted_results),
            "filters": {
                "query_text": query,
                "entity_types": entity_types,
                "max_hops": safe_hops,
                "top_k": top_k,
                "limit": limit,
            },
        }

    except Exception as exc:
        return {
            "status": "error",
            "results": [],
            "total_count": 0,
            "error": str(exc),
        }


# Register the tool if the MCP server is available
if _mcp_server is not None:
    _mcp_server.tool()(search)
