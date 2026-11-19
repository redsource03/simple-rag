# 06: MCP tool — add_document

**What to build:** `tools/add_document.py` implements the `add_document` MCP tool. This is the first complete tracer bullet — after this ticket the agent can add a document to the knowledge graph.

**Blocked by:** 02 (Config), 03 (Schema loader), 04 (LLM factory), 05 (Graph infrastructure)

**Status:** ready-for-agent

- [ ] `tools/add_document.py` with `@mcp.tool()` decorator, function `add_document(datasource_id: str, content: str, title: str, source: str | None = None, tags: list[str] | None = None) -> dict`
- [ ] Returns `{"status": "success", "entities_extracted", "relationships_extracted", "communities_found", ...}` on success
- [ ] Returns `{"status": "error", "error": str}` on failure (invalid datasource_id, pipeline error)
- [ ] Uses `_get_kg_pipeline(datasource_id)` from `graph/pipeline`
- [ ] Uses `schema_loader` for datasource validation
- [ ] `tests/test_add_document.py` covers: success path (mocked pipeline), invalid datasource_id error, pipeline error handling
- [ ] Tool is registered in `mcp_server.py` (or the MCP server ticket)

---

**Notes:** This is the first **complete** tracer bullet. After this ticket, an agent (like the ADK agent) can call `add_document(datasource_id="tech-architecture", content="...", title="...")` and get back a structured result with entity/relationship counts. The datasource_id maps to a YAML schema via `schema_loader`. The agent picks the datasource_id — it doesn't pass an explicit intent parameter.
