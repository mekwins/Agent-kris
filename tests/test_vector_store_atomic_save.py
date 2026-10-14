"""
Regression tests for src/vector_store.py:
1. Corrupt/truncated .vectors.json must degrade to an empty index (search
   still works, just with no semantic results) instead of crashing every
   brain_search_tool / brain_compile_tool call.
2. _save() must be atomic (temp file + os.replace()) so a process kill mid-
   write can never leave a half-written, permanently corrupt file behind.

This is the actual root cause behind the recurring
  "Expecting value: line 1 column 9841301 (char 9841300)"
error: the live .vectors.json for the 'work' vault was truncated mid-write at
some point (non-atomic save), and every load since has failed at that exact
byte offset.
"""
import json
from pathlib import Path
from types import SimpleNamespace

from src import vector_store


def _fake_vault(tmp_path: Path):
    vectors_path = tmp_path / ".vectors.json"
    return SimpleNamespace(vectors_path=vectors_path)


def test_load_returns_empty_store_when_file_missing(tmp_path):
    vault = _fake_vault(tmp_path)
    assert vector_store._load(vault) == {"chunks": []}


def test_load_degrades_gracefully_on_corrupt_truncated_file(tmp_path, capsys):
    vault = _fake_vault(tmp_path)
    # Simulate exactly what was found on the live server: a JSON file cut off
    # mid-write (valid JSON up to some point, then nothing).
    vault.vectors_path.write_text('{"chunks": [{"page_slug": "a", "embed', encoding="utf-8")

    result = vector_store._load(vault)

    assert result == {"chunks": []}, (
        "A corrupt vectors file must degrade to an empty index, not raise "
        "and crash the calling tool."
    )
    captured = capsys.readouterr()
    assert "corrupt/truncated" in captured.out, "Should log a warning so the issue is discoverable."


def test_save_is_atomic_and_produces_valid_json(tmp_path):
    vault = _fake_vault(tmp_path)
    store = {"chunks": [{"page_slug": "x", "content": "hello", "embedding": [0.1, 0.2]}]}

    vector_store._save(vault, store)

    # No leftover temp file after a successful save.
    tmp_file = vault.vectors_path.with_suffix(vault.vectors_path.suffix + ".tmp")
    assert not tmp_file.exists(), "Temp file should be renamed away, not left behind."

    assert vault.vectors_path.exists()
    with open(vault.vectors_path, encoding="utf-8") as f:
        loaded = json.load(f)  # must not raise
    assert loaded == store


def test_save_overwrite_never_leaves_old_file_half_written(tmp_path):
    """Simulate: an old (possibly corrupt) file exists, then _save() replaces it.

    Because _save() writes to a .tmp file first and only then os.replace()s it
    over the real path, the real path is NEVER open in truncate/write mode —
    so even if this process were killed mid-write, the OLD file would remain
    fully intact (not half-overwritten), and only the .tmp file would be the
    casualty. This test just confirms the final file is valid + complete
    after a normal save, which is the behavior that matters for callers.
    """
    vault = _fake_vault(tmp_path)
    vault.vectors_path.write_text('{"chunks": []}', encoding="utf-8")

    new_store = {"chunks": [{"page_slug": "y", "content": "world", "embedding": [0.3]}]}
    vector_store._save(vault, new_store)

    with open(vault.vectors_path, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == new_store
