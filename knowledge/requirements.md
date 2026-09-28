# Hermes Knowledge Hub - System Requirements & Tech Specifications

## Environment & Runtime
- **Operating System**: macOS (Darwin arm64 / x86_64) / Linux
- **Python**: Python 3.10+ (managed via `uv` or system venv)
- **Git**: Local Git repository initialized at `~/.hermes-hub`

## Core Python Dependencies
- `fastmcp`: Fast Model Context Protocol server framework
- `mcp`: Official Anthropic/Linux Foundation Model Context Protocol Python SDK
- `pyyaml`: YAML parsing and frontmatter serialization
- `pydantic` & `pydantic-settings`: Schema validation and typing
- `numpy`: Numerical operations and matrix math

## Security & Architecture Specifications
- **No Client Secrets**: Secrets must never be bundled into client-side JS or Edge routes without `server-only`.
- **Database RLS**: All Supabase/PostgreSQL tables require `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`.
- **Data Validation**: Strict Zod validation across all network/RPC boundaries.
