"""LLM provider: structured extraction + a tool-calling chat model for the agent. Degrades to None without a key."""
import asyncio
import logging
import re
from typing import Protocol, TypeVar

from pydantic import BaseModel

from app.core.config import get_settings

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)
_HINT = re.compile(r"try again in ([\d.]+)\s*(ms|s)", re.I)


def rate_wait(exc: Exception) -> float | None:
    text = str(exc)
    if "429" not in text and "rate_limit" not in text:
        return None
    m = _HINT.search(text)
    return 5.0 if not m else min(float(m.group(1)) / (1000 if m.group(2).lower() == "ms" else 1) + 0.5, 20.0)


class LLMProvider(Protocol):
    available: bool
    chat: object | None

    async def structured(self, schema: type[T], system: str, user: str) -> T: ...
    async def complete(self, system: str, user: str) -> str: ...


class NullLLM:
    available = False
    chat = None

    async def structured(self, schema, system, user):
        raise RuntimeError("LLM not configured")

    async def complete(self, system, user):
        raise RuntimeError("LLM not configured")


class GroqLLM:
    available = True
    _gate = asyncio.Semaphore(2)

    def __init__(self) -> None:
        from langchain_groq import ChatGroq
        s = get_settings()
        self.chat = ChatGroq(model=s.llm_model, api_key=s.groq_api_key, temperature=0, timeout=s.llm_timeout_s, max_retries=2)

    async def _retry(self, fn, attempts: int = 4):
        for i in range(attempts):
            try:
                async with self._gate:
                    return await fn()
            except Exception as e:
                wait = rate_wait(e)
                if wait is None or i == attempts - 1:
                    raise
                await asyncio.sleep(wait)

    async def structured(self, schema, system, user):
        model = self.chat.with_structured_output(schema)
        return await self._retry(lambda: model.ainvoke([("system", system), ("human", user)]))

    async def complete(self, system, user):
        r = await self._retry(lambda: self.chat.ainvoke([("system", system), ("human", user)]))
        return str(r.content).strip()


_llm: LLMProvider | None = None


def get_llm() -> LLMProvider:
    global _llm
    if _llm is None:
        _llm = GroqLLM() if get_settings().groq_api_key else NullLLM()
    return _llm


def set_llm(llm: LLMProvider | None) -> None:
    global _llm
    _llm = llm
