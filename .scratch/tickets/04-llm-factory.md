# 04: LLM factory — provider-agnostic factory + rate limiter

**What to build:** `llm/factory.py` returns the correct LLM/embedder instance based on `ProviderConfig`. `llm/rate_limiter.py` contains `RateLimitedOllamaLLM`.

**Blocked by:** 01 (Prefactoring — rename package to simple_rag and fix pyproject.toml)

**Status:** ready-for-agent

- [ ] `llm/factory.py` with `_get_llm() -> OpenAILLM` and `_get_embedder() -> OpenAIEmbeddings`
- [ ] `_get_llm()` returns OpenAILLM for `openai` provider, RateLimitedOllamaLLM for `ollama` provider
- [ ] `_get_embedder()` returns OpenAIEmbeddings for `openai` provider, OpenAIEmbeddings (with ollama base_url) for `ollama` provider
- [ ] `llm/rate_limiter.py` contains `RateLimitedOllamaLLM` class (sync semaphore + async semaphore)
- [ ] `tests/test_factory.py` covers: OpenAI provider selection, Ollama provider selection, invalid provider raises ValueError
- [ ] `tests/test_rate_limiter.py` covers: rate limiting behavior (concurrent call count)

---

**Notes:** The LLM factory is the seam between config and infrastructure. It should return the correct instance based on `ProviderConfig.llm_provider`. No provider branching in tool modules. `RateLimitedOllamaLLM` is a real concern (Ollama has rate limits) and should be testable in isolation.
