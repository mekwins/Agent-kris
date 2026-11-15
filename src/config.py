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
# Gateway (OpenAI-compatible /v1/embeddings): falls back to LLM_API_KEY so one
# gateway key covers both. EMBEDDING_MODEL / EMBEDDING_DIMENSIONS are sent in
# the request body when set (Azure deployment URLs don't need them).
EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY") or os.getenv("LLM_API_KEY") or _require("EMBEDDING_API_KEY")
EMBEDDING_MODEL: str | None = os.getenv("EMBEDDING_MODEL") or None

# --- Compile agent LLM endpoint (Anthropic Messages API compatible) ---------
# Preferred: the Nexteer AI Gateway (LLM_BASE_URL / LLM_API_KEY / LLM_MODEL).
# Fallback: the legacy Azure AI Foundry vars, so existing deployments keep
# working until the gateway secrets are set.
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL") or _require("ANTHROPIC_FOUNDRY_BASE_URL")
LLM_API_KEY: str = os.getenv("LLM_API_KEY") or _require("ANTHROPIC_FOUNDRY_API_KEY")
LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
# Optional gateway AI Orchestration profile (sent as X-AI-Profile header).
LLM_PROFILE: str | None = os.getenv("LLM_PROFILE") or None

# Optional API key — if set, the MCP HTTP server requires x-api-key header
MCP_API_KEY: str | None = os.getenv("MCP_API_KEY") or None

# --- Multi-vault configuration ---------------------------------------------
# Each vault is a directory under VAULTS_ROOT; the registry file lists them.
VAULTS_ROOT: Path = Path(os.getenv("VAULTS_ROOT", "./vaults")).resolve()
WIKIS_CONFIG: Path = Path(os.getenv("WIKIS_CONFIG", "./wikis.toml")).resolve()
DEFAULT_WIKI: str = os.getenv("DEFAULT_WIKI", "work")

EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
DEFAULT_SEARCH_LIMIT = 10
MAX_CHUNK_WORDS = 400
