# 0001 - Refactor Project Structure: Split Monolithic main.py into Production-Ready Layout

## Problem Statement

`src/rag_agent/main.py` is a 548-line monolithic file that contains:
- MCP server initialization and tool definitions (`add_document`, `graph_search`, `get_lexical_graph`)
- Neo4j driver lifecycle management (`_get_driver`, `_ensure_vector_index`)
- Knowledge graph pipeline factory (`_get_kg_pipeline`)
- Provider-agnostic LLM/embedder factory (`_get_llm`, `_get_embedder`, `RateLimitedOllamaLLM`)
- Vector index creation logic
- Health check endpoint
- `main()` entry point

This violates Python project structure conventions:
- No separation of concerns (tools, infrastructure, config all in one file)
- No testable units (everything is global-state function calls)
- No `__main__.py` entry point (only `python -m rag_agent.main` works)
- No `tests/` directory exists (zero tests)
- `config.py` is 190 lines of dataclasses with no validation
- No package-level `__init__.py` exports
- `RAGConfig` and `ADKConfig` are dead code in config.py
- `save_rag.py` and `search_rag.py` are legacy scripts still in the repo root
- No ADRs exist despite the domain-modeling skill being active
- `pyproject.toml` has conflicting `fastmcp` versions (`>=4.0.0` and `==4.1.6`)
- `pyproject.toml` declares `google-adk==2.14.0` but no code uses it

The user's domain is **personal knowledge management** ("documents → schemas → graph"), the project is a **MCP server** (not a CLI tool), and the Google ADK agent is a **separate service** that calls this MCP server.

## Solution

Refactor the project into a standard Python package layout with clear seams between:
1. **Config** - dataclasses, validation, env loading
2. **Schema loader** - YAML schema discovery and validation
3. **LLM provider** - provider-agnostic factory (OpenAI / Ollama)
4. **Graph infrastructure** - Neo4j driver, vector index, pipeline factory
5. **MCP tools** - individual tool implementations
6. **Entry point** - `__main__.py`

This makes every unit testable in isolation, follows the single-responsibility principle, and aligns with Python packaging standards (PEP 8, PEP 621).

## User Stories

1. As a developer, I want to run `python -m simple_rag` to start the MCP server, so that the project has a standard Python entry point.
2. As a developer, I want each MCP tool (`add_document`, `search`, `list_schemas`) in its own module, so that I can test and modify them independently.
3. As a developer, I want a provider-agnostic LLM factory that returns OpenAI or Ollama LLMs based on config, so that switching providers requires only env var changes.
4. As a developer, I want the Neo4j driver and vector indexes managed in a separate module, so that the MCP tools don't handle connection lifecycle.
5. As a developer, I want YAML schemas in `.agents/schemas/` loaded by a dedicated `schema_loader.py`, so that adding new schemas requires no code changes.
6. As a developer, I want a `tests/` directory with tests for config parsing, schema loading, and tool contracts, so that the project has baseline test coverage.
7. As a developer, I want `pyproject.toml` to have consistent dependency versions and a clean `[tool.setuptools]` or `[tool.poetry]` section, so that `pip install` and `poetry install` work reliably.
8. As a developer, I want dead code (`RAGConfig`, `ADKConfig`, `save_rag.py`, `search_rag.py`) removed, so that the codebase is clean and maintainable.
9. As a developer, I want an `__init__.py` that exports the public API of `simple_rag`, so that external consumers (like the ADK agent) can import cleanly.
10. As a developer, I want the Docker build to include `.agents/schemas/` in the final image, so that the MCP server can discover schemas at runtime.
11. As a developer, I want an ADR documenting the decision to use predefined YAML schemas (not dynamic/LLM-generated), so that future contributors understand the design rationale.
12. As a developer, I want the `RateLimitedOllamaLLM` class moved to its own module (`simple_rag/llm/rate_limiter.py`), so that it can be imported and tested independently.
13. As a developer, I want the MCP server `instructions` string to be a constant in the module, so that it can be updated without touching tool definitions.
14. As a developer, I want the Cypher query in `graph_search` to be a module-level constant, so that it can be reviewed and tested independently.
15. As a developer, I want the project renamed from `rag-agent` to `simple-rag` in `pyproject.toml`, so that the package name matches the repo and domain.

## Implementation Decisions

### Package Layout

```
src/
└── simple_rag/
    ├── __init__.py          # public API exports
    ├── __main__.py          # entry point: python -m simple_rag
    ├── config.py            # dataclasses: AppConfig, Neo4jConfig, ProviderConfig, MCPConfig
    ├── schema_loader.py     # load_schema(), list_schemas(), build_pipeline_config()
    ├── mcp_server.py        # FastMCP instance, tool decorators, health endpoint
    ├── tools/
    │   ├── __init__.py
    │   ├── add_document.py  # add_document datasource_id, content, title
    │   ├── search.py        # search query, datasource_id?, max_hops, top_k, limit
    │   └── list_schemas.py  # list_schemas()
    ├── graph/
    │   ├── __init__.py
    │   ├── driver.py        # _get_driver(), _ensure_vector_index()
    │   └── pipeline.py      # _get_kg_pipeline(datasource_id)
    └── llm/
        ├── __init__.py
        ├── factory.py       # _get_llm(), _get_embedder()
        └── rate_limiter.py  # RateLimitedOllamaLLM
```

### MCP Tool Contract (final)

- `add_document(datasource_id: str, content: str, title: str, source?: str, tags?: list[str]) -> dict`
  - The caller (ADK agent) picks `datasource_id` from `list_schemas()`.
  - Returns: `{"status": "success"/"error", "entities_extracted", "relationships_extracted", ...}`
- `search(query: str, datasource_id?: str, max_hops: int=2, top_k: int=5, limit: int=20) -> dict`
  - Optional `datasource_id` filters by schema.
  - Returns: `{"status": "success", "results": [...], "total_count", "filters": {...}}`
- `list_schemas() -> dict`
  - Returns: `{"status": "success", "schemas": [{"id", "description", "node_types", "relationship_types"}, ...]}`

### Provider Abstraction

- Config-driven via env vars: `LLM_PROVIDER=openai|ollama`, `EMBEDDING_PROVIDER=openai|ollama`
- `ProviderConfig` dataclass in `config.py` holds all provider settings (model, base_url, api_key, etc.)
- `llm/factory.py` returns the correct LLM/embedder instance based on config
- No code-level provider branching in tool modules

### Schema System

- Predefined YAML files in `.agents/schemas/` (versioned in git)
- `schema_loader.py` loads YAML, validates `node_types`/`relationship_types`/`patterns` keys
- `build_pipeline_config(datasource_id)` returns the dict for `SimpleKGPipeline(schema=...)`
- The LLM (ADK agent) **picks** the datasource_id; it never invents schemas
- Dead code removed: `RAGConfig`, `ADKConfig` from `config.py`

### Config Refactor

- `config.py` becomes a thin layer of dataclasses:
  - `Neo4jConfig` - Neo4j connection
  - `ProviderConfig` - unified LLM + embedding provider settings
  - `MCPConfig` - server host/port/log level
  - `AppConfig` - composes all above
- `AppConfig.to_dict()` for serialization (health endpoint, logging)
- `from_env()` classmethod for each config dataclass
- `load_dotenv()` called once at module import

### Docker

- `Dockerfile` copies `.agents/schemas/` into the final image
- `docker-compose.yml` includes: MCP server, Neo4j, and (optional) ADK agent container
- Ollama stays on external server `paulcab-ms-7d75:11434` (not containerized)
- `.dockerignore` excludes `.agents/schemas/` from local build context (it's mounted at runtime)

### Cleanup

- Remove `save_rag.py` and `search_rag.py` (legacy CLI scripts, replaced by MCP tools + TDD)
- Remove `RAGConfig` and `ADKConfig` from `config.py` (dead code)
- Fix `pyproject.toml`: rename to `simple-rag`, fix `fastmcp` version conflict, remove `google-adk` if unused
- Create `docs/adr/0001-predefined-schemas.md` documenting the schema decision
- Rename package from `rag_agent` to `simple_rag` (matches domain name)

### Entry Point

- `src/simple_rag/__main__.py` contains `main()` that:
  1. Loads config
  2. Creates MCP server instance
  3. Registers tools
  4. Calls `mcp.run(transport="http", ...)`
- `pyproject.toml` `[project.scripts]` updated to `simple-rag = "simple_rag.__main__:main"`

## Testing Decisions

### What makes a good test

- Only test **external behavior** (function return values, config parsing, schema discovery)
- Mock external dependencies (Neo4j driver, LLM calls, file I/O)
- Test the **seams** between modules, not internal implementation details
- Use `pytest` with `pytest-asyncio` for async tool tests

### Test modules

| Module | Tests |
|--------|-------|
| `config.py` | `test_config.py` - env var loading, default values, `to_dict()` |
| `schema_loader.py` | `test_schema_loader.py` - `load_schema()`, `list_schemas()`, `build_pipeline_config()`, missing schema handling |
| `tools/add_document.py` | `test_add_document.py` - success path, error path, invalid datasource_id |
| `tools/search.py` | `test_search.py` - query formatting, hop clamping, datasource filtering |
| `tools/list_schemas.py` | `test_list_schemas.py` - returns correct schema list |
| `llm/factory.py` | `test_factory.py` - OpenAI vs Ollama selection |
| `graph/driver.py` | `test_driver.py` - driver creation, index creation |

### Test infrastructure

- `tests/conftest.py` - shared fixtures (mock Neo4j driver, mock LLM, temp schema dir)
- `tests/test_mcp_tools.py` - integration tests for the MCP tool contract (mocked pipeline)
- No real Neo4j or LLM calls during tests (all mocked)
- Schema loader tests use a temp directory with test YAML files

### Prior art

- `pyproject.toml` already declares `pytest==8.2.0` and `pytest-asyncio==0.23.0`
- The project uses `pydantic-settings` pattern (dataclasses with `field(default_factory=lambda: os.getenv(...))`)
- `RateLimitedOllamaLLM` has `invoke()` and `ainvoke()` methods that can be mocked

## Out of Scope

- Google ADK agent implementation (it's a separate service)
- OpenAPI/Swagger spec for the MCP server (MCP handles this via tool definitions)
- Authentication/authorization for the MCP server (out of scope for personal knowledge management)
- Multi-tenant support (domain is personal, single-user)
- Real Neo4j integration tests (tests mock the driver)
- CI/CD pipeline configuration
- Performance benchmarking
- Document upload via file (only content string for now)
- Streaming responses for MCP tools

## Further Notes

- The domain is **personal knowledge management** — the user owns everything. The "documents → schemas → graph" pipeline is the core domain model.
- Schemas are **predefined YAML** (not dynamic/LLM-generated). The LLM's role is to *pick* the right schema, not *invent* one.
- The MCP server is the **product**. The Google ADK agent is a **consumer** of this product (separate service).
- Ollama runs on an **external server** (`paulcab-ms-7d75:11434`). The Docker container only needs MCP server + Neo4j.
- The `RateLimitedOllamaLLM` class is a real concern (Ollama has rate limits). It should be in its own module for testing.
- The Cypher query in `graph_search` is complex and should be a module constant for reviewability.
- `pyproject.toml` has `fastmcp>=4.0.0` AND `fastmcp==4.1.6` — this is a conflict that needs fixing.
- The package name `rag_agent` doesn't match the repo name `simple-rag`. Rename to `simple_rag`.
- No `README.md` exists — should be created as part of this refactor.
