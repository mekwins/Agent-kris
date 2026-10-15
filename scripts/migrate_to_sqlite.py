"""One-time migration: move every vault's `.vectors.json` into the new
SQLite (`vector_store_sqlite`) backend.

Usage:
    uv run python scripts/migrate_to_sqlite.py              # all vaults
    uv run python scripts/migrate_to_sqlite.py --wiki work  # one vault

Does NOT delete the source .vectors.json — run this, verify the reported
counts and a live brain_search_tool call look right, THEN archive/delete
the old JSON file by hand once you're confident (see README note printed
at the end).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import vector_store_sqlite as vs
from src.vaults import available_ids, get_vault


def migrate_one(vault_id: str) -> None:
    vault = get_vault(vault_id)
    json_path = vault.path / ".vectors.json"
    sqlite_path = vault.path / ".vectors.sqlite3"

    print(f"\n=== Vault '{vault.id}' ({vault.path}) ===")
    if not json_path.exists():
        print("  No .vectors.json found — nothing to migrate.")
        return

    before = sqlite_path.stat().st_size if sqlite_path.exists() else 0
    n = vs.migrate_from_json(vault, json_path)
    after = sqlite_path.stat().st_size if sqlite_path.exists() else 0

    print(f"  Migrated {n} chunks.")
    print(f"  JSON size: {json_path.stat().st_size:,} bytes")
    print(f"  SQLite size: {after:,} bytes (was {before:,})")
    print(f"  Verify count: vs.count(vault) = {vs.count(vault)}")
    if n != vs.count(vault):
        print("  WARNING: migrated count != final row count — investigate before trusting this vault's search.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate .vectors.json -> .vectors.sqlite3")
    parser.add_argument("--wiki", help="Migrate only this vault (default: all)")
    args = parser.parse_args()

    ids = [args.wiki] if args.wiki else available_ids()
    if not ids:
        print("No vaults configured in wikis.toml")
        return
    for vault_id in ids:
        migrate_one(vault_id)

    print(
        "\nDone. The old .vectors.json files were NOT deleted — once you've "
        "verified search works correctly against the new SQLite store (e.g. "
        "via a live brain_search_tool call), you can remove them by hand:\n"
        "  find /data/vaults -name '.vectors.json' -delete"
    )


if __name__ == "__main__":
    main()
