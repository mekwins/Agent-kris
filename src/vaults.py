"""Multi-vault registry.

A *vault* is a self-describing knowledge base living in its own directory under
VAULTS_ROOT (default ./vaults/<id>). Each vault carries its own profile in a
`.brain/` folder:

    vaults/<id>/
    ├── .brain/
    │   ├── profile.toml   # id, description, domains, note-type schemas
    │   ├── compile.md     # the compile agent's system prompt for THIS vault
    │   └── folders.md     # folder routing rules for THIS vault
    ├── inbox/
    ├── processed/
    ├── wiki/
    ├── sources/
    └── .vectors.json      # per-vault embedding store (gitignored)

The engine code (vault.py, vector_store.py, search.py, agent.py) is generic and
receives a `Vault` object; all per-vault behaviour lives in the profile, so a
new vault = a new directory + profile, with no code changes.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.config import VAULTS_ROOT, WIKIS_CONFIG, DEFAULT_WIKI


# Fallback compile prompt used when a vault ships no .brain/compile.md.
_DEFAULT_COMPILE_PROMPT = """You compile this vault's inbox notes into interlinked wiki pages.
Route factual knowledge to wiki/concepts/, named people to wiki/people/,
projects to wiki/projects/, ongoing areas to wiki/areas/, speculative ideas to
wiki/brainstorm/, and course/book/practice material to wiki/learning/."""

_DEFAULT_FOLDERS_DOC = """Default folders: wiki/concepts, wiki/people, wiki/projects,
wiki/areas, wiki/brainstorm, wiki/learning."""


@dataclass
class VaultProfile:
    """Declarative, per-vault rules loaded from `.brain/`."""

    id: str
    description: str = ""
    domains: list[str] = field(default_factory=list)
    types: dict[str, Any] = field(default_factory=dict)
    compile_prompt: str = _DEFAULT_COMPILE_PROMPT
    folders_doc: str = _DEFAULT_FOLDERS_DOC

    def types_summary(self) -> str:
        """Human-readable note-type schema block for injection into a prompt."""
        if not self.types:
            return ""
        lines = ["## Note types for this vault"]
        for name, spec in self.types.items():
            fields = ", ".join(spec.get("frontmatter", [])) or "(free-form)"
            hint = spec.get("hint", "")
            lines.append(f"- **{name}** — frontmatter: {fields}. {hint}".rstrip())
        return "\n".join(lines)


@dataclass
class Vault:
    """A resolved vault: filesystem paths + loaded profile."""

    id: str
    path: Path
    profile: VaultProfile

    @property
    def vectors_path(self) -> Path:
        return self.path / ".vectors.json"

    @property
    def inbox_dir(self) -> Path:
        return self.path / "inbox"

    @property
    def wiki_dir(self) -> Path:
        return self.path / "wiki"


def _load_profile(vault_id: str, path: Path) -> VaultProfile:
    brain = path / ".brain"
    profile = VaultProfile(id=vault_id)

    toml_path = brain / "profile.toml"
    if toml_path.exists():
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
        profile.description = data.get("description", "")
        profile.domains = data.get("domains", [])
        profile.types = data.get("types", {})

    compile_md = brain / "compile.md"
    if compile_md.exists():
        profile.compile_prompt = compile_md.read_text(encoding="utf-8").strip()

    folders_md = brain / "folders.md"
    if folders_md.exists():
        profile.folders_doc = folders_md.read_text(encoding="utf-8").strip()

    return profile


@lru_cache(maxsize=1)
def _registry() -> dict[str, Any]:
    """Parse wikis.toml. Shape: {default: str, wikis: {id: {path?: str}}}."""
    if not WIKIS_CONFIG.exists():
        return {"default": DEFAULT_WIKI, "wikis": {}}
    with open(WIKIS_CONFIG, "rb") as f:
        data = tomllib.load(f)
    data.setdefault("wikis", {})
    data.setdefault("default", DEFAULT_WIKI or next(iter(data["wikis"]), "default"))
    return data


def _vault_path(vault_id: str, entry: dict[str, Any]) -> Path:
    raw = entry.get("path")
    if raw:
        return Path(raw).expanduser().resolve()
    return (VAULTS_ROOT / vault_id).resolve()


def available_ids() -> list[str]:
    return sorted(_registry()["wikis"].keys())


def default_id() -> str:
    reg = _registry()
    ids = list(reg["wikis"].keys())
    if reg.get("default") in ids:
        return reg["default"]
    return ids[0] if ids else DEFAULT_WIKI


@lru_cache(maxsize=32)
def get_vault(vault_id: str | None = None) -> Vault:
    """Resolve a vault by id (or the default). Raises if unknown."""
    reg = _registry()
    vid = vault_id or default_id()
    if vid not in reg["wikis"]:
        known = ", ".join(available_ids()) or "(none configured)"
        raise KeyError(f"Unknown wiki '{vid}'. Available: {known}")
    path = _vault_path(vid, reg["wikis"][vid])
    return Vault(id=vid, path=path, profile=_load_profile(vid, path))


def list_vaults() -> list[dict[str, Any]]:
    """Metadata for every configured vault — used by brain_list_wikis."""
    out = []
    for vid in available_ids():
        v = get_vault(vid)
        out.append({
            "wiki": vid,
            "description": v.profile.description,
            "domains": v.profile.domains,
            "types": list(v.profile.types.keys()),
            "path": str(v.path),
            "is_default": vid == default_id(),
        })
    return out
