"""
Brain compilation agent — Anthropic API agentic loop.

Replaces interactive Claude Code slash commands with a programmatic agent
that can be triggered remotely (WhatsApp, webhook, or direct Python call).

Supported tasks:
  "compile inbox"          — ingest all unprocessed inbox files → wiki pages
  "compile inbox limit=N"  — batch compile, max N files
  "compile sources"        — recompile from sources/ after connector sync
  "search: <question>"     — synthesize cited answer from wiki
  "lint"                   — check broken wikilinks, orphan pages, frontmatter
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

import frontmatter as fm
from anthropic import AsyncAnthropic

from src.config import ANTHROPIC_FOUNDRY_BASE_URL, ANTHROPIC_FOUNDRY_API_KEY, VAULT_PATH
from src import vault, vector_store
from src import embed as embedder

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 50  # safety cap on the agentic loop

SYSTEM_PROMPT = f"""You are a knowledge compiler for a personal second brain vault stored at a local filesystem.

## Vault structure
- inbox/         — unprocessed notes (frontmatter status: inbox)
- wiki/          — your compiled, interlinked knowledge base
  - wiki/index.md      — master table of contents (you maintain this)
  - wiki/log.md        — chronological activity log (you maintain this)
  - wiki/concepts/     — settled, factual knowledge (definitions, how things work)
  - wiki/people/       — one page per named person
  - wiki/projects/     — project-specific pages with goals and status
  - wiki/areas/        — ongoing areas of interest or responsibility
  - wiki/brainstorm/   — speculative ideas, startup concepts, creative explorations, session captures
- sources/       — immutable raw inputs (read-only — never write here)

## Frontmatter schema
---
title: "Page Title"
date: YYYY-MM-DD
domain: work | personal | learning
tags: [tag1, tag2]
status: active
---

## Tag taxonomy
Work: nexteer, enterprise-architecture, ai-strategy, vibe-coding, governance, agents, mcp, coolify, claude-enterprise
Personal: health, language-learning, polish, spanish, travel, pixel, birdy
Learning: book, podcast, article, course, ai-research, engineering, programming
Brainstorm: startup-idea, innovation, brainstorm, creative, experiment, concept-draft

## Domain routing
- Nexteer / EA / AI CoE / IT → domain: work
- Health / family / hobbies / Pixel / Birdy → domain: personal
- Books / courses / research / general AI → domain: learning
- Brainstorm content inherits the nearest domain (startup idea → work, personal project → personal, research concept → learning)

## Folder routing
At the start of every compile run, call read_vault_file("FOLDERS.md") to load the current folder registry and routing rules. That file is the single source of truth — always follow it. New folders can be added there without code changes.

Default folders (if FOLDERS.md cannot be read):
- wiki/concepts/ — factual/settled knowledge
- wiki/people/ — named persons
- wiki/projects/ — projects with goals
- wiki/areas/ — ongoing responsibilities
- wiki/brainstorm/ — speculative ideas (prefix: "Idea: ")
- wiki/learning/ — course material, books, exercises, research

## Wiki page format
---
title: "Concept Name"
date: YYYY-MM-DD
domain: work | personal | learning
tags: [relevant, tags]
status: active
---

# Concept Name

2-3 sentence summary of what this concept is and why it matters.

## Key Points
- Important insight or fact
- Another key point

## Related Concepts
- [[Existing Wiki Page]] — brief note on the relationship

## Sources
- [[Source Page Title]]

## Rules
1. One concept per wiki page. Split pages covering multiple unrelated things.
2. Always use [[Page Title]] wikilinks to link to related existing pages.
3. Never delete content — tag outdated content as "archived" instead.
4. People get their own page in wiki/people/ with their ideas and quotes.
5. After a compile run: update wiki/index.md (add new pages) and wiki/log.md (append entry).
6. After writing any wiki page, call embed_wiki_page to index it for semantic search.
7. Call mark_processed on each inbox file after it has been compiled into wiki pages.
8. Do not write to sources/ — it is read-only.

## Compile task (when asked to compile inbox)
1. Call read_vault_file("FOLDERS.md") to load the folder registry and routing rules
2. Call list_vault_files("inbox") to find files with status: inbox
3. For each unprocessed file:
   a. Call read_vault_file to get the content
   b. Identify the domain from content and tags
   c. Determine the target folder using the rules from FOLDERS.md (loaded in step 1)
   d. Call search_wiki before writing to find existing related pages for [[wikilinks]]
   e. Call write_vault_file with the compiled wiki page
   f. Call embed_wiki_page to index the new/updated page
   g. Call mark_processed on the inbox file
4. Update wiki/index.md with links to any new pages (grouped by folder)
5. Append a dated entry to wiki/log.md summarising what was compiled

## Lint task (when asked to lint)
Check every wiki/ page for:
- Broken [[wikilinks]] (link targets that don't exist as wiki pages)
- Missing required frontmatter fields (title, domain, tags, status)
- Orphan pages (no other page links to them)
Report findings without auto-fixing unless asked.

## Search/query task (when asked to search or answer a question)
1. Call search_wiki with the question to find relevant pages
2. Call read_vault_file on the top results
3. Synthesize a cited answer using only the content you read
4. Cite sources as [[Page Title]]
"""

# ---------------------------------------------------------------------------
# Tool definitions (sent to the Anthropic API)
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "list_vault_files",
        "description": "List markdown files in a vault directory with their frontmatter metadata.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Relative path within vault, e.g. 'inbox', 'wiki/concepts'",
                }
            },
            "required": ["directory"],
        },
    },
    {
        "name": "read_vault_file",
        "description": "Read the full content of a vault markdown file (frontmatter + body).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path within vault, e.g. 'inbox/2026-04-19-foo.md'",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_vault_file",
        "description": "Write or overwrite a wiki page. Only allowed in wiki/ directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path within vault, e.g. 'wiki/concepts/mcp.md'",
                },
                "content": {
                    "type": "string",
                    "description": "Full markdown content including YAML frontmatter block",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "mark_processed",
        "description": "Move an inbox file to processed/ and set status: processed. The file is removed from inbox/ so the inbox stays clean.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path of the inbox file to move, e.g. 'inbox/2026-04-19-foo.md'",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "search_wiki",
        "description": "Keyword search across existing wiki pages to find related concepts for wikilinks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search terms"},
                "limit": {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "embed_wiki_page",
        "description": "Index a newly written or updated wiki page into the vector store for semantic search.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path of the wiki page to embed, e.g. 'wiki/concepts/mcp.md'",
                }
            },
            "required": ["path"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _list_vault_files(directory: str) -> list[dict[str, Any]]:
    dir_path = VAULT_PATH / directory
    if not dir_path.exists():
        return []
    results = []
    for md_file in sorted(dir_path.rglob("*.md")):
        rel = str(md_file.relative_to(VAULT_PATH))
        page = vault.read_page(rel)
        if page:
            results.append({
                "path": rel,
                "title": page["title"],
                "domain": page["domain"],
                "tags": page["tags"],
                "status": page.get("status", ""),
                "updated_at": page["updated_at"],
            })
    return results


def _read_vault_file(path: str) -> str:
    file_path = VAULT_PATH / path
    if not file_path.exists():
        return f"ERROR: File not found: {path}"
    return file_path.read_text(encoding="utf-8")


def _write_vault_file(path: str, content: str) -> dict[str, Any]:
    if not path.startswith("wiki/"):
        return {"error": f"Write blocked: can only write to wiki/, got: {path}"}
    file_path = VAULT_PATH / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return {"written": path, "bytes": len(content.encode())}


def _mark_processed(path: str) -> dict[str, Any]:
    file_path = VAULT_PATH / path
    if not file_path.exists():
        return {"error": f"File not found: {path}"}
    post = fm.load(str(file_path))
    post["status"] = "processed"
    dest_dir = VAULT_PATH / "processed"
    dest_dir.mkdir(exist_ok=True)
    dest_path = dest_dir / file_path.name
    dest_path.write_text(fm.dumps(post), encoding="utf-8")
    file_path.unlink()
    return {"moved_to_processed": str(dest_path.relative_to(VAULT_PATH))}


def _search_wiki(query: str, limit: int = 5) -> list[dict[str, Any]]:
    results = vault.keyword_search(query, scope="all", limit=limit)
    return [{"page_slug": r["page_slug"], "snippet": r["content"]} for r in results]


async def _embed_wiki_page(path: str) -> dict[str, Any]:
    page = vault.read_page(path)
    if not page:
        return {"error": f"Page not found: {path}"}
    chunks = vector_store.chunk_content(
        page["content"],
        page_slug=page["slug"],
        tags=page["tags"],
        domain=page["domain"],
    )
    if not chunks:
        return {"embedded": path, "chunks": 0}
    texts = [c["content"] for c in chunks]
    embeddings = await embedder.embed_batch(texts)
    vector_store.upsert(page["slug"], chunks, embeddings)
    return {"embedded": path, "chunks": len(chunks)}


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

class BrainAgent:
    def __init__(self) -> None:
        self.client = AsyncAnthropic(
            base_url=ANTHROPIC_FOUNDRY_BASE_URL,
            api_key=ANTHROPIC_FOUNDRY_API_KEY,
            default_headers={"api-key": ANTHROPIC_FOUNDRY_API_KEY},
        )

    async def run(self, task: str) -> str:
        """Run the agent with a task string. Returns a summary of what was done."""
        messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
        iterations = 0

        while iterations < MAX_ITERATIONS:
            iterations += 1
            response = await self.client.messages.create(
                model=MODEL,
                max_tokens=8096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                tool_results = await self._handle_tool_calls(response)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        return f"Agent stopped after {iterations} iterations (stop_reason={response.stop_reason})."

    async def _handle_tool_calls(self, response: Any) -> list[dict[str, Any]]:
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = await self._execute_tool(block.name, block.input)
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, default=str),
            })
        return results

    async def _execute_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "list_vault_files":
                return _list_vault_files(inputs["directory"])
            case "read_vault_file":
                return _read_vault_file(inputs["path"])
            case "write_vault_file":
                return _write_vault_file(inputs["path"], inputs["content"])
            case "mark_processed":
                return _mark_processed(inputs["path"])
            case "search_wiki":
                return _search_wiki(inputs["query"], inputs.get("limit", 5))
            case "embed_wiki_page":
                return await _embed_wiki_page(inputs["path"])
            case _:
                return {"error": f"Unknown tool: {name}"}

    def _extract_text(self, response: Any) -> str:
        return "\n".join(
            block.text for block in response.content if hasattr(block, "text")
        )


# ---------------------------------------------------------------------------
# Git auto-commit
# ---------------------------------------------------------------------------

def _git_commit(task: str) -> str | None:
    """Stage all vault changes and commit with a timestamped message.
    Returns the short commit hash, or None if there was nothing to commit.
    """
    repo = VAULT_PATH.parent
    try:
        # Stage everything inside vault/ (wiki, processed, sources, index, log)
        subprocess.run(["git", "add", "vault/"], cwd=repo, check=True, capture_output=True)
        # Check if there's actually anything staged
        diff = subprocess.run(
            ["git", "diff", "--cached", "--stat"],
            cwd=repo, check=True, capture_output=True, text=True,
        )
        if not diff.stdout.strip():
            return None
        today = date.today().isoformat()
        msg = f"brain: {task} [{today}]"
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=repo, check=True, capture_output=True, text=True,
        )
        # Extract short hash from "main abc1234" style output
        for line in result.stdout.splitlines():
            if line.startswith("["):
                return line.split()[1]
        return "committed"
    except subprocess.CalledProcessError:
        return None


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------

_COMPILE_TASKS = {"compile inbox", "compile sources"}

async def run(task: str) -> str:
    """Module-level entry point for use by trigger layer and scripts."""
    agent = BrainAgent()
    result = await agent.run(task)

    # Auto-commit vault changes after any compile run
    base_task = task.split(" limit=")[0].strip()
    if base_task in _COMPILE_TASKS:
        commit_hash = _git_commit(base_task)
        if commit_hash:
            result += f"\n\n---\n🗂 Vault changes committed to git ({commit_hash}). Run `git show` to inspect."
        # Nothing new to commit is fine — no noise added to result

    return result
