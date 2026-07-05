from src import vault as vault_ops, embed as embedder, vector_store, gitsync
from src.vaults import get_vault


async def run(
    content: str,
    tags: list[str],
    domain: str,
    title: str | None = None,
    source_url: str | None = None,
    wiki: str | None = None,
) -> dict:
    vault = get_vault(wiki)
    rel_path = vault_ops.write_inbox(vault, content, tags, domain, title=title, source_url=source_url)
    page_slug = rel_path.removesuffix(".md")

    chunks = vector_store.chunk_content(content, page_slug=page_slug, tags=tags, domain=domain)
    if chunks:
        texts = [c["content"] for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        vector_store.upsert(vault, page_slug, chunks, embeddings)

    # Push the capture to GitHub so it reaches every other clone (best-effort).
    pushed = gitsync.commit_and_push(vault, f"brain[{vault.id}]: capture {rel_path}")

    return {
        "wiki": vault.id,
        "path": rel_path,
        "committed": bool(pushed),
        "chunks_indexed": len(chunks),
    }
