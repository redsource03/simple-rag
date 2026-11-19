# 05: Graph infrastructure — Neo4j driver + pipeline factory

**What to build:** `graph/driver.py` manages Neo4j driver lifecycle and vector index creation. `graph/pipeline.py` creates `SimpleKGPipeline` instances using the schema loader.

**Blocked by:** 01 (Prefactoring — rename package to simple_rag and fix pyproject.toml)

**Status:** ready-for-agent

- [ ] `graph/driver.py` with `_get_driver() -> GraphDatabase.Driver` (singleton lifecycle)
- [ ] `graph/driver.py` with `_ensure_vector_index()` that creates chunk_index and entity_index if they don't exist
- [ ] `graph/pipeline.py` with `_get_kg_pipeline(datasource_id) -> SimpleKGPipeline` that loads schema via `schema_loader.build_pipeline_config()`
- [ ] `_get_kg_pipeline()` raises `ValueError` if datasource_id is not found in schemas
- [ ] `_get_kg_pipeline()` uses `_get_llm()` and `_get_embedder()` from `llm/factory`
- [ ] `tests/test_driver.py` covers: driver creation, vector index creation (mocked Neo4j driver)
- [ ] `tests/test_pipeline.py` covers: pipeline creation with valid/invalid datasource_id

---

**Notes:** The pipeline factory is the seam between config and the GraphRAG pipeline. It uses `schema_loader.build_pipeline_config()` to get the node_types/relationship_types/patterns for the datasource. The vector index creation uses `create_vector_index()` from `neo4j_graphrag.indexes`.
