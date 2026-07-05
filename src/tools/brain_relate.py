from src import vault as vault_ops
from src.vaults import get_vault


async def run(concept_a: str, concept_b: str, wiki: str | None = None) -> dict:
    vault = get_vault(wiki)
    path_a = vault_ops.find_page_by_topic(vault, concept_a)
    path_b = vault_ops.find_page_by_topic(vault, concept_b)

    if not path_a:
        return {"error": f"No page found for: {concept_a}", "wiki": vault.id}
    if not path_b:
        return {"error": f"No page found for: {concept_b}", "wiki": vault.id}

    page_a = vault_ops.read_page(vault, path_a)
    page_b = vault_ops.read_page(vault, path_b)

    if not page_a or not page_b:
        return {"error": "Could not read one or both pages", "wiki": vault.id}

    tags_a = set(page_a["tags"])
    tags_b = set(page_b["tags"])
    shared_tags = sorted(tags_a & tags_b)

    path: list[str] = []
    links_a = set(page_a["wikilinks"])
    links_b = set(page_b["wikilinks"])

    if page_b["title"] in links_a or concept_b in links_a:
        path = [page_a["title"], page_b["title"]]
    elif page_a["title"] in links_b or concept_a in links_b:
        path = [page_b["title"], page_a["title"]]
    else:
        # Check for a shared intermediate page (1-hop bridge)
        for link in links_a:
            bridge_path = vault_ops.find_page_by_topic(vault, link)
            if bridge_path:
                bridge = vault_ops.read_page(vault, bridge_path)
                if bridge and (page_b["title"] in bridge["wikilinks"] or concept_b in bridge["wikilinks"]):
                    path = [page_a["title"], bridge["title"], page_b["title"]]
                    break

    return {
        "wiki": vault.id,
        "concept_a": page_a["title"],
        "concept_b": page_b["title"],
        "shared_tags": shared_tags,
        "path": path,
        "direct_link": len(path) == 2,
    }
