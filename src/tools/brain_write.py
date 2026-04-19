from src import vault, embed as embedder, vector_store


async def run(
    content: str,
    tags: list[str],
    domain: str,
    title: str | None = None,
    source_url: str | None = None,
) -> dict:
    rel_path = vault.write_inbox(content, tags, domain, title=title, source_url=source_url)
    page_slug = rel_path.removesuffix(".md")

    chunks = vector_store.chunk_content(content, page_slug=page_slug, tags=tags, domain=domain)
    if chunks:
        texts = [c["content"] for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        vector_store.upsert(page_slug, chunks, embeddings)

    return {"path": rel_path, "committed": True, "chunks_indexed": len(chunks)}
