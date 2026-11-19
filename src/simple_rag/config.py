"""Configuration management for RAG Agent."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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
    def auth(self) -> tuple:
        """Return authentication tuple."""
        return (self.username, self.password)
    
    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        """Create configuration from environment variables."""
        return cls()


@dataclass
class OllamaConfig:
    """Configuration for Ollama integration."""
    
    host: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://paulcab-ms-7d75:11434"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "qwen3-embedding-cpu"))
    chat_model: str = field(default_factory=lambda: os.getenv("CHAT_MODEL", "mdq100/qwen3.5-coder:35b"))
    embedding_dimension: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSION", "2560")))
    
    # Ollama settings
    timeout: int = field(default_factory=lambda: int(os.getenv("OLLAMA_TIMEOUT", "300")))
    num_keep_alive: str = field(default_factory=lambda: os.getenv("OLLAMA_NUM_KEEP_ALIVE", "30m"))

    api_key: str = field(default_factory=lambda: os.getenv("OLLAMA_API_KEY", "change_me"))
    max_concurrency: int = field(default_factory=lambda: int(os.getenv("OLLAMA_MAX_CONCURRENCY", 1)))
    num_ctx: int = field(default_factory=lambda: int(os.getenv("OLLAMA_CTX", 32768)))
    
    @classmethod
    def from_env(cls) -> "OllamaConfig":
        """Create configuration from environment variables."""
        return cls()


@dataclass
class RAGConfig:
    """Configuration for RAG operations."""
    
    # Chunking settings
    chunk_size: int = field(default_factory=lambda: int(os.getenv("RAG_CHUNK_SIZE", "500")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("RAG_CHUNK_OVERLAP", "50")))
    
    # Search settings
    min_relevance_score: float = field(default_factory=lambda: float(os.getenv("RAG_MIN_RELEVANCE_SCORE", "0.7")))
    max_search_results: int = field(default_factory=lambda: int(os.getenv("RAG_MAX_SEARCH_RESULTS", "5")))
    
    # Embedding settings
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "nomic-embed-text"))
    embedding_dimension: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSION", "768")))
    
    # Processing settings
    process_batch_size: int = field(default_factory=lambda: int(os.getenv("RAG_PROCESS_BATCH_SIZE", "100")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("RAG_MAX_RETRIES", "3")))
    retry_delay_seconds: float = field(default_factory=lambda: float(os.getenv("RAG_RETRY_DELAY", "1.0")))
    
    @classmethod
    def from_env(cls) -> "RAGConfig":
        """Create configuration from environment variables."""
        return cls()


@dataclass
class MCPConfig:
    """Configuration for MCP server."""
    
    host: str = field(default_factory=lambda: os.getenv("MCP_SERVER_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("MCP_SERVER_PORT", "8000")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    
    # Server settings
    server_name: str = field(default_factory=lambda: "RAG Agent MCP Server")
    server_description: str = field(default_factory=lambda: "MCP server for RAG operations with Neo4j vector store")
    
    # Connection settings
    max_connections: int = field(default_factory=lambda: int(os.getenv("MCP_MAX_CONNECTIONS", "100")))
    keep_alive_timeout: int = field(default_factory=lambda: int(os.getenv("MCP_KEEP_ALIVE_TIMEOUT", "60")))
    
    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Create configuration from environment variables."""
        return cls()


@dataclass
class ADKConfig:
    """Configuration for Google ADK agent."""
    
    model: str = field(default_factory=lambda: os.getenv("ADK_MODEL", "gemini-1.5-pro"))
    system_prompt: Optional[str] = field(default_factory=lambda: os.getenv("ADK_SYSTEM_PROMPT"))
    system_prompt_file: Optional[str] = field(default_factory=lambda: os.getenv("ADK_SYSTEM_PROMPT_FILE"))
    
    # Agent settings
    max_turns: int = field(default_factory=lambda: int(os.getenv("ADK_MAX_TURNS", "10")))
    temperature: float = field(default_factory=lambda: float(os.getenv("ADK_TEMPERATURE", "0.7")))
    top_p: float = field(default_factory=lambda: float(os.getenv("ADK_TOP_P", "0.95")))
    
    # Conversation settings
    conversation_history_length: int = field(default_factory=lambda: int(os.getenv("ADK_HISTORY_LENGTH", "50")))
    max_tokens_per_turn: int = field(default_factory=lambda: int(os.getenv("ADK_MAX_TOKENS", "4096")))
    
    @classmethod
    def from_env(cls) -> "ADKConfig":
        """Create configuration from environment variables."""
        return cls()


@dataclass
class AppConfig:
    """Main application configuration."""
    
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig.from_env)
    ollama: OllamaConfig = field(default_factory=OllamaConfig.from_env)
    rag: RAGConfig = field(default_factory=RAGConfig.from_env)
    mcp: MCPConfig = field(default_factory=MCPConfig.from_env)
    adk: ADKConfig = field(default_factory=ADKConfig.from_env)
    
    # Application settings
    app_name: str = "RAG Agent"
    app_version: str = "0.1.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create full application configuration."""
        return cls()
    
    def to_dict(self) -> Dict[str, Dict]:
        """Convert configuration to dictionary."""
        return {
            "neo4j": {
                "uri": self.neo4j.uri,
                "database": self.neo4j.database,
                "username": self.neo4j.username,
                "max_connection_pool_size": self.neo4j.max_connection_pool_size
            },
            "ollama": {
                "base_url": self.ollama.base_url,
                "embedding_model": self.ollama.embedding_model,
                "chat_model": self.ollama.chat_model,
                "embedding_dimension": self.ollama.embedding_dimension
            },
            "rag": {
                "chunk_size": self.rag.chunk_size,
                "chunk_overlap": self.rag.chunk_overlap,
                "min_relevance_score": self.rag.min_relevance_score,
                "max_search_results": self.rag.max_search_results,
                "embedding_model": self.rag.embedding_model
            },
            "mcp": {
                "host": self.mcp.host,
                "port": self.mcp.port,
                "log_level": self.mcp.log_level
            },
            "adk": {
                "model": self.adk.model,
                "max_turns": self.adk.max_turns,
                "temperature": self.adk.temperature
            },
            "application": {
                "name": self.app_name,
                "version": self.app_version,
                "debug": self.debug
            }
        }
