"""Vector store — SQLite + sqlite-vec backend.

This module is now a thin compatibility shim over vector_store_sqlite,
which replaced the original flat-JSON `.vectors.json` store. Every caller
(search.py, agent.py, tools/brain_write.py, scripts/index_vault.py)
imports `vector_store` by name, so re-exporting here means none of them
needed to change — only the storage layer underneath did.

See vector_store_sqlite.py's module docstring for the full rationale
(production OOM at ~92MB/2930 chunks on a 512MB machine, hand-rolled
fcntl locking needed for concurrent writers, corruption-on-interrupted-
write risk — all eliminated by moving to a real embedded database).

`_locked` and `_save` are re-exported too: scripts/index_vault.py calls
them directly to do a single bulk atomic write instead of N individual
upserts. For the SQLite backend, "locked" is a no-op context manager
(SQLite's own file locking + WAL already serializes concurrent writers)
and `_save` bulk-replaces the whole vec_chunks table in one transaction.
"""

from __future__ import annotations

import contextlib
from typing import Any, Iterator

from src.vaults import Vault
from src import vector_store_sqlite as _sqlite_store

chunk_content = _sqlite_store.chunk_content
upsert = _sqlite_store.upsert
search = _sqlite_store.search
remove_page = _sqlite_store.remove_page
count = _sqlite_store.count
migrate_from_json = _sqlite_store.migrate_from_json


@contextlib.contextmanager
def _locked(vault: Vault) -> Iterator[None]:
    """No-op for the SQLite backend — kept so scripts/index_vault.py's
    `with vector_store._locked(vault):` call site doesn't need to change.
    SQLite's own file-level locking (plus WAL mode) already serializes
    concurrent writers to the same .vectors.sqlite3 file; the old
    fcntl.flock()-based cross-process lock this replaced was only needed
    because the JSON backend had no locking of its own.
    """
    yield


def _save(vault: Vault, store: dict[str, Any]) -> None:
    """Bulk-replace the entire vector store in one transaction.

    Used by scripts/index_vault.py's full-rebuild path: it chunks+embeds
    every file in memory first, then calls this once with the complete new
    chunk list, instead of one upsert() per file. Mirrors the old JSON
    store's `_save(vault, {"chunks": [...]})` signature so that call site
    needed no changes.
    """
    conn = _sqlite_store._connect(
        vault, dim=len(store["chunks"][0]["embedding"]) if store.get("chunks") else None
    )
    with conn:
        conn.execute("DELETE FROM vec_chunks")
        for chunk in store.get("chunks", []):
            conn.execute(
                "INSERT INTO vec_chunks(embedding, domain, page_slug, section, content, tags) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    _sqlite_store._pack(chunk["embedding"]),
                    chunk.get("domain", ""),
                    chunk["page_slug"],
                    chunk.get("section", ""),
                    chunk.get("content", ""),
                    ",".join(chunk.get("tags", [])),
                ),
            )
