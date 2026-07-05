"""Brain MCP server — SSE transport with optional API key auth."""

from __future__ import annotations

import anyio
import argparse
import json
import os
from typing import Literal

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import Response

from src.tools import (
    brain_search, brain_recall, brain_write, brain_context,
    brain_relate, brain_clip, brain_list_wikis,
)
from src import agent as brain_agent
from src.config import MCP_API_KEY

# Every tool takes an optional `wiki` id. Vaults are dynamic (from wikis.toml),
# so the param is a free string — call brain_list_wikis to discover valid ids.

# Bind address is env-configurable so the same image runs locally (127.0.0.1)
# and on a host like fly.io (HOST=0.0.0.0, PORT injected by the platform).
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8765"))

mcp = FastMCP("brain-mcp", host=HOST, port=PORT)


class APIKeyMiddleware:
    """Pure ASGI middleware — safe for SSE streaming (no response buffering).

    Localhost (127.0.0.1 / ::1) is always trusted without a key so that
    mcp-remote reconnections work even when the header is dropped.
    API key is enforced for all non-local clients (remote hosting scenario).
    """

    def __init__(self, app, api_key: str) -> None:
        self.app = app
        self.api_key = api_key

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            client_ip = (scope.get("client") or ("", 0))[0]
            if client_ip not in ("127.0.0.1", "::1"):
                headers = {k.lower(): v for k, v in scope.get("headers", [])}
                key = headers.get(b"x-api-key", b"").decode()
                if key != self.api_key:
                    response = Response("Unauthorized", status_code=401)
                    await response(scope, receive, send)
                    return
        await self.app(scope, receive, send)


@mcp.tool()
async def brain_list_wikis_tool() -> str:
    """List all available vaults (wikis) with their descriptions, domains, and note types. Call this first to know which `wiki` to pass to the other tools."""
    result = await brain_list_wikis.run()
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def brain_search_tool(
    query: str,
    scope: str = "all",
    limit: int = 10,
    mode: Literal["hybrid", "semantic", "keyword"] = "hybrid",
    wiki: str | None = None,
) -> str:
    """Search wiki and source content within a vault. mode=hybrid (default) combines semantic + keyword; keyword does exact text match only; semantic does vector search only. `scope` optionally filters by a domain string; use brain_list_wikis to see a vault's domains."""
    result = await brain_search.run(query, scope=scope, limit=limit, mode=mode, wiki=wiki)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def brain_recall_tool(
    topic: str,
    depth: Literal[1, 2] = 1,
    wiki: str | None = None,
) -> str:
    """Fetch a specific wiki page and its linked neighbors from a vault."""
    result = await brain_recall.run(topic, depth=depth, wiki=wiki)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def brain_write_tool(
    content: str,
    tags: list[str],
    domain: str,
    title: str | None = None,
    source_url: str | None = None,
    wiki: str | None = None,
) -> str:
    """Write new content to a vault's inbox and index it for search."""
    result = await brain_write.run(content, tags, domain, title=title, source_url=source_url, wiki=wiki)
    return json.dumps(result, indent=2)


@mcp.tool()
async def brain_context_tool(
    agent_type: str | None = None,
    wiki: str | None = None,
) -> str:
    """Return a recent-page context bundle for a vault. `agent_type` optionally filters by a domain string within that vault."""
    result = await brain_context.run(agent_type, wiki=wiki)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def brain_relate_tool(
    concept_a: str,
    concept_b: str,
    wiki: str | None = None,
) -> str:
    """Find the connection path and shared tags between two wiki concepts in a vault."""
    result = await brain_relate.run(concept_a, concept_b, wiki=wiki)
    return json.dumps(result, indent=2)


@mcp.tool()
async def brain_clip_tool(
    url: str,
    domain: str = "learning",
    tags: list[str] | None = None,
    wiki: str | None = None,
) -> str:
    """Clip a web page to a vault's inbox. Fetches the URL, extracts the article as markdown, downloads images to <vault>/assets/. Compile afterwards to add it to the wiki."""
    result = await brain_clip.run(url, domain=domain, tags=tags or ["article"], wiki=wiki)
    return json.dumps(result, indent=2)


@mcp.tool()
async def brain_compile_tool(
    task: Literal["compile inbox", "compile sources", "lint", "search"] = "compile inbox",
    limit: int | None = None,
    query: str | None = None,
    wiki: str | None = None,
) -> str:
    """
    Run the brain compilation agent against a vault.
    - task='compile inbox': process all unread inbox files → wiki pages
    - task='compile sources': recompile from sources/ after connector sync
    - task='lint': check broken wikilinks, orphan pages, frontmatter
    - task='search' + query='...': synthesize a cited answer from wiki
    Pass `wiki` to select the vault (see brain_list_wikis).
    """
    if task == "search":
        if not query:
            return json.dumps({"error": "query is required for search task"})
        full_task = f"search: {query}"
    elif limit is not None:
        full_task = f"{task} limit={limit}"
    else:
        full_task = task
    result = await brain_agent.run(full_task, wiki=wiki)
    return result


async def _run_sse() -> None:
    app = mcp.sse_app()
    if MCP_API_KEY:
        app = APIKeyMiddleware(app, api_key=MCP_API_KEY)
    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Brain MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="sse",
        help="Transport mode (default: sse)",
    )
    args = parser.parse_args()

    if args.transport == "sse":
        print(f"Brain MCP server (SSE) starting on http://{HOST}:{PORT}/sse", flush=True)
        anyio.run(_run_sse)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
