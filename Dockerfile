# Brain MCP server — container image for fly.io (or any Docker host).
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# git is required: the compile agent shells out to `git` to version the vault,
# and FileNotFoundError from a missing binary would not be caught otherwise.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (cached layer) using the lockfile.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Application code + vault registry. Vault *data* is NOT baked into the image;
# the entrypoint clones the brain-vaults repo onto the volume at boot (see
# docker-entrypoint.sh) so GitHub stays the single source of truth.
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY wikis.toml ./wikis.toml
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN chmod +x ./docker-entrypoint.sh

# Runtime configuration (secrets are provided via `fly secrets set`).
ENV HOST=0.0.0.0 \
    PORT=8080 \
    VAULTS_ROOT=/data/vaults \
    WIKIS_CONFIG=/app/wikis.toml \
    PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "-m", "src.server", "--transport", "sse"]
