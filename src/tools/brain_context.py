from src import vault

AGENT_DOMAIN_MAP = {
    "work": "work",
    "personal": "personal",
    "research": "learning",
}


async def run(agent_type: str) -> dict:
    domain = AGENT_DOMAIN_MAP.get(agent_type, "all")
    pages = vault.list_pages(domain=domain if domain != "all" else None)

    if not pages:
        return {"context": f"No pages found for domain: {domain}", "key_pages": []}

    pages.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    key_pages = pages[:10]

    context_parts = [f"## {p['title']}\n{p['content'][:500]}..." for p in key_pages]
    context = f"Brain context for agent_type={agent_type} (domain={domain}):\n\n" + "\n\n---\n\n".join(context_parts)

    return {"context": context, "key_pages": key_pages}
