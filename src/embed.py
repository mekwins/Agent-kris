"""Embedding via direct HTTP POST — works with any OpenAI-compatible endpoint."""

import httpx
from src.config import EMBEDDING_ENDPOINT, EMBEDDING_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS

# "api-key" for Azure OpenAI, Bearer for the Nexteer gateway / OpenAI.
_HEADERS = {
    "api-key": EMBEDDING_API_KEY,
    "Authorization": f"Bearer {EMBEDDING_API_KEY}",
    "Content-Type": "application/json",
}
# Model-named endpoints (gateway) need model + dimensions in the body; pinning
# dimensions keeps text-embedding-3-large compatible with the 1536-dim store.
_BODY_EXTRA = {"model": EMBEDDING_MODEL, "dimensions": EMBEDDING_DIMENSIONS} if EMBEDDING_MODEL else {}


async def embed(text: str) -> list[float]:
    return (await embed_batch([text]))[0]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    cleaned = [t.replace("\n", " ") for t in texts]
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            EMBEDDING_ENDPOINT,
            headers=_HEADERS,
            json={"input": cleaned, **_BODY_EXTRA},
        )
        response.raise_for_status()
    data = response.json()["data"]
    return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]
