from src import vault as vault_ops
from src.vaults import get_vault


async def run(topic: str, depth: int = 1, wiki: str | None = None) -> dict:
    vault = get_vault(wiki)
    rel_path = vault_ops.find_page_by_topic(vault, topic)
    if not rel_path:
        return {"error": f"No wiki page found for topic: {topic}", "wiki": vault.id}

    page = vault_ops.read_page(vault, rel_path)
    if not page:
        return {"error": f"Could not read page: {rel_path}", "wiki": vault.id}

    related = []
    linked_slugs = set(page["wikilinks"])

    for link_title in linked_slugs:
        link_path = vault_ops.find_page_by_topic(vault, link_title)
        if link_path:
            linked_page = vault_ops.read_page(vault, link_path)
            if linked_page:
                related.append(linked_page)

    if depth == 2:
        depth2_slugs: set[str] = set()
        for linked_page in related:
            for wl in linked_page["wikilinks"]:
                if wl not in linked_slugs:
                    depth2_slugs.add(wl)
        for link_title in depth2_slugs:
            link_path = vault_ops.find_page_by_topic(vault, link_title)
            if link_path:
                linked_page = vault_ops.read_page(vault, link_path)
                if linked_page:
                    related.append(linked_page)

    return {"wiki": vault.id, "page": page, "related": related}
