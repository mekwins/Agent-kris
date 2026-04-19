"""Search orchestration — semantic, keyword, and hybrid."""

from __future__ import annotations

from src import embed as embedder
from src import vector_store, vault


async def semantic_search(query: str, scope: str = "all", limit: int = 10) -> dict:
    query_vec = await embedder.embed(query)
    chunks = [{**c, "match_type": "semantic"} for c in vector_store.search(query_vec, scope=scope, limit=limit)]
    return {"chunks": chunks, "pages": _pages_for_chunks(chunks)}


def keyword_search(query: str, scope: str = "all", limit: int = 10) -> dict:
    chunks = vault.keyword_search(query, scope=scope, limit=limit)
    return {"chunks": chunks, "pages": _pages_for_chunks(chunks)}


async def hybrid_search(query: str, scope: str = "all", limit: int = 10) -> dict:
    query_vec = await embedder.embed(query)
    semantic_chunks = vector_store.search(query_vec, scope=scope, limit=limit)
    keyword_chunks = vault.keyword_search(query, scope=scope, limit=limit)

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
    return {"chunks": merged, "pages": _pages_for_chunks(merged)}


def _pages_for_chunks(chunks: list[dict]) -> list[dict]:
    seen: set[str] = set()
    pages = []
    for chunk in chunks:
        slug = chunk["page_slug"]
        if slug not in seen:
            seen.add(slug)
            page = vault.read_page(f"{slug}.md")
            if page:
                pages.append(page)
    return pages
