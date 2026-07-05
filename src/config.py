import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing required env var: {key}")
    return val


EMBEDDING_ENDPOINT: str = _require("EMBEDDING_ENDPOINT")
EMBEDDING_API_KEY: str = _require("EMBEDDING_API_KEY")

# Azure AI Foundry endpoint for Claude (replaces direct Anthropic API key)
ANTHROPIC_FOUNDRY_BASE_URL: str = _require("ANTHROPIC_FOUNDRY_BASE_URL")
ANTHROPIC_FOUNDRY_API_KEY: str = _require("ANTHROPIC_FOUNDRY_API_KEY")

# Optional API key — if set, the MCP HTTP server requires x-api-key header
MCP_API_KEY: str | None = os.getenv("MCP_API_KEY") or None

# --- Multi-vault configuration ---------------------------------------------
# Each vault is a directory under VAULTS_ROOT; the registry file lists them.
VAULTS_ROOT: Path = Path(os.getenv("VAULTS_ROOT", "./vaults")).resolve()
WIKIS_CONFIG: Path = Path(os.getenv("WIKIS_CONFIG", "./wikis.toml")).resolve()
DEFAULT_WIKI: str = os.getenv("DEFAULT_WIKI", "work")

EMBEDDING_DIMENSIONS = 1536
DEFAULT_SEARCH_LIMIT = 10
MAX_CHUNK_WORDS = 400
