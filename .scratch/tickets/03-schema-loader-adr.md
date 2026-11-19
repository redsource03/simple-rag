# 03: Schema loader — YAML loader + ADR

**What to build:** `schema_loader.py` loads predefined YAML schemas from `.agents/schemas/` and provides discovery/validation functions.

**Blocked by:** 01 (Prefactoring — rename package to simple_rag and fix pyproject.toml)

**Status:** ready-for-agent

- [ ] `schema_loader.py` with functions: `load_schema(datasource_id)`, `list_schemas()`, `build_pipeline_config(datasource_id)`
- [ ] `load_schema()` returns schema dict (node_types, relationship_types, patterns, description) or `None` if not found
- [ ] `list_schemas()` returns list of dicts with `id`, `description`, `node_types`, `relationship_types`
- [ ] `build_pipeline_config()` returns dict suitable for `SimpleKGPipeline(schema=...)`
- [ ] `docs/adr/0001-predefined-schemas.md` documents the decision: schemas are predefined YAML, LLM picks the right one, never invents
- [ ] `tests/test_schema_loader.py` covers: `load_schema()` success/failure, `list_schemas()` discovery, `build_pipeline_config()` output shape
- [ ] Schema loader tests use temp directory with test YAML files (no real filesystem dependency)

---

**Notes:** The domain is **personal knowledge management** — schemas are the user's vocabulary. Predefined YAML is the source of truth. The LLM (ADK agent) picks the datasource_id; it never invents schemas. The three existing schemas (tech-architecture, research-paper, project-plan) are in `.agents/schemas/` and should not be touched by this ticket.
