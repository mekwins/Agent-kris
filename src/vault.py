"""Local filesystem operations for the vault."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import frontmatter

from src.config import VAULT_PATH


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", text.lower().strip()).strip("-")


def read_page(rel_path: str) -> dict[str, Any] | None:
    """Read a markdown file and return its frontmatter + content."""
    path = VAULT_PATH / rel_path
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
    content: str,
    tags: list[str],
    domain: str,
    title: str | None = None,
    source_url: str | None = None,
) -> str:
    """Write a new file to vault/inbox/ with proper frontmatter. Returns relative path."""
    today = date.today().isoformat()
    slug = _slugify(title or f"note-{today}")
    filename = f"{today}-{slug}.md"
    inbox_dir = VAULT_PATH / "inbox"
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


def find_page_by_topic(topic: str) -> str | None:
    """Find a wiki page path by slug or title (case-insensitive)."""
    wiki_dir = VAULT_PATH / "wiki"
    if not wiki_dir.exists():
        return None
    normalized = _slugify(topic)
    for md_file in wiki_dir.rglob("*.md"):
        rel = md_file.relative_to(VAULT_PATH)
        if _slugify(md_file.stem) == normalized:
            return str(rel)
        post = frontmatter.load(str(md_file))
        if _slugify(post.get("title", "")) == normalized:
            return str(rel)
    return None


def list_pages(domain: str | None = None) -> list[dict[str, Any]]:
    """List all wiki pages, optionally filtered by domain."""
    wiki_dir = VAULT_PATH / "wiki"
    if not wiki_dir.exists():
        return []
    pages = []
    for md_file in wiki_dir.rglob("*.md"):
        page = read_page(str(md_file.relative_to(VAULT_PATH)))
        if page and (domain is None or page["domain"] == domain):
            pages.append(page)
    return pages


def keyword_search(query: str, scope: str = "all", limit: int = 10) -> list[dict[str, Any]]:
    """Full-text search across all vault markdown files. Returns chunk-shaped dicts."""
    search_dirs = [VAULT_PATH / "wiki", VAULT_PATH / "sources", VAULT_PATH / "inbox"]
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results: list[dict[str, Any]] = []

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for md_file in search_dir.rglob("*.md"):
            page = read_page(str(md_file.relative_to(VAULT_PATH)))
            if not page:
                continue
            if scope != "all" and page["domain"] != scope:
                continue

            # Find all matches and extract a snippet around each
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
