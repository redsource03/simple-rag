"""Provider-agnostic LLM and embedder factory.

Returns the correct LLM/embedder instance based on ``ProviderConfig``.
No provider branching in tool modules — tools receive a configured instance.
"""

from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM

from simple_rag.config import ProviderConfig
from simple_rag.llm.rate_limiter import RateLimitedOllamaLLM


def _get_llm() -> OpenAILLM:
    """Return the LLM instance based on ProviderConfig.llm_provider.

    Returns:
        OpenAILLM for 'openai' provider, RateLimitedOllamaLLM for 'ollama' provider.

    Raises:
        ValueError: If the provider is not recognized.
    """
    provider_config = ProviderConfig.from_env()

    if provider_config.llm_provider == "openai":
        return OpenAILLM(
            model_name=provider_config.llm_model,
            base_url=provider_config.openai_base_url or provider_config.llm_base_url,
            api_key=provider_config.openai_api_key or provider_config.llm_api_key,
            model_params={
                "temperature": provider_config.llm_temperature,
                "max_tokens": provider_config.llm_max_tokens,
            },
        )

    if provider_config.llm_provider == "ollama":
        return RateLimitedOllamaLLM(
            model_name=provider_config.llm_model,
            max_concurrent=provider_config.ollama_max_concurrency,
            base_url=provider_config.ollama_base_url,
            model_params={
                "temperature": provider_config.llm_temperature,
                "response_format": {"type": "json_object"},
                "reasoning_effort": "low",
                "extra_body": {
                    "options": {
                        "num_ctx": provider_config.ollama_num_ctx,
                    },
                    "keep_alive": provider_config.ollama_num_keep_alive,
                },
            },
            timeout=None,
            api_key=provider_config.ollama_api_key,
        )

    raise ValueError(
        f"Unknown LLM provider '{provider_config.llm_provider}'. "
        f"Supported providers: 'openai', 'ollama'"
    )


def _get_embedder() -> OpenAIEmbeddings:
    """Return the embedder instance based on ProviderConfig.embedding_provider.

    Returns:
        OpenAIEmbeddings configured for the selected provider.

    Raises:
        ValueError: If the provider is not recognized.
    """
    provider_config = ProviderConfig.from_env()

    if provider_config.embedding_provider == "openai":
        return OpenAIEmbeddings(
            model=provider_config.embedding_model,
            base_url=provider_config.openai_base_url or provider_config.embedding_base_url,
            api_key=provider_config.openai_api_key or provider_config.embedding_api_key,
        )

    if provider_config.embedding_provider == "ollama":
        return OpenAIEmbeddings(
            model=provider_config.embedding_model,
            base_url=provider_config.ollama_base_url,
            api_key=provider_config.ollama_api_key,
        )

    raise ValueError(
        f"Unknown embedding provider '{provider_config.embedding_provider}'. "
        f"Supported providers: 'openai', 'ollama'"
    )
