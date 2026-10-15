"""SQLite + sqlite-vec vector store with cosine similarity search.

Replaces the previous per-vault `.vectors.json` flat-file store. Rationale
(see commit history and brain_mcp_json_bug_analysis.html for the full
incident writeup this replaces):

  - The flat-JSON store required loading and json-parsing the ENTIRE index
    into Python memory for every single search, and rewriting the entire
    file for every single write (upsert/remove_page). At ~3000 chunks /
    92MB this triggered a real production OOM that crashed the whole VM.
  - Concurrent writers (a live brain_compile_tool run + an operator-
    triggered index_vault.py rebuild) required hand-rolled fcntl.flock()
    locking to avoid corrupting the file — SQLite gives this for free via
    its own file-level locking and WAL mode.
  - A single interrupted write (process kill, deploy, OOM) could leave the
    file permanently truncated/corrupt with no graceful recovery path
    short of a full re-embed from source.

SQLite + the sqlite-vec extension (vec0 virtual table) gives:
  - On-disk storage, not RAM-resident — rows are read from disk as needed
    per query instead of the whole index being parsed into memory first.
  - WAL mode + normal SQLite transactions for safe concurrent writers,
    replacing the hand-rolled flock()/temp-file/os.replace() dance.
  - A real (if still brute-force-under-the-hood-at-this-scale) ANN-style
    KNN query via `WHERE embedding MATCH ? AND k = ?`, with cosine
    distance support and partition-key filtering for the `scope` filter.

Each vault still owns its own file: `.vectors.sqlite3` next to the old
`.vectors.json` (which migrate_from_json() reads once and can then be
deleted/archived).
"""

from __future__ import annotations

import sqlite3
import struct
import threading
from pathlib import Path
from typing import Any, Iterator

import sqlite_vec

from src.vaults import Vault

# One connection per (vault path) per thread — sqlite3 connections are not
# thread-safe to share, and the MCP server may field concurrent requests.
_local = threading.local()


def _embedding_dim(sample: list[float] | None = None) -> int:
    # The vault's embedding model (Azure/OpenAI-compatible) is fixed at
    # 1536 dims (text-embedding-3-small-equivalent) — see embed.py. Kept as
    # a function (not a bare constant) so a future dimension change only
    # needs to update this one place, and so tests can pass an explicit
    # sample to infer dimension instead of hardcoding it twice.
    if sample is not None:
        return len(sample)
    return 1536


def _db_path(vault: Vault) -> Path:
    return vault.path / ".vectors.sqlite3"


def _connect(vault: Vault, dim: int | None = None) -> sqlite3.Connection:
    """Open (or reuse, per-thread) the connection for this vault's DB file.

    Creates the schema on first connect if the file is new/empty. WAL mode
    lets readers (search) and a writer (upsert/remove_page) proceed
    concurrently without blocking each other, which is the common case here
    (a live compile embedding one page while another request searches).
    """
    cache_key = str(vault.path)
    cache = getattr(_local, "conns", None)
    if cache is None:
        cache = _local.conns = {}
    conn = cache.get(cache_key)
    if conn is not None:
        return conn

    db_path = _db_path(vault)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")

    _ensure_schema(conn, dim or _embedding_dim())
    cache[cache_key] = conn
    return conn


def _ensure_schema(conn: sqlite3.Connection, dim: int) -> None:
    conn.execute(
        f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
            embedding float[{dim}] distance_metric=cosine,
            domain TEXT partition key,
            page_slug TEXT,
            section TEXT,
            content TEXT,
            tags TEXT
        )
        """
    )
    conn.commit()


def _pack(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def chunk_content(content: str, page_slug: str, tags: list[str], domain: str) -> list[dict[str, Any]]:
    """Split page content into chunks on H2 headings, then by paragraph if too long.

    Unchanged from the JSON-store version — chunking logic is storage-agnostic.
    """
    import re

    from src.config import MAX_CHUNK_WORDS

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

    A single SQLite transaction does what the JSON store needed
    fcntl.flock() + a full read-modify-write-the-whole-file cycle for:
    SQLite's own file locking serializes this against any other writer on
    the same DB file, and a crash mid-transaction rolls back cleanly
    instead of leaving a half-written file.
    """
    conn = _connect(vault, dim=len(embeddings[0]) if embeddings else None)
    with conn:
        conn.execute("DELETE FROM vec_chunks WHERE page_slug = ?", (page_slug,))
        for chunk, embedding in zip(chunks, embeddings):
            conn.execute(
                "INSERT INTO vec_chunks(embedding, domain, page_slug, section, content, tags) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    _pack(embedding),
                    chunk["domain"],
                    chunk["page_slug"],
                    chunk.get("section", ""),
                    chunk["content"],
                    ",".join(chunk.get("tags", [])),
                ),
            )


def search(
    vault: Vault,
    query_embedding: list[float],
    scope: str = "all",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return top-k chunks sorted by cosine similarity (as a 0..1 score,
    matching the previous JSON-store's convention: 1.0 = identical).

    sqlite-vec's cosine distance_metric returns a distance in [0, 2]
    (0 = identical, 2 = opposite); converted back to the old
    1 - cosine_distance/... convention isn't quite right either, so we
    convert distance -> similarity the same way the old code computed it:
    similarity = 1 - distance/2 for cosine distance as returned by vec0.
    """
    conn = _connect(vault, dim=len(query_embedding))
    q = _pack(query_embedding)

    if scope != "all":
        rows = conn.execute(
            "SELECT page_slug, content, section, tags, domain, distance "
            "FROM vec_chunks WHERE embedding MATCH ? AND k = ? AND domain = ? "
            "ORDER BY distance",
            (q, limit, scope),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT page_slug, content, section, tags, domain, distance "
            "FROM vec_chunks WHERE embedding MATCH ? AND k = ? "
            "ORDER BY distance",
            (q, limit),
        ).fetchall()

    results = []
    for page_slug, content, section, tags, domain, distance in rows:
        score = 1.0 - (distance / 2.0)
        results.append(
            {
                "page_slug": page_slug,
                "content": content,
                "section": section,
                "tags": [t for t in tags.split(",") if t],
                "domain": domain,
                "score": score,
            }
        )
    return results


def remove_page(vault: Vault, page_slug: str) -> None:
    conn = _connect(vault)
    with conn:
        conn.execute("DELETE FROM vec_chunks WHERE page_slug = ?", (page_slug,))


def count(vault: Vault) -> int:
    """Total chunk count — used by health checks / migration verification."""
    conn = _connect(vault)
    return conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]


def migrate_from_json(vault: Vault, json_path: Path | None = None) -> int:
    """One-time migration: read the legacy `.vectors.json` and bulk-insert
    every chunk into the new SQLite store. Returns the number of chunks
    migrated. Safe to re-run (clears the destination table first).

    Does NOT delete the source JSON file — caller decides whether/when to
    archive it, so a migration can always be verified side-by-side before
    the old file is removed.
    """
    import json as json_module

    path = json_path or (vault.path / ".vectors.json")
    if not path.exists():
        return 0
    with open(path, encoding="utf-8") as f:
        store = json_module.load(f)
    chunks = store.get("chunks", [])
    if not chunks:
        return 0

    dim = len(chunks[0]["embedding"])
    conn = _connect(vault, dim=dim)
    with conn:
        conn.execute("DELETE FROM vec_chunks")
        for chunk in chunks:
            conn.execute(
                "INSERT INTO vec_chunks(embedding, domain, page_slug, section, content, tags) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    _pack(chunk["embedding"]),
                    chunk.get("domain", ""),
                    chunk["page_slug"],
                    chunk.get("section", ""),
                    chunk.get("content", ""),
                    ",".join(chunk.get("tags", [])),
                ),
            )
    return len(chunks)
