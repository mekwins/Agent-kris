from src import vault as vault_ops
from src.vaults import get_vault


async def run(agent_type: str | None = None, wiki: str | None = None) -> dict:
    """Return recent-page context for a vault.

    `agent_type` optionally filters by a domain string within the vault; when
    omitted the most recent pages across the whole vault are returned.
    """
    vault = get_vault(wiki)
    domain = agent_type if agent_type and agent_type != "all" else None
    pages = vault_ops.list_pages(vault, domain=domain)

    if not pages:
        return {"wiki": vault.id, "context": f"No pages found in {vault.id}", "key_pages": []}

    pages.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    key_pages = pages[:10]

    context_parts = [f"## {p['title']}\n{p['content'][:500]}..." for p in key_pages]
    header = f"Brain context for wiki={vault.id}" + (f" (domain={domain})" if domain else "")
    context = header + ":\n\n" + "\n\n---\n\n".join(context_parts)

    return {"wiki": vault.id, "context": context, "key_pages": key_pages}
