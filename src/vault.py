"""Local filesystem operations for a vault.

Every function takes a `Vault` so the same engine serves any number of vaults.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

import frontmatter

from src.vaults import Vault


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", text.lower().strip()).strip("-")


def read_page(vault: Vault, rel_path: str) -> dict[str, Any] | None:
    """Read a markdown file (relative to the vault root) + its frontmatter."""
    path = vault.path / rel_path
    if not path.exists():
        return None
    post = frontmatter.load(str(path))
    return {
        "slug": rel_path.removesuffix(".md"),
        "title": post.get("title", path.stem),
        "domain": post.get("domain", ""),
        "tags": post.get("tags", []),
        "content": post.content,
        "wikilinks": extract_wikilinks(post.content),
        "updated_at": str(post.get("date", "")),
    }


def write_inbox(
    vault: Vault,
    content: str,
    tags: list[str],
    domain: str,
    title: str | None = None,
    source_url: str | None = None,
) -> str:
    """Write a new file to <vault>/inbox/ with frontmatter. Returns relative path."""
    today = date.today().isoformat()
    slug = _slugify(title or f"note-{today}")
    filename = f"{today}-{slug}.md"
    inbox_dir = vault.inbox_dir
    inbox_dir.mkdir(parents=True, exist_ok=True)

    metadata: dict[str, Any] = {
        "title": title or slug,
        "date": today,
        "domain": domain,
        "tags": tags,
        "status": "inbox",
    }
    if source_url:
        metadata["source_url"] = source_url

    post = frontmatter.Post(content, **metadata)
    path = inbox_dir / filename
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return f"inbox/{filename}"


def find_page_by_topic(vault: Vault, topic: str) -> str | None:
    """Find a wiki page path by slug or title (case-insensitive)."""
    wiki_dir = vault.wiki_dir
    if not wiki_dir.exists():
        return None
    normalized = _slugify(topic)
    for md_file in wiki_dir.rglob("*.md"):
        rel = md_file.relative_to(vault.path)
        if _slugify(md_file.stem) == normalized:
            return str(rel)
        post = frontmatter.load(str(md_file))
        if _slugify(post.get("title", "")) == normalized:
            return str(rel)
    return None


def list_pages(vault: Vault, domain: str | None = None) -> list[dict[str, Any]]:
    """List all wiki pages, optionally filtered by domain."""
    wiki_dir = vault.wiki_dir
    if not wiki_dir.exists():
        return []
    pages = []
    for md_file in wiki_dir.rglob("*.md"):
        page = read_page(vault, str(md_file.relative_to(vault.path)))
        if page and (domain is None or page["domain"] == domain):
            pages.append(page)
    return pages


def keyword_search(vault: Vault, query: str, scope: str = "all", limit: int = 10) -> list[dict[str, Any]]:
    """Full-text search across the vault's markdown. Returns chunk-shaped dicts."""
    search_dirs = [vault.path / "wiki", vault.path / "sources", vault.path / "inbox"]
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results: list[dict[str, Any]] = []

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for md_file in search_dir.rglob("*.md"):
            page = read_page(vault, str(md_file.relative_to(vault.path)))
            if not page:
                continue
            if scope != "all" and page["domain"] != scope:
                continue

            seen_snippets: set[str] = set()
            for match in pattern.finditer(page["content"]):
                start = max(0, match.start() - 120)
                end = min(len(page["content"]), match.end() + 120)
                snippet = page["content"][start:end].strip()
                if snippet in seen_snippets:
                    continue
                seen_snippets.add(snippet)
                results.append({
                    "page_slug": page["slug"],
                    "content": f"...{snippet}...",
                    "score": 1.0,
                    "tags": page["tags"],
                    "domain": page["domain"],
                    "match_type": "keyword",
                })
                if len(results) >= limit * 3:
                    break

    return results[:limit]


def extract_wikilinks(content: str) -> list[str]:
    return re.findall(r"\[\[([^\]]+)\]\]", content)
