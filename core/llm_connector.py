"""LLM connector — supports OpenAI and Anthropic providers."""
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMConnector:
    """Thin wrapper around LLM providers (OpenAI / Anthropic)."""

    def __init__(self, provider: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> None:
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai")
        self.config: Dict[str, Any] = config or {}
        self._client: Any = None
        self._setup()

    def _setup(self) -> None:
        if self.provider == "openai":
            try:
                import openai  # type: ignore
                api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
                self._client = openai.AsyncOpenAI(api_key=api_key)
            except ImportError:
                logger.warning("openai package not installed.")
        elif self.provider == "anthropic":
            try:
                import anthropic  # type: ignore
                api_key = self.config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
                self._client = anthropic.AsyncAnthropic(api_key=api_key)
            except ImportError:
                logger.warning("anthropic package not installed.")
        else:
            logger.warning("Unknown LLM provider: %s", self.provider)

    async def complete(self, prompt: str, max_tokens: int = 512) -> str:
        """Single-turn text completion."""
        return await self.chat(
            [{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        model: Optional[str] = None,
    ) -> str:
        """Multi-turn chat completion."""
        if self._client is None:
            return "[LLM not configured]"

        if self.provider == "openai":
            return await self._openai_chat(messages, system_prompt, max_tokens, model)
        if self.provider == "anthropic":
            return await self._anthropic_chat(messages, system_prompt, max_tokens, model)
        return "[Unsupported provider]"

    async def _openai_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        max_tokens: int,
        model: Optional[str],
    ) -> str:
        payload: List[Dict[str, str]] = []
        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})
        payload.extend(messages)
        response = await self._client.chat.completions.create(
            model=model or self.config.get("model", "gpt-4o-mini"),
            messages=payload,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def _anthropic_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        max_tokens: int,
        model: Optional[str],
    ) -> str:
        kwargs: Dict[str, Any] = {
            "model": model or self.config.get("model", "claude-3-haiku-20240307"),
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        response = await self._client.messages.create(**kwargs)
        return response.content[0].text if response.content else ""
