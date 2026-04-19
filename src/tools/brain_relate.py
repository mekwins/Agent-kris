from src import vault


async def run(concept_a: str, concept_b: str) -> dict:
    path_a = vault.find_page_by_topic(concept_a)
    path_b = vault.find_page_by_topic(concept_b)

    if not path_a:
        return {"error": f"No page found for: {concept_a}"}
    if not path_b:
        return {"error": f"No page found for: {concept_b}"}

    page_a = vault.read_page(path_a)
    page_b = vault.read_page(path_b)

    if not page_a or not page_b:
        return {"error": "Could not read one or both pages"}

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
            bridge_path = vault.find_page_by_topic(link)
            if bridge_path:
                bridge = vault.read_page(bridge_path)
                if bridge and (page_b["title"] in bridge["wikilinks"] or concept_b in bridge["wikilinks"]):
                    path = [page_a["title"], bridge["title"], page_b["title"]]
                    break

    return {
        "concept_a": page_a["title"],
        "concept_b": page_b["title"],
        "shared_tags": shared_tags,
        "path": path,
        "direct_link": len(path) == 2,
    }
