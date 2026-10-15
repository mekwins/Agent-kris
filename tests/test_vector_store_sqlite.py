"""Regression tests for the SQLite/sqlite-vec vector store, replacing the
flat-JSON `.vectors.json` store.

Covers: chunking parity (unchanged logic, moved file), upsert/search/
remove_page round-trip, scope filtering via the vec0 partition key, cosine
similarity score correctness, and migrate_from_json() against a realistic
multi-chunk fixture.
"""
import math
from types import SimpleNamespace

import pytest

from src import vector_store_sqlite as vs


def _vault(tmp_path):
    return SimpleNamespace(id="test", path=tmp_path, profile=None)


def _unit(vec):
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec]


def test_upsert_and_search_roundtrip(tmp_path):
    vault = _vault(tmp_path)
    chunks = [
        {"page_slug": "a", "content": "hello world", "section": "intro", "tags": ["x"], "domain": "areas"},
    ]
    embeddings = [_unit([1.0, 0.0, 0.0])]
    vs.upsert(vault, "a", chunks, embeddings)

    results = vs.search(vault, _unit([1.0, 0.0, 0.0]), limit=5)
    assert len(results) == 1
    assert results[0]["page_slug"] == "a"
    assert results[0]["content"] == "hello world"
    assert results[0]["tags"] == ["x"]
    assert results[0]["score"] == pytest.approx(1.0, abs=1e-4)


def test_search_scope_filter_uses_partition_key(tmp_path):
    vault = _vault(tmp_path)
    vs.upsert(
        vault, "a",
        [{"page_slug": "a", "content": "c1", "section": "", "tags": [], "domain": "areas"}],
        [_unit([1.0, 0.0, 0.0])],
    )
    vs.upsert(
        vault, "b",
        [{"page_slug": "b", "content": "c2", "section": "", "tags": [], "domain": "people"}],
        [_unit([1.0, 0.0, 0.0])],
    )

    all_results = vs.search(vault, _unit([1.0, 0.0, 0.0]), scope="all", limit=10)
    assert {r["page_slug"] for r in all_results} == {"a", "b"}

    scoped = vs.search(vault, _unit([1.0, 0.0, 0.0]), scope="areas", limit=10)
    assert {r["page_slug"] for r in scoped} == {"a"}


def test_upsert_replaces_existing_page_chunks(tmp_path):
    vault = _vault(tmp_path)
    vs.upsert(
        vault, "a",
        [{"page_slug": "a", "content": "old", "section": "", "tags": [], "domain": "areas"}],
        [_unit([1.0, 0.0, 0.0])],
    )
    assert vs.count(vault) == 1

    vs.upsert(
        vault, "a",
        [{"page_slug": "a", "content": "new1", "section": "", "tags": [], "domain": "areas"},
         {"page_slug": "a", "content": "new2", "section": "", "tags": [], "domain": "areas"}],
        [_unit([1.0, 0.0, 0.0]), _unit([0.0, 1.0, 0.0])],
    )
    # old single chunk replaced by exactly the two new ones, not appended
    assert vs.count(vault) == 2
    contents = {r["content"] for r in vs.search(vault, _unit([1.0, 0.0, 0.0]), limit=10)}
    assert contents == {"new1", "new2"}


def test_remove_page(tmp_path):
    vault = _vault(tmp_path)
    vs.upsert(
        vault, "a",
        [{"page_slug": "a", "content": "c1", "section": "", "tags": [], "domain": "areas"}],
        [_unit([1.0, 0.0, 0.0])],
    )
    vs.upsert(
        vault, "b",
        [{"page_slug": "b", "content": "c2", "section": "", "tags": [], "domain": "areas"}],
        [_unit([0.0, 1.0, 0.0])],
    )
    assert vs.count(vault) == 2

    vs.remove_page(vault, "a")
    assert vs.count(vault) == 1
    remaining = vs.search(vault, _unit([1.0, 0.0, 0.0]), limit=10)
    assert {r["page_slug"] for r in remaining} == {"b"}


def test_cosine_similarity_ordering(tmp_path):
    """A chunk pointing in the exact query direction must rank above one
    that's merely similar, which must rank above an orthogonal one."""
    vault = _vault(tmp_path)
    vs.upsert(
        vault, "exact",
        [{"page_slug": "exact", "content": "exact", "section": "", "tags": [], "domain": "areas"}],
        [_unit([1.0, 0.0, 0.0])],
    )
    vs.upsert(
        vault, "similar",
        [{"page_slug": "similar", "content": "similar", "section": "", "tags": [], "domain": "areas"}],
        [_unit([0.9, 0.1, 0.0])],
    )
    vs.upsert(
        vault, "orthogonal",
        [{"page_slug": "orthogonal", "content": "orthogonal", "section": "", "tags": [], "domain": "areas"}],
        [_unit([0.0, 1.0, 0.0])],
    )

    results = vs.search(vault, _unit([1.0, 0.0, 0.0]), limit=10)
    slugs_in_order = [r["page_slug"] for r in results]
    assert slugs_in_order == ["exact", "similar", "orthogonal"]
    assert results[0]["score"] > results[1]["score"] > results[2]["score"]


def test_migrate_from_json(tmp_path):
    import json

    vault = _vault(tmp_path)
    json_path = tmp_path / ".vectors.json"
    json_path.write_text(
        json.dumps(
            {
                "chunks": [
                    {
                        "page_slug": "p1",
                        "content": "content one",
                        "section": "intro",
                        "tags": ["t1", "t2"],
                        "domain": "areas",
                        "embedding": _unit([1.0, 0.0, 0.0]),
                    },
                    {
                        "page_slug": "p2",
                        "content": "content two",
                        "section": "",
                        "tags": [],
                        "domain": "people",
                        "embedding": _unit([0.0, 1.0, 0.0]),
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    migrated = vs.migrate_from_json(vault, json_path)
    assert migrated == 2
    assert vs.count(vault) == 2

    results = vs.search(vault, _unit([1.0, 0.0, 0.0]), limit=10)
    assert results[0]["page_slug"] == "p1"
    assert results[0]["tags"] == ["t1", "t2"]


def test_migrate_from_json_missing_file_returns_zero(tmp_path):
    vault = _vault(tmp_path)
    assert vs.migrate_from_json(vault, tmp_path / "does-not-exist.json") == 0


def test_chunk_content_unchanged_logic(tmp_path):
    """chunk_content() must behave identically to the old JSON-store version
    — only storage changed, not chunking semantics."""
    content = "## Intro\nShort section.\n\n## Details\n" + " ".join(["word"] * 600)
    chunks = vs.chunk_content(content, page_slug="p", tags=["t"], domain="areas")
    assert len(chunks) >= 2
    assert all(c["page_slug"] == "p" for c in chunks)
    assert all(c["domain"] == "areas" for c in chunks)
