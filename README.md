# simple-rag

Agentic RAG application using Google ADK and Neo4j GraphRAG.

## Architecture

The project is organized as a modular MCP server:

```
src/simple_rag/
├── __main__.py          # Entry point (python -m simple_rag)
├── mcp_server.py        # MCP server bootstrap + tool registration
├── config.py            # AppConfig, Neo4jConfig, ProviderConfig dataclasses
├── schema_loader.py     # Load/list predefined schemas from YAML files
├── graph/
│   ├── driver.py        # Neo4j driver singleton + vector index management
│   └── pipeline.py      # SimpleKGPipeline factory (schema-aware)
├── llm/
│   ├── factory.py       # Provider-agnostic LLM/embedder factory
│   └── rate_limiter.py  # RateLimitedOllamaLLM wrapper
└── tools/
    ├── add_document.py  # add_document MCP tool
    ├── search.py        # search MCP tool (vector + graph traversal)
    ├── list_schemas.py  # list_schemas MCP tool
    └── __init__.py
```

## Tools

| Tool | Description |
|------|-------------|
| `add_document` | Add a document to the knowledge graph via SimpleKGPipeline |
| `search` | Semantic vector search with configurable graph traversal hops |
| `list_schemas` | List available predefined knowledge-graph schemas |

## Setup

1. Install dependencies:

```bash
pip install -e .
```

2. Set environment variables (or create a `.env` file):

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
```

3. Run the MCP server:

```bash
python -m simple_rag
```

## Docker Compose

Start Neo4j and the app together:

```bash
docker compose up -d
```

The MCP server will be available at `http://localhost:8000`.

## Schema Directory

Predefined schemas are loaded from `src/simple_rag/schemas/` (YAML files).
Each file defines node types, relationship types, and extraction patterns
for a specific knowledge domain.

## Testing

```bash
python -m pytest tests/ -v
```

## Codebase Design

See `docs/adr/0001-predefined-schemas.md` for the architectural decision
record that explains the predefined schemas approach.

See `GLOSSARY.md` for domain terminology.
