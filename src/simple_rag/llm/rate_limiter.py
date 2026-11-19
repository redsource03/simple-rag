"""Rate-limited Ollama LLM wrapper.

Provides ``RateLimitedOllamaLLM``, a subclass of ``neo4j_graphrag.llm.OpenAILLM``
that caps concurrent sync and async requests to prevent Ollama rate-limit errors.
"""

import asyncio
import threading
from typing import Any, Optional

from neo4j_graphrag.llm import OpenAILLM


class RateLimitedOllamaLLM(OpenAILLM):
    """OllamaLLM subclass that caps concurrent sync and async requests."""

    def __init__(
        self,
        model_name: str,
        max_concurrent: int = 1,
        model_params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            model_name=model_name,
            model_params=model_params,
            **kwargs,
        )
        self._max_concurrent = max_concurrent
        self._async_sem: Optional[asyncio.Semaphore] = None
        self._sync_sem = threading.Semaphore(max_concurrent)

    def _get_async_semaphore(self) -> asyncio.Semaphore:
        """Lazily instantiate the async semaphore inside the active event loop."""
        if self._async_sem is None:
            self._async_sem = asyncio.Semaphore(self._max_concurrent)
        return self._async_sem

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        """Sync invoke with semaphore-based concurrency limiting."""
        with self._sync_sem:
            return super().invoke(*args, **kwargs)

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
        """Async invoke with semaphore-based concurrency limiting."""
        async with self._get_async_semaphore():
            return await super().ainvoke(*args, **kwargs)
