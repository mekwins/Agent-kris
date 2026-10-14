"""Bootstrap or rebuild the vector index for one or all vaults.

Usage:
    uv run python scripts/index_vault.py              # index every vault
    uv run python scripts/index_vault.py --wiki work  # index a single vault
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import embed as embedder, vector_store, vault as vault_ops
from src.vaults import Vault, available_ids, get_vault


async def index_vault(vault_id: str) -> None:
    """Rebuild a vault's entire vector index from wiki/ + sources/ markdown.

    Builds the new store ENTIRELY in memory, then writes it with a single
    locked _save() call at the very end — not via hundreds of individual
    upsert() calls against a destructively-unlinked file. This matters for
    two reasons:

    1. Safety: the old approach called vault.vectors_path.unlink() up front,
       then rebuilt file-by-file via upsert(). A concurrent live process
       (e.g. brain_compile_tool embedding a newly-compiled page) could run
       its own upsert() in that same window — before this fix, both that
       live upsert() and this rebuild's upsert() calls raced to write the
       same shared ".tmp" filename with no locking, interleaving their
       output and corrupting the file (this is exactly how a REAL
       corruption was reproduced in production during initial testing of
       this fix). Building one complete in-memory store and writing it with
       one locked call means other processes always see either the
       complete pre-rebuild file or the complete post-rebuild file.
    2. Speed: one atomic write instead of N (577+) separate lock/write/fsync/
       rename cycles.
    """
    vault = get_vault(vault_id)
    dirs = [vault.path / "wiki", vault.path / "sources"]
    md_files = [f for d in dirs if d.exists() for f in d.rglob("*.md")]

    print(f"\n=== Vault '{vault.id}' ({vault.path}) ===")
    if not md_files:
        print("  No markdown files found in wiki/ or sources/")
        return

    print(f"  Indexing {len(md_files)} files...")
    new_chunks: list[dict] = []
    total_chunks = 0
    for i, md_file in enumerate(md_files, 1):
        rel = str(md_file.relative_to(vault.path))
        page = vault_ops.read_page(vault, rel)
        if not page:
            print(f"    [{i}/{len(md_files)}] {rel} — skipped (unreadable)")
            continue
        page_slug = rel.removesuffix(".md")
        chunks = vector_store.chunk_content(
            page["content"],
            page_slug=page_slug,
            tags=page["tags"],
            domain=page["domain"],
        )
        if chunks:
            texts = [c["content"] for c in chunks]
            embeddings = await embedder.embed_batch(texts)
            for chunk, embedding in zip(chunks, embeddings):
                new_chunks.append({**chunk, "embedding": embedding})
        total_chunks += len(chunks)
        print(f"    [{i}/{len(md_files)}] {rel} — {len(chunks)} chunks")

    # Single locked, atomic write of the complete rebuilt index — see
    # docstring above for why this matters over incremental per-file saves.
    with vector_store._locked(vault):
        vector_store._save(vault, {"chunks": new_chunks})
    print(f"  Done. {total_chunks} chunks across {len(md_files)} files.")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild vault vector index")
    parser.add_argument("--wiki", help="Index only this vault (default: all)")
    args = parser.parse_args()

    ids = [args.wiki] if args.wiki else available_ids()
    if not ids:
        print("No vaults configured in wikis.toml")
        return
    for vault_id in ids:
        await index_vault(vault_id)


if __name__ == "__main__":
    asyncio.run(main())
