"""Per-vault JSON-backed vector store with cosine similarity search.

Each vault owns its own `.vectors.json`, so embeddings never cross vaults.
"""

from __future__ import annotations

import json
import re
from typing import Any

import numpy as np

from src.config import MAX_CHUNK_WORDS
from src.vaults import Vault


def _load(vault: Vault) -> dict[str, Any]:
    if not vault.vectors_path.exists():
        return {"chunks": []}
    with open(vault.vectors_path, encoding="utf-8") as f:
        return json.load(f)


def _save(vault: Vault, store: dict[str, Any]) -> None:
    vault.vectors_path.parent.mkdir(parents=True, exist_ok=True)
    with open(vault.vectors_path, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False)


def chunk_content(content: str, page_slug: str, tags: list[str], domain: str) -> list[dict[str, Any]]:
    """Split page content into chunks on H2 headings, then by paragraph if too long."""
    sections = re.split(r"^## ", content, flags=re.MULTILINE)
    chunks = []
    for section in sections:
        if not section.strip():
            continue
        words = section.split()
        if len(words) <= MAX_CHUNK_WORDS:
            chunks.append({"text": section.strip(), "section": section.split("\n")[0].strip()})
        else:
            paragraphs = re.split(r"\n\n+", section)
            current, current_words = [], 0
            for para in paragraphs:
                para_words = len(para.split())
                if current_words + para_words > MAX_CHUNK_WORDS and current:
                    chunks.append({"text": "\n\n".join(current).strip(), "section": ""})
                    current, current_words = [para], para_words
                else:
                    current.append(para)
                    current_words += para_words
            if current:
                chunks.append({"text": "\n\n".join(current).strip(), "section": ""})

    return [
        {"page_slug": page_slug, "content": c["text"], "section": c["section"], "tags": tags, "domain": domain}
        for c in chunks
        if c["text"]
    ]


def upsert(vault: Vault, page_slug: str, chunks: list[dict[str, Any]], embeddings: list[list[float]]) -> None:
    """Replace all chunks for a page, then add new ones."""
    store = _load(vault)
    store["chunks"] = [c for c in store["chunks"] if c["page_slug"] != page_slug]
    for chunk, embedding in zip(chunks, embeddings):
        store["chunks"].append({**chunk, "embedding": embedding})
    _save(vault, store)


def search(
    vault: Vault,
    query_embedding: list[float],
    scope: str = "all",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return top-k chunks sorted by cosine similarity."""
    store = _load(vault)
    candidates = store["chunks"]
    if scope != "all":
        candidates = [c for c in candidates if c.get("domain") == scope]

    if not candidates:
        return []

    q = np.array(query_embedding)
    scored = []
    for chunk in candidates:
        vec = np.array(chunk["embedding"])
        score = float(np.dot(q, vec) / (np.linalg.norm(q) * np.linalg.norm(vec) + 1e-9))
        scored.append({**{k: v for k, v in chunk.items() if k != "embedding"}, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def remove_page(vault: Vault, page_slug: str) -> None:
    store = _load(vault)
    store["chunks"] = [c for c in store["chunks"] if c["page_slug"] != page_slug]
    _save(vault, store)
