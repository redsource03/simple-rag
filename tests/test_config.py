"""Tests for simple_rag.config module.

Covers:
- Environment variable loading
- Default values
- AppConfig.to_dict() serialization
- ProviderConfig OpenAI vs Ollama selection logic
"""

import os
from simple_rag.config import (
    AppConfig,
    MCPConfig,
    Neo4jConfig,
    ProviderConfig,
)


# ---------------------------------------------------------------------------
# Neo4jConfig
# ---------------------------------------------------------------------------


class TestNeo4jConfig:
    def test_defaults(self) -> None:
        config = Neo4jConfig()
        assert config.uri == "bolt://localhost:7687"
        assert config.database == "neo4j"
        assert config.username == "neo4j"
        assert config.password == "password"
        assert config.auth_token == "neo4j/password"
        assert config.max_connection_lifetime == 3600
        assert config.max_connection_pool_size == 50
        assert config.connection_acquisition_timeout == 60

    def test_auth_property(self) -> None:
        config = Neo4jConfig()
        assert config.auth == ("neo4j", "password")

    def test_from_env_respects_env(self, monkeypatch: "pytest.MonkeyPatch") -> None:
        monkeypatch.setenv("NEO4J_URI", "bolt://test:7687")
        monkeypatch.setenv("NEO4J_DATABASE", "testdb")
        monkeypatch.setenv("NEO4J_USERNAME", "testuser")
        monkeypatch.setenv("NEO4J_PASSWORD", "testpass")
        config = Neo4jConfig.from_env()
        assert config.uri == "bolt://test:7687"
        assert config.database == "testdb"
        assert config.username == "testuser"
        assert config.password == "testpass"


# ---------------------------------------------------------------------------
# ProviderConfig
# ---------------------------------------------------------------------------


class TestProviderConfig:
    def test_defaults_ollama(self, monkeypatch: "pytest.MonkeyPatch") -> None:
        monkeypatch.delenv("OLLAMA_NUM_KEEP_ALIVE", raising=False)
        config = ProviderConfig()
        assert config.llm_provider == "ollama"
        assert config.embedding_provider == "ollama"
        assert config.llm_model == "mdq100/qwen3.5-coder:35b"
        assert config.embedding_model == "qwen3-embedding-cpu"
        assert config.llm_max_tokens == 4096
        assert config.llm_temperature == 0.0
        assert config.embedding_dimension == 2560
        assert config.ollama_max_concurrency == 1
        assert config.ollama_num_ctx == 32768
        assert config.ollama_num_keep_alive == "30m"

    def test_defaults_openai(self, monkeypatch: "pytest.MonkeyPatch") -> None:
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
        monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
        monkeypatch.setenv("EMBEDDING_DIMENSION", "1536")
        config = ProviderConfig.from_env()
        assert config.llm_provider == "openai"
        assert config.embedding_provider == "openai"
        assert config.llm_model == "gpt-4o"
        assert config.embedding_model == "text-embedding-3-small"
        assert config.embedding_dimension == 1536

    def test_is_openai(self) -> None:
        config = ProviderConfig(llm_provider="openai")
        assert config.is_openai() is True
        assert config.is_ollama() is False

    def test_is_ollama(self) -> None:
        config = ProviderConfig(llm_provider="ollama")
        assert config.is_ollama() is True
        assert config.is_openai() is False

    def test_from_env_provider_selection(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
        config = ProviderConfig.from_env()
        assert config.is_openai() is True
        assert config.is_ollama() is False


# ---------------------------------------------------------------------------
# MCPConfig
# ---------------------------------------------------------------------------


class TestMCPConfig:
    def test_defaults(self) -> None:
        config = MCPConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.log_level == "INFO"
        assert config.server_name == "simple-rag MCP Server"
        assert config.server_description == (
            "MCP server for personal knowledge management with Neo4j vector store"
        )
        assert config.max_connections == 100
        assert config.keep_alive_timeout == 60

    def test_from_env_respects_env(self, monkeypatch: "pytest.MonkeyPatch") -> None:
        monkeypatch.setenv("MCP_SERVER_HOST", "127.0.0.1")
        monkeypatch.setenv("MCP_SERVER_PORT", "9000")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        config = MCPConfig.from_env()
        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.log_level == "DEBUG"


# ---------------------------------------------------------------------------
# AppConfig
# ---------------------------------------------------------------------------


class TestAppConfig:
    def test_defaults(self) -> None:
        config = AppConfig()
        assert config.app_name == "simple-rag"
        assert config.app_version == "0.1.0"
        assert config.debug is False

    def test_to_dict(self) -> None:
        config = AppConfig()
        d = config.to_dict()
        assert isinstance(d, dict)
        assert "neo4j" in d
        assert "provider" in d
        assert "mcp" in d
        assert "application" in d
        assert d["application"]["name"] == "simple-rag"
        assert d["application"]["version"] == "0.1.0"
        assert d["provider"]["llm_provider"] == "ollama"
        assert d["provider"]["embedding_provider"] == "ollama"

    def test_to_dict_serializable(self) -> None:
        config = AppConfig()
        d = config.to_dict()
        import json
        json.dumps(d)  # raises if not serializable

    def test_debug_from_env(self, monkeypatch: "pytest.MonkeyPatch") -> None:
        monkeypatch.setenv("DEBUG", "true")
        config = AppConfig.from_env()
        assert config.debug is True

        monkeypatch.setenv("DEBUG", "false")
        config = AppConfig.from_env()
        assert config.debug is False
