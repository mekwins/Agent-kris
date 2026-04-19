from src import vault


async def run(topic: str, depth: int = 1) -> dict:
    rel_path = vault.find_page_by_topic(topic)
    if not rel_path:
        return {"error": f"No wiki page found for topic: {topic}"}

    page = vault.read_page(rel_path)
    if not page:
        return {"error": f"Could not read page: {rel_path}"}

    related = []
    linked_slugs = set(page["wikilinks"])

    for link_title in linked_slugs:
        link_path = vault.find_page_by_topic(link_title)
        if link_path:
            linked_page = vault.read_page(link_path)
            if linked_page:
                related.append(linked_page)

    if depth == 2:
        depth2_slugs: set[str] = set()
        for linked_page in related:
            for wl in linked_page["wikilinks"]:
                if wl not in linked_slugs:
                    depth2_slugs.add(wl)
        for link_title in depth2_slugs:
            link_path = vault.find_page_by_topic(link_title)
            if link_path:
                linked_page = vault.read_page(link_path)
                if linked_page:
                    related.append(linked_page)

    return {"page": page, "related": related}
