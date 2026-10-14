"""Per-vault JSON-backed vector store with cosine similarity search.

Each vault owns its own `.vectors.json`, so embeddings never cross vaults.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import numpy as np

from src.config import MAX_CHUNK_WORDS
from src.vaults import Vault


def _load(vault: Vault) -> dict[str, Any]:
    if not vault.vectors_path.exists():
        return {"chunks": []}
    try:
        with open(vault.vectors_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        # Defense-in-depth: a corrupt/truncated vectors file (e.g. from an old
        # non-atomic write, a full disk, or a copy interrupted mid-transfer)
        # should degrade search to "no semantic results" instead of crashing
        # every call to brain_search_tool / brain_compile_tool. The file itself
        # needs a full `uv run python scripts/index_vault.py --wiki <id>`
        # rebuild to actually restore semantic search for this vault.
        print(
            f"[vector_store] WARNING: {vault.vectors_path} is corrupt/truncated "
            f"({exc}). Treating as empty index — run scripts/index_vault.py to "
            f"rebuild it.",
            flush=True,
        )
        return {"chunks": []}


def _save(vault: Vault, store: dict[str, Any]) -> None:
    """Atomically overwrite the vault's vector store.

    Writes to a temp file in the same directory, then os.replace()s it over
    the real path. os.replace() is atomic on POSIX, so a crash/kill/restart
    mid-write can never leave a half-written, permanently-corrupt
    .vectors.json behind — readers only ever see the old complete file or the
    new complete file, never a partial one.

    (Previously this opened vectors_path directly in "w" mode and wrote into
    it in place — if the process died mid-json.dump(), the file was left
    truncated forever, and every subsequent _load() would fail with the same
    JSONDecodeError at the same byte offset until someone noticed and fully
    reindexed the vault from scratch via scripts/index_vault.py.)
    """
    vault.vectors_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = vault.vectors_path.with_suffix(vault.vectors_path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, vault.vectors_path)


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
