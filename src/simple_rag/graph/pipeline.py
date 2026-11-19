"""Pipeline factory for SimpleKGPipeline.

Creates ``SimpleKGPipeline`` instances using the schema loader,
LLM factory, and graph driver.
"""

from typing import Any, Optional

from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.components.text_splitters.fixed_size_splitter import FixedSizeSplitter

from simple_rag.graph.driver import _get_driver, _ensure_vector_index
from simple_rag.llm.factory import _get_llm, _get_embedder
from simple_rag.schema_loader import build_pipeline_config


# Default text splitter configuration
_DEFAULT_CHUNK_SIZE = 2800
_DEFAULT_CHUNK_OVERLAP = 400


def _get_kg_pipeline(
    datasource_id: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = _DEFAULT_CHUNK_OVERLAP,
) -> SimpleKGPipeline:
    """Create a ``SimpleKGPipeline`` for the given datasource_id.

    Args:
        datasource_id: The schema identifier to use (e.g., ``"tech-architecture"``).
        chunk_size: Text chunk size for the ``FixedSizeSplitter`` (default: 2800).
        chunk_overlap: Text chunk overlap (default: 400).

    Returns:
        A configured ``SimpleKGPipeline`` instance.

    Raises:
        ValueError: If the datasource_id is not found in predefined schemas.
    """
    # Get schema config from loader
    schema_config = build_pipeline_config(datasource_id)

    # Get LLM and embedder from factory
    llm = _get_llm()
    embedder = _get_embedder()

    # Ensure vector indexes exist
    driver = _get_driver()
    _ensure_vector_index(driver)

    # Build the pipeline
    pipeline = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        schema=schema_config,
        text_splitter=FixedSizeSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            approximate=True,
        ),
        on_error="IGNORE",
        from_file=False,
    )

    return pipeline
