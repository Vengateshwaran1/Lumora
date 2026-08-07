# Lumora

Lumora is an autonomous AI software engineering platform: it understands a
GitHub repository, answers questions about it with cited sources (RAG),
plans and implements issues, reviews pull requests, runs tests, and debugs
failures — orchestrated by a supervisor of specialized LangGraph agents.

This repository is currently at **Milestone 1 — Repository Ingestion &
RAG**: connect a repo, clone it, chunk it with AST-aware parsing, embed and
index it, and answer questions about it with file/line citations. Coding
agents, planning agents, PR generation, and auth are not implemented yet —
see [Roadmap](#roadmap) below.

## Architecture Summary

Full design, including diagrams, alternatives considered, and trade-offs
for every decision, lives in
[`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md).
Per-milestone implementation decisions (where a milestone deliberately
simplifies the top-level design, and why) live in their own docs — see
[`docs/architecture/milestone-1-rag-pipeline.md`](docs/architecture/milestone-1-rag-pipeline.md)
for Milestone 1. The short version of the overall architecture:

- **Backend**: FastAPI, layered as Clean Architecture (`api → application →
  domain`, with `infrastructure` implementing ports). Agent orchestration
  runs on LangGraph with a Postgres checkpointer, off the request path, in a
  separate worker pool.
- **Frontend**: React 19 + Vite, feature-based (not layer-based) structure.
  TanStack Query owns all server state; Zustand owns only ephemeral UI
  state.
- **Data**: PostgreSQL (including the code knowledge graph, as edge tables —
  no separate graph DB), Redis (queue + pub/sub + cache), Qdrant (hybrid
  dense + sparse vector search), S3-compatible object storage (MinIO
  locally) for large artifacts.
- **Repo access**: a GitHub App installation, not user OAuth — scoped
  tokens, webhook delivery, org-owned rather than tied to one person.

## Tech Stack

| Layer      | Technology                                                                 |
| ---------- | --------------------------------------------------------------------------- |
| Frontend   | React 19, TypeScript (strict), Vite, Tailwind CSS v4, shadcn/ui, React Router, TanStack Query, Zustand, Framer Motion |
| Backend    | Python 3.12+, uv, FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic v2       |
| AI         | LangGraph, LangChain, OpenAI, Ollama, MCP                                   |
| Data       | PostgreSQL, Redis, Qdrant, MinIO (S3-compatible)                            |
| Infra      | Docker, Docker Compose, GitHub Actions                                      |

## Project Structure

```
lumora/
  apps/
    web/                 # React frontend
    api/                 # FastAPI backend
  packages/
    shared-types/        # Types/constants shared between web and api
  infra/
    docker/               # Dockerfiles
  docs/
    architecture/          # Architecture doc
  docker-compose.yml       # Local dev stack
  .github/workflows/       # CI
```

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with
  Compose v2)
- [Node.js](https://nodejs.org/) 22+ and npm (for host-run frontend dev)
- [uv](https://docs.astral.sh/uv/) (for host-run backend dev — manages its
  own pinned Python 3.12, no separate Python install required)

### Run the full stack with Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

This starts Postgres, Redis, Qdrant, MinIO, the API, and the Vite dev
server, wired together on a compose network with healthchecks gating
startup order.

| Service        | URL                                      |
| -------------- | ----------------------------------------- |
| Web app        | http://localhost:5173                     |
| API            | http://localhost:8000/api/v1/health       |
| MinIO console  | http://localhost:9001                     |
| Qdrant         | http://localhost:6333                     |

Database migrations are **not** run on API startup (see
[ARCHITECTURE.md §12](docs/architecture/ARCHITECTURE.md#12-deployment-architecture)).
Run them explicitly:

```bash
docker compose run --rm migrate
```

> **After changing a dependency file** (`apps/api/uv.lock` or
> `package-lock.json`): `docker compose up --build` alone won't refresh the
> `api_venv` / `web_node_modules` named volumes — they only get seeded from
> the image once, the first time they're created. Drop them first:
> `docker compose down -v` (wipes DB/queue data too) or, to keep app data,
> `docker volume rm lumora_api_venv lumora_web_node_modules`.

### Run services directly on the host (without Docker)

Each app has its own `.env.example` for host-run dev (using `localhost`
instead of the compose service names) — copy it before starting:

**Backend**

```bash
cd apps/api
cp .env.example .env
uv sync
uv run uvicorn lumora_api.main:app --reload
```

**Frontend** (from the repo root — this is an npm workspace)

```bash
cp apps/web/.env.example apps/web/.env.local
npm install
npm run dev --workspace apps/web
```

## Repository Ingestion & RAG

By default, indexing and chat work **with zero setup** — no Ollama, no
model downloads, fully offline beyond cloning the target repo:
`EMBEDDING_PROVIDER=deterministic` (hash-seeded vectors — real, working,
but not semantically meaningful) and `CHAT_PROVIDER=extractive` (a
citation list, not generated prose). This is what `docker compose up`
gives you immediately. See
[milestone-1-rag-pipeline.md](docs/architecture/milestone-1-rag-pipeline.md)
for why.

### Try it

```bash
# Register a (public) repo — this only stores the URL, it doesn't clone yet
curl -X POST http://localhost:8000/api/v1/repositories \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/octocat/Hello-World"}'
# → {"id": "...", "status": "pending", ...}

# Trigger clone + index (runs in the background; poll /status)
curl -X POST http://localhost:8000/api/v1/repositories/<id>/index

curl http://localhost:8000/api/v1/repositories/<id>/status

# Hybrid search — dense + BM25, fused, with file/line citations
curl -X POST http://localhost:8000/api/v1/repositories/<id>/search \
  -H "Content-Type: application/json" \
  -d '{"query": "hello world", "top_k": 5}'

# RAG chat — retrieval + an answer grounded in what was retrieved
curl -X POST http://localhost:8000/api/v1/repositories/<id>/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What does this repo do?"}'
```

### Switching to real Ollama-backed embeddings and chat

1. Install [Ollama](https://ollama.com/) and start it (`ollama serve`, or
   the desktop app — it listens on `localhost:11434` by default).
2. Pull the default models (or set `OLLAMA_EMBEDDING_MODEL` /
   `OLLAMA_CHAT_MODEL` to your own choice):
   ```bash
   ollama pull nomic-embed-text
   ollama pull qwen3
   ```
3. Set `EMBEDDING_PROVIDER=ollama` and `CHAT_PROVIDER=ollama`:
   - **Docker Compose**: add both to your root `.env`, then
     `docker compose up --build` — the API container reaches your host's
     Ollama via `host.docker.internal` automatically (see
     `docker-compose.yml`'s `extra_hosts`).
   - **Host-run dev**: set them in `apps/api/.env` (which already points
     `OLLAMA_BASE_URL` at `http://localhost:11434`).
4. Re-index existing repos (`POST .../index` again) — vectors from the
   deterministic provider aren't compatible with real embeddings, and
   `ensure_collection` sizes the Qdrant collection from whichever
   provider's dimensions it sees first.

Optionally, `RERANKER_PROVIDER=cross_encoder` enables a
sentence-transformers cross-encoder reranking pass — downloads model
weights from Hugging Face on first use, so it's opt-in rather than default
(see the pipeline doc for why).

## Development Workflow

All commands below assume dependencies are installed (`uv sync` in
`apps/api`, `npm install` at the repo root). Backend tests need Postgres
and Qdrant running (`docker compose up -d postgres qdrant` from the repo
root is enough — the API/web containers aren't needed) and migrations
applied (`docker compose run --rm migrate`, or `uv run alembic upgrade
head` from `apps/api` for host-run dev); they do **not** need Ollama —
the suite uses the deterministic embedding provider and mocks Ollama's
HTTP API for the provider-specific unit tests.

| Check              | Backend (`apps/api`)      | Frontend (`apps/web`, run from repo root or with `--workspace apps/web`) |
| ------------------ | -------------------------- | -------------------------------------------------------------------------- |
| Lint                | `uv run ruff check .`      | `npm run lint --workspace apps/web`                                        |
| Format check        | `uv run black --check .`   | `npm run format:check --workspace apps/web`                                |
| Format (write)      | `uv run black .`           | `npm run format --workspace apps/web`                                      |
| Type check          | `uv run mypy .`            | `npm run typecheck --workspace apps/web`                                   |
| Tests               | `uv run pytest`            | —                                                                            |
| Build               | —                           | `npm run build --workspace apps/web`                                       |

These same commands run in CI on every push/PR — see `.github/workflows/`.

### Pre-commit hooks

```bash
pip install pre-commit  # or: uv tool install pre-commit
pre-commit install
```

Runs formatting/lint fixes and file-hygiene checks on staged files before
each commit. The backend hooks invoke `uv` directly (`language: system`),
so `uv` must be on `PATH` — if `uv` was installed via `pip install --user
uv` rather than its standalone installer, that may mean `python -m uv`
works but bare `uv` doesn't; add its install location to `PATH` or install
it via the [standalone installer](https://docs.astral.sh/uv/getting-started/installation/).

## Roadmap

Sequenced by risk retired — see
[ARCHITECTURE.md §14](docs/architecture/ARCHITECTURE.md#14-development-roadmap)
for the full breakdown and verification gates.

- [x] **M0 — Foundations**: monorepo, toolchains, Docker Compose dev stack, CI
- [x] **M1 — Vertical slice**: index one repo → cited Q&A
- [ ] **M2 — Incremental indexing**: webhooks, diff-based re-index
- [ ] **M3 — Planning agent**: issue → structured implementation plan
- [ ] **M4 — Sandboxed execution**: Coding/Test/Debug agents, approval gate
- [ ] **M5 — PR automation**: end-to-end issue → PR flow
- [ ] **M6 — Multi-tenancy**: org/user model, RLS, auth hardening
- [ ] **M7 — Docs generation + cross-session memory**
- [ ] **M8 — Production hardening + scale**

## Engineering Standards

Clean Architecture on the backend, feature-based structure on the frontend,
strict typing on both sides (`mypy --strict`, TypeScript `strict`), no
business logic ahead of the milestone that needs it. See
[ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for the reasoning
behind every structural decision.
