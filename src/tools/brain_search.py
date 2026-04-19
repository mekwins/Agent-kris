from src.search import semantic_search, keyword_search, hybrid_search
from src.config import DEFAULT_SEARCH_LIMIT


async def run(
    query: str,
    scope: str = "all",
    limit: int = DEFAULT_SEARCH_LIMIT,
    mode: str = "hybrid",
) -> dict:
    if mode == "keyword":
        return keyword_search(query, scope=scope, limit=limit)
    if mode == "semantic":
        return await semantic_search(query, scope=scope, limit=limit)
    return await hybrid_search(query, scope=scope, limit=limit)
