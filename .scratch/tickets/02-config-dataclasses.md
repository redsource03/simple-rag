# 02: Config — clean dataclasses and ProviderConfig

**What to build:** Refactor `config.py` into a thin layer of dataclasses with a unified `ProviderConfig` that replaces the split `OllamaConfig`/`RAGConfig`. Remove dead code.

**Blocked by:** 01 (Prefactoring — rename package to simple_rag and fix pyproject.toml)

**Status:** ready-for-agent

- [ ] `RAGConfig` removed (dead code — no code uses it)
- [ ] `ADKConfig` removed (dead code — no code uses it)
- [ ] `OllamaConfig` replaced by `ProviderConfig` dataclass with: `llm_provider`, `llm_model`, `llm_base_url`, `llm_api_key`, `llm_max_tokens`, `llm_temperature`, `embedding_provider`, `embedding_model`, `embedding_base_url`, `embedding_api_key`, `embedding_dimension`, plus provider-specific fields (`openai_base_url`, `openai_api_key`, `ollama_base_url`, `ollama_api_key`, `ollama_max_concurrency`, `ollama_num_ctx`, `ollama_num_keep_alive`)
- [ ] `Neo4jConfig` kept (unchanged, just cleaned up)
- [ ] `MCPConfig` kept (host, port, log_level, server_name, server_description, max_connections, keep_alive_timeout)
- [ ] `AppConfig` composes all above + `app_name`, `app_version`, `debug`
- [ ] `AppConfig.to_dict()` returns serializable dict for health/logging
- [ ] `from_env()` classmethod on each dataclass
- [ ] `load_dotenv()` called once at module import
- [ ] `tests/test_config.py` covers: env var loading, default values, `to_dict()` serialization
- [ ] `tests/test_config.py` covers: `ProviderConfig` OpenAI vs Ollama selection logic

---

**Notes:** `ProviderConfig` is the key new dataclass. It unifies LLM and embedding settings under one config object. The MCP tools will receive a `ProviderConfig` instance and use it to create LLM/embedder instances — no provider branching in tool code.
