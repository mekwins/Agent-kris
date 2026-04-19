"""Embedding via direct HTTP POST — works with any OpenAI-compatible endpoint."""

import httpx
from src.config import EMBEDDING_ENDPOINT, EMBEDDING_API_KEY

_HEADERS = {"api-key": EMBEDDING_API_KEY, "Content-Type": "application/json"}


async def embed(text: str) -> list[float]:
    return (await embed_batch([text]))[0]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    cleaned = [t.replace("\n", " ") for t in texts]
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            EMBEDDING_ENDPOINT,
            headers=_HEADERS,
            json={"input": cleaned},
        )
        response.raise_for_status()
    data = response.json()["data"]
    return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]
