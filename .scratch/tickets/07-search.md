# 07: MCP tool — search

**What to build:** `tools/search.py` implements the `search` MCP tool — semantic vector search with graph traversal.

**Blocked by:** 02 (Config), 03 (Schema loader), 04 (LLM factory), 05 (Graph infrastructure)

**Status:** ready-for-agent

- [ ] `tools/search.py` with `@mcp.tool()` decorator, function `search(query: str, datasource_id: str | None = None, max_hops: int = 2, top_k: int = 5, limit: int = 20) -> dict`
- [ ] Returns `{"status": "success", "results": [...], "total_count", "filters": {...}}`
- [ ] `max_hops` clamped to [1, 4] to prevent runaway traversals
- [ ] `datasource_id` optional filter (passed through to pipeline if applicable)
- [ ] Uses `_get_embedder()` and `_get_driver()` from `llm/factory` and `graph/driver`
- [ ] Cypher query is a module-level constant (not inline in function)
- [ ] `tests/test_search.py` covers: query formatting, hop clamping (1, 2, 4, 5→4), datasource filtering, error handling

---

**Notes:** The Cypher query traverses Chunk → Entity → Community → Entity relationships with configurable hops. It returns chunks with entity metadata, community summaries, and connected entities. The `datasource_id` parameter allows filtering by schema (future use when schemas have separate indexes).
