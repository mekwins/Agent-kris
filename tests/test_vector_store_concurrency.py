"""
Regression tests for the concurrent-write corruption found live in production:

Two processes (a live brain_compile_tool run embedding a newly-written wiki
page, and a separate `scripts/index_vault.py` full-rebuild run) both called
vector_store.upsert() around the same moment. Before this fix, upsert()'s
_save() wrote to a SHARED FIXED temp filename (".vectors.json.tmp") with no
locking — both processes opened that same temp path, truncated it, and wrote
into it concurrently, interleaving their JSON output byte-for-byte before
os.replace() ever ran. The result was a literal mid-file corruption:

    Expecting ',' delimiter: line 1 column 4428838 (char 4428837)

(As distinct from the earlier, unrelated truncation-at-EOF corruption fixed
in the first vector_store.py commit, where a single process's write was cut
off by a kill/restart.)

The fix: (1) each _save() call writes to a per-process+random temp filename,
so two processes can never truncate/clobber the same temp file, and
(2) upsert()/remove_page() hold a cross-process fcntl.flock() for their
entire read-modify-write cycle, so even with unique temp names, two
concurrent upserts can't produce a lost update from interleaved read-then-write
ordering.
"""
import json
import os
import threading
import time
from pathlib import Path
from types import SimpleNamespace

from src import vector_store


def _fake_vault(tmp_path: Path):
    vectors_path = tmp_path / ".vectors.json"
    return SimpleNamespace(vectors_path=vectors_path)


def test_save_uses_unique_temp_filename_per_call(tmp_path):
    """Two _save() calls must never target the same temp path."""
    vault = _fake_vault(tmp_path)
    seen_tmp_names = set()

    # Monkeypatch os.replace to capture the temp path each _save() uses,
    # without actually needing two real concurrent processes.
    original_replace = os.replace

    def spy_replace(src, dst):
        seen_tmp_names.add(str(src))
        return original_replace(src, dst)

    import src.vector_store as vs_module
    vs_module.os.replace = spy_replace
    try:
        vector_store._save(vault, {"chunks": []})
        vector_store._save(vault, {"chunks": []})
    finally:
        vs_module.os.replace = original_replace

    assert len(seen_tmp_names) == 2, (
        "Two _save() calls produced the same temp filename — this is exactly "
        "the mechanism that caused a real production corruption "
        "(Expecting ',' delimiter mid-file) when two processes wrote "
        "concurrently to a shared fixed temp path."
    )


def test_concurrent_upserts_do_not_corrupt_the_file(tmp_path):
    """Simulate two 'processes' (threads racing on the same vault) upserting
    different pages concurrently. The final file must always be valid,
    complete JSON — never a byte-interleaved corruption — and must contain
    both pages' chunks (no silently lost update), because upsert() now holds
    an exclusive lock for its entire read-modify-write cycle.
    """
    vault = _fake_vault(tmp_path)
    vector_store._save(vault, {"chunks": []})  # seed an existing, valid file

    errors = []

    def upsert_page(slug: str, delay: float):
        try:
            time.sleep(delay)  # stagger starts to encourage interleaving
            vector_store.upsert(
                vault,
                page_slug=slug,
                chunks=[{"page_slug": slug, "content": f"content for {slug}", "section": "", "tags": [], "domain": "test"}],
                embeddings=[[0.1, 0.2, 0.3]],
            )
        except Exception as exc:  # pragma: no cover - surfaced via errors list
            errors.append(exc)

    threads = [
        threading.Thread(target=upsert_page, args=(f"page-{i}", 0.01 * (i % 3)))
        for i in range(8)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, f"upsert() raised under concurrent access: {errors}"

    # The file must be valid, parseable JSON (the whole point of this test).
    with open(vault.vectors_path, encoding="utf-8") as f:
        store = json.load(f)  # must not raise JSONDecodeError

    slugs_present = {c["page_slug"] for c in store["chunks"]}
    assert slugs_present == {f"page-{i}" for i in range(8)}, (
        "Some concurrent upserts were lost — expected all 8 pages' chunks "
        "to be present since each upsert() now holds the lock for its full "
        "read-modify-write cycle."
    )


def test_no_leftover_lock_file_blocks_future_access(tmp_path):
    """The .lock file is a coordination file, not vault data — a leftover
    lock file (from a crashed process) must not prevent future upserts: the
    lock is released on process exit either way (flock is tied to the fd),
    and a fresh process can still open + lock the same lock file.
    """
    vault = _fake_vault(tmp_path)
    vector_store._save(vault, {"chunks": []})

    vector_store.upsert(
        vault,
        page_slug="a",
        chunks=[{"page_slug": "a", "content": "x", "section": "", "tags": [], "domain": "test"}],
        embeddings=[[0.1]],
    )
    # A second, independent upsert call must still succeed without hanging.
    vector_store.upsert(
        vault,
        page_slug="b",
        chunks=[{"page_slug": "b", "content": "y", "section": "", "tags": [], "domain": "test"}],
        embeddings=[[0.2]],
    )

    with open(vault.vectors_path, encoding="utf-8") as f:
        store = json.load(f)
    assert {c["page_slug"] for c in store["chunks"]} == {"a", "b"}
