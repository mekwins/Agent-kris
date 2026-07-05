"""Search orchestration — semantic, keyword, and hybrid (per vault)."""

from __future__ import annotations

from src import embed as embedder
from src import vector_store, vault as vault_ops
from src.vaults import Vault


async def semantic_search(vault: Vault, query: str, scope: str = "all", limit: int = 10) -> dict:
    query_vec = await embedder.embed(query)
    chunks = [
        {**c, "match_type": "semantic"}
        for c in vector_store.search(vault, query_vec, scope=scope, limit=limit)
    ]
    return {"chunks": chunks, "pages": _pages_for_chunks(vault, chunks)}


def keyword_search(vault: Vault, query: str, scope: str = "all", limit: int = 10) -> dict:
    chunks = vault_ops.keyword_search(vault, query, scope=scope, limit=limit)
    return {"chunks": chunks, "pages": _pages_for_chunks(vault, chunks)}


async def hybrid_search(vault: Vault, query: str, scope: str = "all", limit: int = 10) -> dict:
    query_vec = await embedder.embed(query)
    semantic_chunks = vector_store.search(vault, query_vec, scope=scope, limit=limit)
    keyword_chunks = vault_ops.keyword_search(vault, query, scope=scope, limit=limit)

    # Merge: semantic chunks first, then keyword-only hits not already present
    seen: set[str] = set()
    merged: list[dict] = []

    for chunk in semantic_chunks:
        key = chunk["page_slug"]
        chunk = {**chunk, "match_type": "semantic"}
        merged.append(chunk)
        seen.add(key)

    for chunk in keyword_chunks:
        if chunk["page_slug"] not in seen:
            merged.append(chunk)
            seen.add(chunk["page_slug"])

    merged = merged[:limit]
    return {"chunks": merged, "pages": _pages_for_chunks(vault, merged)}


def _pages_for_chunks(vault: Vault, chunks: list[dict]) -> list[dict]:
    seen: set[str] = set()
    pages = []
    for chunk in chunks:
        slug = chunk["page_slug"]
        if slug not in seen:
            seen.add(slug)
            page = vault_ops.read_page(vault, f"{slug}.md")
            if page:
                pages.append(page)
    return pages
