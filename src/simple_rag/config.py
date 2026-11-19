"""Configuration management for simple_rag MCP server.

Config-driven provider selection (OpenAI or Ollama) via environment variables.
No code-level provider branching in tool modules.
"""

import os
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

# Load environment variables once at module import
load_dotenv()


# ---------------------------------------------------------------------------
# Config dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Neo4jConfig:
    """Configuration for Neo4j connection."""

    uri: str = field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    database: str = field(default_factory=lambda: os.getenv("NEO4J_DATABASE", "neo4j"))
    username: str = field(default_factory=lambda: os.getenv("NEO4J_USERNAME", "neo4j"))
    password: str = field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", "password"))
    auth_token: str = field(default_factory=lambda: os.getenv("NEO4J_AUTH", "neo4j/password"))

    # Connection pooling
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_acquisition_timeout: int = 60

    @property
    def auth(self) -> tuple[str, str]:
        """Return authentication tuple."""
        return (self.username, self.password)

    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        """Create configuration from environment variables."""
        return cls()


@dataclass
class ProviderConfig:
    """Unified provider configuration for LLM and embedding.

    Replaces the split OllamaConfig / RAGConfig. The provider is selected
    via ``LLM_PROVIDER`` and ``EMBEDDING_PROVIDER`` env vars (``"openai"``
    or ``"ollama"``).
    """

    # --- LLM settings ---
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "ollama"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "mdq100/qwen3.5-coder:35b"))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "http://paulcab-ms-7d75:11434"))
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", "change_me"))
    llm_max_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "4096")))
    llm_temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.0")))

    # --- Embedding settings ---
    embedding_provider: str = field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "ollama"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "qwen3-embedding-cpu"))
    embedding_base_url: str = field(default_factory=lambda: os.getenv("EMBEDDING_BASE_URL", "http://paulcab-ms-7d75:11434"))
    embedding_api_key: str = field(default_factory=lambda: os.getenv("EMBEDDING_API_KEY", "change_me"))
    embedding_dimension: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSION", "2560")))

    # --- Provider-specific fields ---
    openai_base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://paulcab-ms-7d75:11434"))
    ollama_api_key: str = field(default_factory=lambda: os.getenv("OLLAMA_API_KEY", "change_me"))
    ollama_max_concurrency: int = field(default_factory=lambda: int(os.getenv("OLLAMA_MAX_CONCURRENCY", "1")))
    ollama_num_ctx: int = field(default_factory=lambda: int(os.getenv("OLLAMA_CTX", "32768")))
    ollama_num_keep_alive: str = field(default_factory=lambda: os.getenv("OLLAMA_NUM_KEEP_ALIVE", "30m"))

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        """Create provider configuration from environment variables."""
        return cls()

    def is_openai(self) -> bool:
        """Return True if the LLM provider is OpenAI."""
        return self.llm_provider == "openai"

    def is_ollama(self) -> bool:
        """Return True if the LLM provider is Ollama."""
        return self.llm_provider == "ollama"


@dataclass
class MCPConfig:
    """Configuration for MCP server."""

    host: str = field(default_factory=lambda: os.getenv("MCP_SERVER_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("MCP_SERVER_PORT", "8000")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Server settings
    server_name: str = field(default_factory=lambda: "simple-rag MCP Server")
    server_description: str = field(default_factory=lambda: "MCP server for personal knowledge management with Neo4j vector store")

    # Connection settings
    max_connections: int = field(default_factory=lambda: int(os.getenv("MCP_MAX_CONNECTIONS", "100")))
    keep_alive_timeout: int = field(default_factory=lambda: int(os.getenv("MCP_KEEP_ALIVE_TIMEOUT", "60")))

    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Create configuration from environment variables."""
        return cls()


@dataclass
class AppConfig:
    """Main application configuration."""

    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig.from_env)
    provider: ProviderConfig = field(default_factory=ProviderConfig.from_env)
    mcp: MCPConfig = field(default_factory=MCPConfig.from_env)

    # Application settings
    app_name: str = "simple-rag"
    app_version: str = "0.1.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create full application configuration."""
        return cls()

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Convert configuration to dictionary for health/logging."""
        return {
            "neo4j": {
                "uri": self.neo4j.uri,
                "database": self.neo4j.database,
                "username": self.neo4j.username,
                "max_connection_pool_size": self.neo4j.max_connection_pool_size,
            },
            "provider": {
                "llm_provider": self.provider.llm_provider,
                "llm_model": self.provider.llm_model,
                "embedding_provider": self.provider.embedding_provider,
                "embedding_model": self.provider.embedding_model,
                "embedding_dimension": self.provider.embedding_dimension,
            },
            "mcp": {
                "host": self.mcp.host,
                "port": self.mcp.port,
                "log_level": self.mcp.log_level,
            },
            "application": {
                "name": self.app_name,
                "version": self.app_version,
                "debug": self.debug,
            },
        }
