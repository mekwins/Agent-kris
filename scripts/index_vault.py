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


async def index_file(vault: Vault, md_file: Path) -> int:
    rel = str(md_file.relative_to(vault.path))
    page = vault_ops.read_page(vault, rel)
    if not page:
        return 0

    page_slug = rel.removesuffix(".md")
    chunks = vector_store.chunk_content(
        page["content"],
        page_slug=page_slug,
        tags=page["tags"],
        domain=page["domain"],
    )
    if not chunks:
        return 0

    texts = [c["content"] for c in chunks]
    embeddings = await embedder.embed_batch(texts)
    vector_store.upsert(vault, page_slug, chunks, embeddings)
    return len(chunks)


async def index_vault(vault_id: str) -> None:
    vault = get_vault(vault_id)
    dirs = [vault.path / "wiki", vault.path / "sources"]
    md_files = [f for d in dirs if d.exists() for f in d.rglob("*.md")]

    print(f"\n=== Vault '{vault.id}' ({vault.path}) ===")
    if not md_files:
        print("  No markdown files found in wiki/ or sources/")
        return

    # Fresh index for this vault (avoid stale chunks from renamed/removed pages).
    if vault.vectors_path.exists():
        vault.vectors_path.unlink()

    print(f"  Indexing {len(md_files)} files...")
    total_chunks = 0
    for i, md_file in enumerate(md_files, 1):
        count = await index_file(vault, md_file)
        total_chunks += count
        rel = md_file.relative_to(vault.path)
        print(f"    [{i}/{len(md_files)}] {rel} — {count} chunks")
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
