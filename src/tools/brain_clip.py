"""brain_clip — fetch a URL, extract article content as markdown, download images locally."""

from __future__ import annotations

import asyncio
import hashlib
import re
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import trafilatura

from src.config import VAULT_PATH

_SLUG_RE = re.compile(r"[^\w\s-]")
_SPACES_RE = re.compile(r"[\s_]+")
_IMG_RE = re.compile(r"!\[([^\]]*)\]\((https?://[^\)\s]+)\)")


def _slugify(text: str) -> str:
    text = _SLUG_RE.sub("", text.lower())
    return _SPACES_RE.sub("-", text).strip("-")[:60]


async def _download_image(url: str, dest: Path) -> bool:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(r.content)
            return True
    except Exception:
        return False


async def run(
    url: str,
    domain: str = "learning",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    tags = tags or ["article"]

    # Fetch raw HTML
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        return {"error": f"Fetch failed: {e}"}

    # Extract article content as markdown (trafilatura strips nav, ads, boilerplate)
    content = trafilatura.extract(
        html,
        output_format="markdown",
        include_images=True,
        include_links=True,
        favor_recall=True,
    )
    if not content:
        return {"error": "Could not extract readable content from URL — page may be JS-rendered or paywalled"}

    # Extract title and other metadata
    meta = trafilatura.extract_metadata(html, default_url=url)
    title = (meta.title if meta and meta.title else url)[:120]
    slug = _slugify(title)

    # Rewrite image URLs → local paths and collect downloads
    assets_rel = f"assets/{slug}"
    assets_dir = VAULT_PATH / assets_rel
    pending: list[tuple[str, Path]] = []

    def _rewrite(m: re.Match) -> str:
        alt, img_url = m.group(1), m.group(2)
        ext = Path(img_url.split("?")[0]).suffix or ".jpg"
        if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
            ext = ".jpg"
        filename = hashlib.md5(img_url.encode()).hexdigest()[:12] + ext
        pending.append((img_url, assets_dir / filename))
        return f"![{alt}](../../{assets_rel}/{filename})"

    content_local = _IMG_RE.sub(_rewrite, content)

    # Download all images concurrently
    results = await asyncio.gather(*[_download_image(u, d) for u, d in pending])
    images_ok = sum(results)

    # Build inbox file
    today = date.today().isoformat()
    tags_yaml = ", ".join(tags)
    body = (
        f"---\n"
        f'title: "{title}"\n'
        f"date: {today}\n"
        f"domain: {domain}\n"
        f"tags: [{tags_yaml}]\n"
        f'source_url: "{url}"\n'
        f"status: inbox\n"
        f"---\n\n"
        f"# {title}\n\n"
        f"{content_local}\n"
    )

    filename = f"{today}-{slug}.md"
    inbox_path = VAULT_PATH / "inbox" / filename
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    inbox_path.write_text(body, encoding="utf-8")

    return {
        "clipped": f"inbox/{filename}",
        "title": title,
        "domain": domain,
        "tags": tags,
        "words": len(content_local.split()),
        "images_downloaded": images_ok,
        "images_total": len(pending),
        "assets_dir": f"vault/{assets_rel}" if pending else None,
    }
