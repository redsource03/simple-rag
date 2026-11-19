# 08: MCP tool — list_schemas + MCP server + entry point + Docker + cleanup

**What to build:** Merged final ticket combining: list_schemas tool, MCP server setup, entry point, Docker stack, and cleanup. After this ticket, the project is fully production-ready.

**Blocked by:** 07 (MCP tool — search)

**Status:** ready-for-agent

### list_schemas tool
- [ ] `tools/list_schemas.py` with `@mcp.tool()` decorator, function `list_schemas() -> dict`
- [ ] Returns `{"status": "success", "schemas": [{id, description, node_types, relationship_types}, ...]}`
- [ ] Uses `schema_loader.list_schemas()`
- [ ] `tests/test_list_schemas.py` covers: returns 3 schemas, empty dir returns empty list

### MCP server
- [ ] `mcp_server.py` with FastMCP instance, tool registration, health endpoint
- [ ] `__main__.py` with `main()` that loads config, creates MCP server, registers tools, calls `mcp.run()`
- [ ] `python -m simple_rag` starts the server
- [ ] `pyproject.toml` `[project.scripts]` = `simple-rag = "simple_rag.__main__:main"`
- [ ] `tests/test_mcp_server.py` covers: server startup, health endpoint returns 200

### Docker
- [ ] `Dockerfile` copies `.agents/schemas/` into final image
- [ ] `docker-compose.yml` runs MCP server + Neo4j (Ollama stays on external server `paulcab-ms-7d75:11434`)
- [ ] `docker-compose.yml` has Neo4j health check, MCP server health check
- [ ] `.dockerignore` excludes `.agents/schemas/` from local build context
- [ ] `docker compose up` starts MCP server + Neo4j successfully

### Cleanup
- [ ] `save_rag.py` and `search_rag.py` removed from repo root
- [ ] `RAGConfig` and `ADKConfig` removed from `config.py`
- [ ] `src/simple_rag/__init__.py` exports public API (`AppConfig`, `schema_loader`, `llm.factory`)
- [ ] `README.md` created with project description, setup instructions, docker usage
- [ ] `docs/adr/0001-predefined-schemas.md` exists (from ticket #4)
- [ ] `poetry lock` runs without errors
- [ ] `python -m simple_rag` starts the server (no import errors)

---

**Notes:** This is the **final** ticket. After it completes:
- `python -m simple_rag` starts the MCP server
- `docker compose up` starts MCP server + Neo4j
- All three MCP tools (add_document, search, list_schemas) are implemented and tested
- The project has proper structure, tests, Docker deployment, and documentation
- The ADK agent can call `list_schemas()` to discover datasource IDs, then `add_document(datasource_id, content, title)` to add documents
