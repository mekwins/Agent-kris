"""Bootstrap or rebuild the vector index from all vault markdown files."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import VAULT_PATH
from src import embed as embedder, vector_store, vault


async def index_file(md_file: Path) -> int:
    rel = str(md_file.relative_to(VAULT_PATH))
    page = vault.read_page(rel)
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
    vector_store.upsert(page_slug, chunks, embeddings)
    return len(chunks)


async def main() -> None:
    dirs = [VAULT_PATH / "wiki", VAULT_PATH / "sources"]
    md_files = [f for d in dirs if d.exists() for f in d.rglob("*.md")]

    if not md_files:
        print("No markdown files found in wiki/ or sources/")
        return

    print(f"Indexing {len(md_files)} files...")
    total_chunks = 0
    for i, md_file in enumerate(md_files, 1):
        count = await index_file(md_file)
        total_chunks += count
        rel = md_file.relative_to(VAULT_PATH)
        print(f"  [{i}/{len(md_files)}] {rel} — {count} chunks")

    print(f"\nDone. {total_chunks} chunks indexed across {len(md_files)} files.")


if __name__ == "__main__":
    asyncio.run(main())
