"""simple_rag.llm — Provider-agnostic LLM/embedder factory.

Exports:
    - factory._get_llm()
    - factory._get_embedder()
    - rate_limiter.RateLimitedOllamaLLM
"""

from simple_rag.llm import factory, rate_limiter

__all__ = ["factory", "rate_limiter"]
