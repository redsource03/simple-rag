import asyncio
import threading

from fastmcp import FastMCP
from typing import List, Optional, Any
from starlette.requests import Request
from starlette.responses import  JSONResponse

from neo4j import GraphDatabase
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.embeddings import OllamaEmbeddings
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.embeddings import OpenAIEmbeddings

from simple_rag.config import Neo4jConfig, ProviderConfig

# Initialize FastMCP server
mcp = FastMCP(
    "Local RAG",
    instructions="""This MCP server provides GraphRAG capabilities using Neo4j and SimpleKGPipeline.

Available tools:
- add_document: Add a document and build knowledge graph (entities + relationships)
- search_documents: Search the knowledge base using vector similarity
- graph_search: Search using graph traversal and relationship paths

The server uses Neo4j GraphRAG with SimpleKGPipeline for knowledge graph construction.
Ensure Neo4j and Ollama are running before using these tools."""
)

# Global instances
_driver: Optional[GraphDatabase.Driver] = None
_kg_pipeline: Optional[SimpleKGPipeline] = None
_vector_retriever: Optional[VectorRetriever] = None
_chunk_index = "chunk_index"
_entity_index = "entity_index"


_text_splitter = FixedSizeSplitter(
    chunk_size=2800,
    chunk_overlap=400,
    approximate=True
)


def _ensure_vector_index() -> None:
    """Create vector indexes for chunks and entities if they don't exist.
    
    Creates the following indexes:
    - chunk_index: for Chunk nodes with embedding property
    - entity_index: for Entity nodes with embedding property
    """
    driver = _get_driver()
    neo4j_config = Neo4jConfig.from_env()
    provider_config = ProviderConfig.from_env()
    
    # List of indexes to create
    indexes_to_create = [
        {"name": _chunk_index, "label": "Chunk", "embedding_property": "embedding"}
    ]
    
    try:
        with driver.session(database=neo4j_config.database) as session:
            for index_config in indexes_to_create:
                index_name = index_config["name"]
                label = index_config["label"]
                embedding_property = index_config["embedding_property"]
                
                # Check if index already exists by name only
                # Neo4j SHOW INDEXES returns all indexes; filter by name
                # This works across all Neo4j versions (4.x and 5.x)
                result = session.run(
                    "SHOW INDEXES WHERE name = $index_name",
                    index_name=index_name
                )
                existing_indexes = list(result)
                
                if not existing_indexes:
                    print(f"Creating vector index '{index_name}' for {label} nodes...")
                    create_vector_index(
                        driver,
                        index_name,
                        label=label,
                        embedding_property=embedding_property,
                        dimensions=provider_config.embedding_dimension,
                        similarity_fn="euclidean",
                    )
                    print(f"Vector index '{index_name}' created successfully")
                else:
                    print(f"Vector index '{index_name}' already exists")
    except Exception as e:
        print(f"Warning: Could not create vector indexes: {e}")


def _get_driver() -> GraphDatabase.Driver:
    """Get or create the Neo4j driver instance."""
    global _driver
    if _driver is None:
        neo4j_config = Neo4jConfig.from_env()
        _driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=neo4j_config.auth,
            max_connection_lifetime=neo4j_config.max_connection_lifetime,
            max_connection_pool_size=neo4j_config.max_connection_pool_size,
            connection_acquisition_timeout=neo4j_config.connection_acquisition_timeout
        )
        print(f"Connected to Neo4j at {neo4j_config.uri}")
        
        # Ensure vector index exists
        #_ensure_vector_index()
    
    return _driver


class RateLimitedOllamaLLM(OpenAILLM):
    """OllamaLLM subclass that caps concurrent sync and async requests."""

    def __init__(
        self,
        model_name: str,
        max_concurrent: int = 1,
        model_params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            model_name=model_name,
            model_params=model_params,
            **kwargs,
        )
        self._max_concurrent = max_concurrent
        self._async_sem: Optional[asyncio.Semaphore] = None
        self._sync_sem = threading.Semaphore(max_concurrent)

    def _get_async_semaphore(self) -> asyncio.Semaphore:
        # Lazily instantiate inside the active event loop to avoid loop-binding errors
        if self._async_sem is None:
            self._async_sem = asyncio.Semaphore(self._max_concurrent)
        return self._async_sem

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        with self._sync_sem:
            return super().invoke(*args, **kwargs)

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
        async with self._get_async_semaphore():
            return await super().ainvoke(*args, **kwargs)


def _get_ollama_llm() -> RateLimitedOllamaLLM:
    provider_config = ProviderConfig.from_env()

    return RateLimitedOllamaLLM(
        model_name=provider_config.llm_model,
        max_concurrent=provider_config.ollama_max_concurrency,
        base_url=provider_config.ollama_base_url,
        model_params={
          "temperature": provider_config.llm_temperature,
          "response_format": {"type": "json_object"},
          "reasoning_effort": "low",
          "extra_body": {
              "options": {
                  "num_ctx": provider_config.ollama_num_ctx,
              },
              "keep_alive": provider_config.ollama_num_keep_alive,
          },
      },
        timeout=None,
        api_key=provider_config.ollama_api_key
    )

def _get_embedder():
    provider_config = ProviderConfig.from_env()
    #embedder = OllamaEmbeddings(model=provider_config.embedding_model, host="http://localhost:4000",headers={"Authorization": f"Bearer {provider_config.api_key}"})
    embedder = OpenAIEmbeddings(
        model=provider_config.embedding_model,
        base_url=provider_config.embedding_base_url,
        api_key=provider_config.embedding_api_key
    )
    return embedder
def _get_kg_pipeline() -> SimpleKGPipeline:
    """Get or create the SimpleKGPipeline instance."""
    global _kg_pipeline
    if _kg_pipeline is None:
        neo4j_config = Neo4jConfig.from_env()
        provider_config = ProviderConfig.from_env()
        
        # Initialize LLM and Embedder
        #embedder = OllamaEmbeddings(model=provider_config.embedding_model)
        embedder = _get_embedder()
        print(f"Initializing with host: {provider_config.ollama_base_url}")
        print(f"Embedding model: {provider_config.embedding_model}")
        print(f"Chat model: {provider_config.llm_model}")
        llm = _get_ollama_llm()
        
        # Define node types as per GraphRAG specification
        node_types = ["Document", "Chunk", "Entity", "Community"]
        relationship_types = [
            "PART_OF",           # Chunk -> Document
            "HAS_ENTITY",        # Chunk -> Entity
            "RELATES_TO",        # Entity -> Entity
            "IN_COMMUNITY",      # Entity -> Community
            "PARENT_COMMUNITY"   # Community -> Community (hierarchy)
        ]
        patterns = [
            # Entity-Entity relationships (extracted from text)
            ("Entity", "RELATES_TO", "Entity"),
            # Entity-Community membership
            ("Entity", "IN_COMMUNITY", "Community"),
            # Community hierarchy
            ("Community", "PARENT_COMMUNITY", "Community"),
        ]
        
        _kg_pipeline = SimpleKGPipeline(
            llm=llm,
            driver=_get_driver(),
            embedder=embedder,
            schema={
                "node_types": node_types,
                "relationship_types": relationship_types,
                "patterns": patterns
            },
            text_splitter=_text_splitter,
            on_error="IGNORE",
            from_file=False
        )
        print("Initialized SimpleKGPipeline for GraphRAG knowledge graph construction")
    
    return _kg_pipeline


@mcp.tool()
async def add_document(
    content: str,
    title: str,
    source: Optional[str] = None,
    tags: Optional[List[str]] = None,
    category: Optional[str] = None
) -> dict:
    """Add a document to the GraphRAG knowledge base using SimpleKGPipeline.
    
    This tool builds a knowledge graph from the document content, extracting:
    - Entities (nodes): People, organizations, tools, concepts, locations
    - Relationships (edges): How entities are connected (RELATES_TO)
    - Community summaries: Grouped clusters of related entities with hierarchy
    
    The pipeline creates:
    - Document and Chunk nodes (with PART_OF relationships)
    - Entity nodes with embeddings (connected via HAS_ENTITY)
    - Entity relationships (RELATES_TO)
    - Community nodes with summaries (entities connected via IN_COMMUNITY)
    - Community hierarchy (PARENT_COMMUNITY relationships)
    
    Args:
        content: The full document content to process
        title: A descriptive title for the document
        source: Optional source of the document (e.g., URL, file path, author)
        tags: Optional tags for categorizing the document
        category: Optional category for the document
        
    Returns:
        Dictionary with:
        - status: 'success' or 'error'
        - title: Document title
        - entities_extracted: Number of entities found
        - relationships_extracted: Number of relationships found
        - communities_found: Number of communities identified
        - source: Document source
        - tags: Document tags
        
    Example:
        add_document(
            content="Paul C. works at RAG Agent and uses Neo4j for knowledge management.",
            title="RAG Agent Introduction",
            source="https://example.com",
            tags=["rag", "neo4j"],
            category="technical"
        )
    """
    try:
        kg_pipeline = _get_kg_pipeline()
        
        # Run the knowledge graph pipeline on the text
        result = await kg_pipeline.run_async(
            text=content
        )
        
        return {
            "status": "success",
            "title": title,
            "entities_extracted": result.entities_count if hasattr(result, 'entities_count') else 0,
            "relationships_extracted": result.relationships_count if hasattr(result, 'relationships_count') else 0,
            "communities_found": result.communities_count if hasattr(result, 'communities_count') else 0,
            "source": source,
            "tags": tags or [],
            "category": category,
            "message": "Extracted entities and relationships, built community summaries"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "title": title,
            "error": str(e)
        }


@mcp.tool()
async def graph_search(
    query_text: str,
    entity_types: Optional[List[str]] = None,
    max_hops: int = 2,
    top_k: int = 5,
    limit: int = 20,
) -> dict:
    """Search the knowledge graph using semantic vector search and graph traversal.

    Finds the most relevant text chunks for a natural language query, then traverses
    connected Documents, Entities, Communities, and related Entities up to `max_hops`.

    Args:
        query_text: Natural language question or search query.
        entity_types: Optional list of entity types to filter by (e.g., ["Person", "Organization"]).
        max_hops: Number of relationship hops to traverse between entities (default: 2, max: 4).
        top_k: Number of initial text chunks to retrieve via vector similarity (default: 5).
        limit: Maximum number of graph result records to return (default: 20).

    Returns:
        Dictionary containing status, retrieved results (chunks, entities, communities,
        connections), total_count, and applied filters.
    """
    try:
        driver = _get_driver()
        provider_config = ProviderConfig.from_env()
        #embedder = OllamaEmbeddings(model=provider_config.embedding_model)
        embedder = _get_embedder()

        # Clamp max_hops to prevent runaway multi-hop traversals
        safe_hops = max(1, min(int(max_hops), 4))

        cypher_retrieval_query = f"""
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

        retriever = VectorCypherRetriever(
            driver=driver,
            index_name=_chunk_index,
            retrieval_query=cypher_retrieval_query,
            embedder=embedder,
        )

        search_response = retriever.search(
            query_text=query_text,
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
                "query_text": query_text,
                "entity_types": entity_types,
                "max_hops": safe_hops,
                "top_k": top_k,
                "limit": limit,
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "results": [],
            "total_count": 0,
            "error": str(e),
        }

@mcp.tool()
async def  get_lexical_graph(
    entity_name: Optional[str] = None,
    depth: int = 2,
    include_communities: bool = True,
    limit: int = 100,
) -> dict:
    """Explore the entity-relation-entity lexical graph and optional community hierarchy.

    Use this tool when you have a specific entity name and want to inspect its
    direct or multi-hop relationships, connected entities, and community memberships.

    Args:
        entity_name: Optional starting entity name (case-insensitive match).
                     If omitted, returns the most frequent relationships in the graph.
        depth: Number of relationship hops to traverse between entities (default: 2, max: 4).
        include_communities: Whether to include Community memberships and parent communities.
        limit: Maximum number of relationship edges to return (default: 100).

    Returns:
        Dictionary containing status, nodes (with type/community info), relationships,
        total_count, and applied filters.
    """
    try:
        driver = _get_driver()
        safe_depth = max(1, min(int(depth), 4))

        query = f"""
        MATCH path = (e1:Entity)-[rels:RELATES_TO*1..{safe_depth}]-(e2:Entity)
        WHERE ($entity_name IS NULL OR toLower(e1.name) = toLower($entity_name))
        UNWIND relationships(path) AS rel
        WITH DISTINCT startNode(rel) AS src, endNode(rel) AS tgt, type(rel) AS relation_type

        // Optional community enrichment for source and target entities
        OPTIONAL MATCH (src)-[:IN_COMMUNITY]->(src_comm:Community)
        OPTIONAL MATCH (src_comm)-[:PARENT_COMMUNITY]->(src_parent:Community)
        OPTIONAL MATCH (tgt)-[:IN_COMMUNITY]->(tgt_comm:Community)

        RETURN src.name AS source,
               src.entity_type AS source_type,
               src_comm.id AS source_community,
               src_parent.id AS source_parent_community,
               tgt.name AS target,
               tgt.entity_type AS target_type,
               tgt_comm.id AS target_community,
               relation_type
        LIMIT $limit
        """

        with driver.session(database="neo4j") as session:
            result = session.run(
                query,
                entity_name=entity_name.strip() if entity_name else None,
                limit=limit,
            )

            relationships = []
            nodes_map = {}

            for row in result:
                src = row["source"]
                tgt = row["target"]

                relationships.append({
                    "source": src,
                    "target": tgt,
                    "relation_type": row["relation_type"],
                })

                if src and src not in nodes_map:
                    node_info = {
                        "name": src,
                        "entity_type": row["source_type"],
                    }
                    if include_communities and row["source_community"] is not None:
                        node_info["community"] = row["source_community"]
                        if row["source_parent_community"] is not None:
                            node_info["parent_community"] = row["source_parent_community"]
                    nodes_map[src] = node_info

                if tgt and tgt not in nodes_map:
                    node_info = {
                        "name": tgt,
                        "entity_type": row["target_type"],
                    }
                    if include_communities and row["target_community"] is not None:
                        node_info["community"] = row["target_community"]
                    nodes_map[tgt] = node_info

            return {
                "status": "success",
                "nodes": list(nodes_map.values()),
                "relationships": relationships,
                "total_count": len(relationships),
                "filters": {
                    "entity_name": entity_name,
                    "depth": safe_depth,
                    "include_communities": include_communities,
                    "limit": limit,
                },
            }

    except Exception as e:
        return {
            "status": "error",
            "nodes": [],
            "relationships": [],
            "total_count": 0,
            "error": str(e),
        }
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "mcp-server"})

def main():
    """Entry point for the RAG agent server."""
    # Ensure vector index exists
    _ensure_vector_index()
    mcp.run(transport="http", host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
