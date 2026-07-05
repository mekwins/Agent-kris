from src.search import semantic_search, keyword_search, hybrid_search
from src.config import DEFAULT_SEARCH_LIMIT
from src.vaults import get_vault


async def run(
    query: str,
    scope: str = "all",
    limit: int = DEFAULT_SEARCH_LIMIT,
    mode: str = "hybrid",
    wiki: str | None = None,
) -> dict:
    vault = get_vault(wiki)
    if mode == "keyword":
        result = keyword_search(vault, query, scope=scope, limit=limit)
    elif mode == "semantic":
        result = await semantic_search(vault, query, scope=scope, limit=limit)
    else:
        result = await hybrid_search(vault, query, scope=scope, limit=limit)
    result["wiki"] = vault.id
    return result
