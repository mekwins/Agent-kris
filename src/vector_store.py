"""Per-vault JSON-backed vector store with cosine similarity search.

Each vault owns its own `.vectors.json`, so embeddings never cross vaults.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import re
import uuid
from typing import Any, Iterator

import numpy as np

from src.config import MAX_CHUNK_WORDS
from src.vaults import Vault


@contextlib.contextmanager
def _locked(vault: Vault) -> Iterator[None]:
    """Cross-process exclusive lock around a read-modify-write cycle.

    Two processes can legitimately touch the same vault's vectors file at
    once — e.g. a live brain_compile_tool run (embedding newly-written wiki
    pages one at a time) racing an operator-triggered `index_vault.py` full
    rebuild. Without this lock, both processes read, modify, and os.replace()
    independently; whichever one finishes last silently wins and the other's
    writes are lost — or worse, both temp files can interleave on disk if
    they happen to share a filename, corrupting the result even though each
    individual _save() call is atomic on its own.

    fcntl.flock() blocks until the lock is free, so this serializes the
    upsert/remove_page read-modify-write cycle across every process touching
    this vault, without needing any shared coordination beyond the filesystem.
    """
    lock_path = vault.vectors_path.with_suffix(vault.vectors_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _load(vault: Vault) -> dict[str, Any]:
    """Read the vectors file. Used by read-only callers (search()).

    Degrades a corrupt/truncated file to an empty index (with a logged
    warning) rather than raising — so a broken file turns semantic search
    into "no results" instead of crashing every brain_search_tool call.
    Safe here specifically because search() never writes anything back;
    for read-modify-write callers see `_load_strict`.
    """
    if not vault.vectors_path.exists():
        return {"chunks": []}
    try:
        with open(vault.vectors_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        print(
            f"[vector_store] WARNING: {vault.vectors_path} is corrupt/truncated "
            f"({exc}). Treating as empty index for this search — run "
            f"scripts/index_vault.py to rebuild it.",
            flush=True,
        )
        return {"chunks": []}


def _load_strict(vault: Vault) -> dict[str, Any]:
    """Read the vectors file for a read-modify-write cycle (upsert/remove_page).

    Unlike `_load`, this RAISES on corruption instead of degrading to an
    empty store. upsert()/remove_page() always write back what they read —
    if a corrupt file were silently treated as empty here, every embed call
    would quietly overwrite the (larger, still mostly-good) on-disk store
    with just that one page's chunks, destroying the rest of the index one
    upsert at a time. Failing loudly instead forces a real
    `scripts/index_vault.py` rebuild rather than a slow silent data loss.
    """
    if not vault.vectors_path.exists():
        return {"chunks": []}
    with open(vault.vectors_path, encoding="utf-8") as f:
        return json.load(f)


def _save(vault: Vault, store: dict[str, Any]) -> None:
    """Atomically overwrite the vault's vector store.

    Writes to a per-process-unique temp file in the same directory, then
    os.replace()s it over the real path. os.replace() is atomic on POSIX, so
    a crash/kill/restart mid-write can never leave a half-written,
    permanently-corrupt .vectors.json behind — readers only ever see the old
    complete file or the new complete file, never a partial one.

    The temp filename includes the pid + a random token so that even if this
    is ever called without holding `_locked()` (defense-in-depth only —
    callers should always hold the lock), two concurrent writers can't both
    write through the *same* temp file path and interleave their output.

    (Previously this opened vectors_path directly in "w" mode and wrote into
    it in place — if the process died mid-json.dump(), the file was left
    truncated forever, and every subsequent _load() would fail with the same
    JSONDecodeError at the same byte offset until someone noticed and fully
    reindexed the vault from scratch via scripts/index_vault.py.)
    """
    vault.vectors_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = vault.vectors_path.with_suffix(
        f"{vault.vectors_path.suffix}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp"
    )
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
    """Replace all chunks for a page, then add new ones.

    Holds the cross-process lock for the entire read-modify-write cycle so a
    concurrent upsert/remove_page/rebuild for the same vault can't interleave
    with this one and silently lose data (see `_locked`'s docstring).
    """
    with _locked(vault):
        store = _load_strict(vault)
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
    with _locked(vault):
        store = _load_strict(vault)
        store["chunks"] = [c for c in store["chunks"] if c["page_slug"] != page_slug]
        _save(vault, store)
