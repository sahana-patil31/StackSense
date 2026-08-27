import hashlib
import json
import urllib.request
import urllib.error
from typing import Any, Iterable

from app.core.config import get_settings


class ProviderError(RuntimeError):
    pass


class EmbeddingProvider:
    dimension = 64

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class LocalHashEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> list[float]:
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("Embedding requires non-empty text")
        values = [0.0] * self.dimension
        for index in range(0, len(text), 3):
            digest = hashlib.sha256(text[index:index + 3].encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:2], "big") % self.dimension
            values[bucket] += 1.0 if digest[2] & 1 else -1.0
        magnitude = sum(value * value for value in values) ** 0.5
        return [round(value / magnitude, 8) for value in values] if magnitude else values


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str, api_key: str, endpoint: str = "https://api.openai.com/v1/embeddings"):
        self.model, self.api_key, self.endpoint = model, api_key, endpoint

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ProviderError("Embedding requires non-empty text")
        payload = json.dumps({"model": self.model, "input": text}).encode()
        request = urllib.request.Request(self.endpoint, payload, {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return list(json.loads(response.read())["data"][0]["embedding"])
        except (urllib.error.URLError, KeyError, IndexError, ValueError) as exc:
            raise ProviderError(f"Embedding provider request failed: {exc}") from exc


class LLMProvider:
    def answer(self, question: str, evidence: Iterable[dict[str, Any]], history: Iterable[dict[str, str]] = ()) -> str:
        raise NotImplementedError


class LocalGroundedLLMProvider(LLMProvider):
    def answer(self, question: str, evidence: Iterable[dict[str, Any]], history: Iterable[dict[str, str]] = ()) -> str:
        items = list(evidence)
        if not items:
            return "Insufficient evidence: I don't have enough evidence in STACKSENSE to determine the answer."
        relevant = [item for item in items if any(word.lower() in item.get("content", "").lower() for word in question.split() if len(word) > 3)] or items[:2]
        claims = []
        for item in relevant[:3]:
            source = item.get("source_type", "source")
            source_id = item.get("source_id") or "unknown"
            claims.append(f"{item['title']}: {item['content'][:400]} [Source: {source}_{source_id}]")
        return "Based on the available evidence: " + " ".join(claims)


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, model: str, api_key: str, endpoint: str = "https://api.openai.com/v1/chat/completions"):
        self.model, self.api_key, self.endpoint = model, api_key, endpoint

    def answer(self, question: str, evidence: Iterable[dict[str, Any]], history: Iterable[dict[str, str]] = ()) -> str:
        items = list(evidence)
        if not self.api_key:
            raise ProviderError("LLM provider requires LLM_API_KEY")
        prompt = "Answer only from this evidence. Say insufficient evidence when it does not support an answer.\n" + "\n".join(item["content"] for item in items)
        messages = [{"role": "system", "content": "You are a grounded software operations assistant."}, *list(history), {"role": "user", "content": f"{prompt}\nQuestion: {question}"}]
        request = urllib.request.Request(self.endpoint, json.dumps({"model": self.model, "messages": messages, "temperature": 0}).encode(), {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read())["choices"][0]["message"]["content"]
        except (urllib.error.URLError, KeyError, IndexError, ValueError) as exc:
            raise ProviderError(f"LLM provider request failed: {exc}") from exc


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider.lower() == "local":
        return LocalHashEmbeddingProvider()
    if not settings.llm_api_key:
        raise ProviderError("Embedding provider requires LLM_API_KEY")
    return OpenAICompatibleEmbeddingProvider(settings.embedding_model, settings.llm_api_key)


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider.lower() == "local":
        return LocalGroundedLLMProvider()
    if not settings.llm_api_key:
        raise ProviderError("LLM provider requires LLM_API_KEY")
    return OpenAICompatibleLLMProvider(settings.llm_model, settings.llm_api_key)
