"""Neo4j driver lifecycle and vector index management.

Provides:
- ``_get_driver()`` — singleton driver instance
- ``_ensure_vector_index()`` — creates chunk_index and entity_index if missing
"""

from typing import Optional

from neo4j import GraphDatabase
from neo4j_graphrag.indexes import create_vector_index

from simple_rag.config import Neo4jConfig, ProviderConfig

# Global singleton
_driver: Optional[GraphDatabase.Driver] = None

# Default vector index names
_CHUNK_INDEX = "chunk_index"
_ENTITY_INDEX = "entity_index"


def _get_driver() -> GraphDatabase.Driver:
    """Get or create the Neo4j driver instance (singleton lifecycle).

    Returns:
        A ``neo4j.Driver`` connected to the configured Neo4j instance.
    """
    global _driver
    if _driver is None:
        neo4j_config = Neo4jConfig.from_env()
        _driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=neo4j_config.auth,
            max_connection_lifetime=neo4j_config.max_connection_lifetime,
            max_connection_pool_size=neo4j_config.max_connection_pool_size,
            connection_acquisition_timeout=neo4j_config.connection_acquisition_timeout,
        )
    return _driver


def _ensure_vector_index(driver: GraphDatabase.Driver) -> None:
    """Create vector indexes for chunks and entities if they don't exist.

    Creates:
        - ``chunk_index``: for Chunk nodes with embedding property
        - ``entity_index``: for Entity nodes with embedding property

    Args:
        driver: The Neo4j driver instance.

    Notes:
        Uses ``SHOW INDEXES`` to check existence (works across Neo4j 4.x/5.x).
        Exceptions are silently caught — index creation is best-effort.
    """
    neo4j_config = Neo4jConfig.from_env()
    provider_config = ProviderConfig.from_env()

    indexes_to_create = [
        {"name": _CHUNK_INDEX, "label": "Chunk", "embedding_property": "embedding"},
        {"name": _ENTITY_INDEX, "label": "Entity", "embedding_property": "embedding"},
    ]

    try:
        with driver.session(database=neo4j_config.database) as session:
            for index_config in indexes_to_create:
                index_name = index_config["name"]
                label = index_config["label"]
                embedding_property = index_config["embedding_property"]

                # Check if index already exists
                result = session.run(
                    "SHOW INDEXES WHERE name = $index_name",
                    index_name=index_name,
                )
                existing_indexes = list(result)

                if not existing_indexes:
                    create_vector_index(
                        driver,
                        index_name,
                        label=label,
                        embedding_property=embedding_property,
                        dimensions=provider_config.embedding_dimension,
                        similarity_fn="euclidean",
                    )
    except Exception:
        # Index creation is best-effort; don't block pipeline creation
        pass
