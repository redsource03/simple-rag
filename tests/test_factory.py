"""Tests for simple_rag.llm.factory module.

Covers:
- OpenAI provider selection
- Ollama provider selection
- Invalid provider raises ValueError
"""

import asyncio
import threading
from unittest.mock import MagicMock, patch

import pytest

from simple_rag.config import ProviderConfig
from simple_rag.llm import factory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_provider(llm_provider: str = "openai", llm_model: str = "gpt-4", embedding_provider: str = "openai") -> MagicMock:
    """Create a mock ProviderConfig with realistic defaults.

    Uses a plain MagicMock (no spec) so attribute access returns the
    explicitly set values rather than nested Mocks.
    """
    mock = MagicMock()
    mock.llm_provider = llm_provider
    mock.llm_model = llm_model
    mock.llm_base_url = ""
    mock.llm_api_key = "test-key"
    mock.llm_max_tokens = 4096
    mock.llm_temperature = 0.0
    mock.embedding_provider = embedding_provider
    mock.embedding_model = "text-embedding-3-large"
    mock.embedding_base_url = ""
    mock.embedding_api_key = "test-key"
    mock.embedding_dimension = 1536
    mock.openai_base_url = ""
    mock.openai_api_key = "test-key"
    mock.ollama_base_url = "http://localhost:11434"
    mock.ollama_api_key = "test-key"
    mock.ollama_max_concurrency = 1
    mock.ollama_num_ctx = 32768
    mock.ollama_num_keep_alive = "30m"
    return mock


# ---------------------------------------------------------------------------
# _get_llm
# ---------------------------------------------------------------------------


class TestGetLLM:
    def test_get_llm_openai_returns_OpenAILLM(self) -> None:
        mock_provider = _make_mock_provider(llm_provider="openai")
        with patch.object(ProviderConfig, "from_env", return_value=mock_provider):
            llm = factory._get_llm()
        assert llm is not None
        assert hasattr(llm, "invoke")
        assert hasattr(llm, "ainvoke")

    def test_get_llm_ollama_returns_RateLimitedOllamaLLM(self) -> None:
        mock_provider = _make_mock_provider(llm_provider="ollama", llm_model="qwen3.5-coder:35b")
        with patch.object(ProviderConfig, "from_env", return_value=mock_provider):
            llm = factory._get_llm()
        assert llm is not None
        assert hasattr(llm, "invoke")
        assert hasattr(llm, "ainvoke")
        # Verify it has semaphore-based concurrency control
        assert hasattr(llm, "_sync_sem")
        assert isinstance(llm._sync_sem, threading.Semaphore)
        assert hasattr(llm, "_async_sem")

    def test_get_llm_invalid_provider_raises(self) -> None:
        mock_provider = _make_mock_provider(llm_provider="invalid")
        with patch.object(ProviderConfig, "from_env", return_value=mock_provider):
            with pytest.raises(ValueError):
                factory._get_llm()

    def test_get_llm_uses_correct_model(self) -> None:
        mock_provider = _make_mock_provider(llm_provider="openai", llm_model="gpt-4.1-mini")
        with patch.object(ProviderConfig, "from_env", return_value=mock_provider):
            llm = factory._get_llm()
        assert llm.model_name == "gpt-4.1-mini"


# ---------------------------------------------------------------------------
# _get_embedder
# ---------------------------------------------------------------------------


class TestGetEmbedder:
    def test_get_embedder_openai_returns_OpenAIEmbeddings(self) -> None:
        mock_provider = _make_mock_provider(embedding_provider="openai")
        with patch.object(ProviderConfig, "from_env", return_value=mock_provider):
            with patch("simple_rag.llm.factory.OpenAIEmbeddings") as MockEmbeddings:
                embedder = factory._get_embedder()
        MockEmbeddings.assert_called_once()
        call_kwargs = MockEmbeddings.call_args.kwargs
        assert call_kwargs["model"] == "text-embedding-3-large"

    def test_get_embedder_ollama_returns_OpenAIEmbeddings_with_base_url(self) -> None:
        mock_provider = _make_mock_provider(embedding_provider="ollama")
        mock_provider.ollama_base_url = "http://custom-ollama:11434"
        with patch.object(ProviderConfig, "from_env", return_value=mock_provider):
            with patch("simple_rag.llm.factory.OpenAIEmbeddings") as MockEmbeddings:
                embedder = factory._get_embedder()
        MockEmbeddings.assert_called_once()
        call_kwargs = MockEmbeddings.call_args.kwargs
        assert call_kwargs["model"] == "text-embedding-3-large"
        assert call_kwargs["base_url"] == "http://custom-ollama:11434"

    def test_get_embedder_invalid_provider_raises(self) -> None:
        mock_provider = _make_mock_provider(embedding_provider="invalid")
        with patch.object(ProviderConfig, "from_env", return_value=mock_provider):
            with pytest.raises(ValueError):
                factory._get_embedder()
