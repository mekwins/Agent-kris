"""
Brain compilation agent — Anthropic API agentic loop, scoped to a single vault.

The *engine* prompt below is generic (mechanics: folders, wikilinks, tools,
tasks). Everything vault-specific — tag taxonomy, routing nuances, note-type
schemas, editorial voice — comes from that vault's `.brain/` profile and is
appended at runtime. So a new vault type needs a new profile, not new code.

Supported tasks:
  "compile inbox"          — ingest all unprocessed inbox files → wiki pages
  "compile inbox limit=N"  — batch compile, max N files
  "compile sources"        — recompile from sources/ after connector sync
  "search: <question>"     — synthesize cited answer from wiki
  "lint"                   — check broken wikilinks, orphan pages, frontmatter
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import frontmatter as fm
from anthropic import AsyncAnthropic

from src.config import ANTHROPIC_FOUNDRY_BASE_URL, ANTHROPIC_FOUNDRY_API_KEY
from src import vault as vault_ops, vector_store, gitsync
from src import embed as embedder
from src.vaults import Vault, get_vault

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 50  # safety cap on the agentic loop

# Generic, vault-agnostic mechanics. The vault profile is appended after this.
ENGINE_PROMPT = """You are a knowledge compiler for a personal second-brain vault stored on a local filesystem.

## Vault structure
- inbox/         — unprocessed notes (frontmatter status: inbox)
- wiki/          — your compiled, interlinked knowledge base
  - wiki/index.md      — master table of contents (you maintain this)
  - wiki/log.md        — chronological activity log (you maintain this)
  - wiki/concepts/     — settled, factual knowledge
  - wiki/people/       — one page per named person
  - wiki/projects/     — project-specific pages with goals and status
  - wiki/areas/        — ongoing areas of interest or responsibility
  - wiki/brainstorm/   — speculative ideas and creative explorations
  - wiki/learning/     — course/book/practice material (subfolder per subject)
  - wiki/tasks/        — actionable tasks (any vault); each links to its assignee
- sources/       — immutable raw inputs (read-only — never write here)

## Wiki page format
---
title: "Concept Name"
date: YYYY-MM-DD
domain: <a domain string valid for this vault>
tags: [relevant, tags]
status: active
---

# Concept Name

2-3 sentence summary of what this is and why it matters.

## Key Points
- Important insight or fact

## Related Concepts
- [[Existing Wiki Page]] — brief note on the relationship

## Sources
- [[Source Page Title]]

## General rules
1. One concept per wiki page. Split pages covering multiple unrelated things.
2. Always use [[Page Title]] wikilinks to connect related existing pages.
3. Never delete content — tag outdated content as "archived" instead.
4. After writing any wiki page, call embed_wiki_page to index it for search.
5. Call mark_processed on each inbox file after compiling it into wiki pages.
6. Do not write to sources/ — it is read-only.

## Tasks and people cross-referencing (applies to EVERY vault)
Tasks can appear in any vault. When a note describes something to do (or the
user says "add a task to ... for <person>"):
1. Create/update a page in wiki/tasks/ named after the task. Frontmatter:
   title, status (open|done), assignee, due (optional), related, tags.
2. Resolve every named person BEFORE writing the task:
   a. Call search_wiki with the person's name to check if they already exist.
   b. If a wiki/people/ page exists, reuse it — link as [[Their Name]] and set
      assignee to that exact title. Do NOT create a duplicate.
   c. If they do NOT exist, create a short wiki/people/<name>.md stub (just the
      name and that they were referenced — never invent facts) and link to it.
3. Link the task to any related project/concept with [[wikilinks]].
4. On the assignee's people page, add the task under an "## Assigned Tasks"
   section as [[Task Title]] — so the link is bidirectional and shows up in
   both retrieval (brain_recall) and Obsidian's backlinks panel.
This resolve-or-create-then-link behavior is how the vault stays a connected
graph rather than a pile of disconnected notes.

## Folder routing
At the start of every compile run, call read_vault_file(".brain/folders.md") to
load this vault's folder registry and routing rules. That file is the single
source of truth for where content goes — always follow it.

## Compile task (when asked to compile inbox)
1. Read the folder routing rules (.brain/folders.md)
2. list_vault_files("inbox") to find files with status: inbox
3. For each unprocessed file: read it, classify it, pick the target folder,
   search_wiki for existing related pages to [[wikilink]], write_vault_file the
   compiled page, embed_wiki_page it, then mark_processed the inbox file
4. Update wiki/index.md (add new pages, grouped by folder)
5. Append a dated entry to wiki/log.md summarising what was compiled

## Lint task
Check every wiki/ page for broken [[wikilinks]], missing required frontmatter
(title, domain, tags, status), and orphan pages. Report without auto-fixing.

## Search/query task
search_wiki for the question, read_vault_file the top results, synthesize a
cited answer using only what you read, and cite sources as [[Page Title]].
"""


def _system_prompt(vault: Vault) -> str:
    """Engine mechanics + this vault's profile (routing, types, editorial rules)."""
    parts = [
        ENGINE_PROMPT,
        f"\n# Vault: {vault.id}\n{vault.profile.description}".rstrip(),
    ]
    types = vault.profile.types_summary()
    if types:
        parts.append("\n" + types)
    parts.append("\n## This vault's compile rules\n" + vault.profile.compile_prompt)
    return "\n".join(parts)


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
        "description": "Read the full content of a vault file (frontmatter + body). Also works for .brain/folders.md.",
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
        "description": "Move an inbox file to processed/ and set status: processed.",
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
# Agent loop
# ---------------------------------------------------------------------------

class BrainAgent:
    def __init__(self, vault: Vault) -> None:
        self.vault = vault
        self.client = AsyncAnthropic(
            base_url=ANTHROPIC_FOUNDRY_BASE_URL,
            api_key=ANTHROPIC_FOUNDRY_API_KEY,
            default_headers={"api-key": ANTHROPIC_FOUNDRY_API_KEY},
        )

    async def run(self, task: str) -> str:
        """Run the agent with a task string. Returns a summary of what was done."""
        messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
        iterations = 0
        system = _system_prompt(self.vault)

        while iterations < MAX_ITERATIONS:
            iterations += 1
            response = await self.client.messages.create(
                model=MODEL,
                max_tokens=8096,
                system=system,
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
                return self._list_vault_files(inputs["directory"])
            case "read_vault_file":
                return self._read_vault_file(inputs["path"])
            case "write_vault_file":
                return self._write_vault_file(inputs["path"], inputs["content"])
            case "mark_processed":
                return self._mark_processed(inputs["path"])
            case "search_wiki":
                return self._search_wiki(inputs["query"], inputs.get("limit", 5))
            case "embed_wiki_page":
                return await self._embed_wiki_page(inputs["path"])
            case _:
                return {"error": f"Unknown tool: {name}"}

    # --- tool implementations (all scoped to self.vault) -------------------

    def _list_vault_files(self, directory: str) -> list[dict[str, Any]]:
        dir_path = self.vault.path / directory
        if not dir_path.exists():
            return []
        results = []
        for md_file in sorted(dir_path.rglob("*.md")):
            rel = str(md_file.relative_to(self.vault.path))
            page = vault_ops.read_page(self.vault, rel)
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

    def _read_vault_file(self, path: str) -> str:
        file_path = self.vault.path / path
        if not file_path.exists():
            return f"ERROR: File not found: {path}"
        return file_path.read_text(encoding="utf-8")

    def _write_vault_file(self, path: str, content: str) -> dict[str, Any]:
        if not path.startswith("wiki/"):
            return {"error": f"Write blocked: can only write to wiki/, got: {path}"}
        file_path = self.vault.path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return {"written": path, "bytes": len(content.encode())}

    def _mark_processed(self, path: str) -> dict[str, Any]:
        file_path = self.vault.path / path
        if not file_path.exists():
            return {"error": f"File not found: {path}"}
        post = fm.load(str(file_path))
        post["status"] = "processed"
        dest_dir = self.vault.path / "processed"
        dest_dir.mkdir(exist_ok=True)
        dest_path = dest_dir / file_path.name
        dest_path.write_text(fm.dumps(post), encoding="utf-8")
        file_path.unlink()
        return {"moved_to_processed": str(dest_path.relative_to(self.vault.path))}

    def _search_wiki(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        results = vault_ops.keyword_search(self.vault, query, scope="all", limit=limit)
        return [{"page_slug": r["page_slug"], "snippet": r["content"]} for r in results]

    async def _embed_wiki_page(self, path: str) -> dict[str, Any]:
        page = vault_ops.read_page(self.vault, path)
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
        vector_store.upsert(self.vault, page["slug"], chunks, embeddings)
        return {"embedded": path, "chunks": len(chunks)}

    def _extract_text(self, response: Any) -> str:
        return "\n".join(
            block.text for block in response.content if hasattr(block, "text")
        )


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------

_COMPILE_TASKS = {"compile inbox", "compile sources"}


async def run(task: str, wiki: str | None = None) -> str:
    """Module-level entry point. Runs `task` against the given (or default) vault.

    For compile tasks we pull the vault repo first (so we build on the latest
    content from other clones), then commit + push afterwards (so the results
    reach GitHub and every other clone). Both are best-effort.
    """
    vault = get_vault(wiki)
    base_task = task.split(" limit=")[0].strip()
    is_compile = base_task in _COMPILE_TASKS

    if is_compile:
        gitsync.pull(vault)

    agent = BrainAgent(vault)
    result = await agent.run(task)

    if is_compile:
        msg = f"brain[{vault.id}]: {base_task} [{date.today().isoformat()}]"
        commit_hash = gitsync.commit_and_push(vault, msg)
        if commit_hash:
            result += (
                f"\n\n---\nVault '{vault.id}' changes committed and pushed ({commit_hash})."
            )

    return result
