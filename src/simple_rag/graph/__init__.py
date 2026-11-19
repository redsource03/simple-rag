"""simple_rag.graph — Neo4j driver and pipeline factory.

Exports:
    - driver._get_driver()
    - driver._ensure_vector_index()
    - pipeline._get_kg_pipeline(datasource_id)
"""

from simple_rag.graph import driver, pipeline

__all__ = ["driver", "pipeline"]
