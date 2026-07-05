from src.vaults import list_vaults


async def run() -> dict:
    """Return every configured vault with its description, domains and note types.

    Call this first so you know which `wiki` to target for other brain tools.
    """
    return {"wikis": list_vaults()}
