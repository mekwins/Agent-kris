"""
Regression test for the "Object of type date is not JSON serializable" bug.

Root cause: frontmatter is parsed with PyYAML, and an unquoted date-like
scalar in a tag (e.g. `tags: [weekly-digest, 2026-10-06]` instead of
`tags: [weekly-digest, "2026-10-06"]`) is parsed by PyYAML as a real
datetime.date object, not a string. That object then flows into
vault_ops.read_page()'s "tags"/"domain" fields, into vector_store chunks,
and crashes json.dump() with:

    TypeError: Object of type date is not JSON serializable

This was hit live in production while rebuilding the 'work' vault's index:
9 real wiki pages (weekly digest notes) had exactly this frontmatter shape.

Fix: vault_ops.read_page() now stringifies domain/tags at the single source,
and vector_store._save() additionally passes default=str to json.dump() as
defense-in-depth for any other non-JSON-native value that might reach it.
"""
import datetime
from pathlib import Path

from src import vault as vault_ops
from src.vaults import Vault


def _write_page_with_date_tag(vault_path: Path) -> Vault:
    wiki_dir = vault_path / "wiki" / "areas"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    page_path = wiki_dir / "weekly-digest.md"
    # Deliberately unquoted date-like tag — this is exactly the shape PyYAML
    # parses as datetime.date rather than str.
    page_path.write_text(
        "---\n"
        "title: \"Weekly Digest\"\n"
        "date: 2026-10-06\n"
        "domain: areas\n"
        "tags: [weekly-digest, 2026-10-06]\n"
        "status: active\n"
        "---\n\n"
        "# Weekly Digest\n\nSome content.\n",
        encoding="utf-8",
    )
    return Vault(id="test", path=vault_path, profile=None)  # type: ignore[arg-type]


def test_read_page_stringifies_date_like_tags(tmp_path):
    vault = _write_page_with_date_tag(tmp_path)
    page = vault_ops.read_page(vault, "wiki/areas/weekly-digest.md")

    assert page is not None
    for tag in page["tags"]:
        assert isinstance(tag, str), (
            f"Tag {tag!r} (type {type(tag).__name__}) was not stringified — "
            "this is exactly the value that crashes json.dump() with "
            "'Object of type date is not JSON serializable'."
        )
    assert "2026-10-06" in page["tags"]
    assert isinstance(page["domain"], str)


def test_read_page_result_is_json_serializable(tmp_path):
    """End-to-end: the page dict as a whole must survive json.dumps()
    without needing default=str, proving no raw date/datetime objects
    survive into the returned dict.
    """
    import json

    vault = _write_page_with_date_tag(tmp_path)
    page = vault_ops.read_page(vault, "wiki/areas/weekly-digest.md")

    json.dumps(page)  # must not raise TypeError


def test_read_page_handles_non_list_tags_defensively(tmp_path):
    """A single malformed scalar tag (not even a list) must not crash —
    degrade to a one-item list instead of raising.
    """
    wiki_dir = tmp_path / "wiki" / "areas"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    page_path = wiki_dir / "bad-tags.md"
    page_path.write_text(
        "---\n"
        "title: \"Bad Tags\"\n"
        "domain: areas\n"
        "tags: 2026-10-06\n"  # scalar, not a list
        "status: active\n"
        "---\n\n"
        "# Bad Tags\n",
        encoding="utf-8",
    )
    vault = Vault(id="test", path=tmp_path, profile=None)  # type: ignore[arg-type]

    page = vault_ops.read_page(vault, "wiki/areas/bad-tags.md")
    assert page is not None
    assert isinstance(page["tags"], list)
    assert all(isinstance(t, str) for t in page["tags"])
