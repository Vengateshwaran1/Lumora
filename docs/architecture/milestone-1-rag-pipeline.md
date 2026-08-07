# Milestone 1 — Repository Ingestion & RAG Pipeline

## Context

Builds the vertical slice from [ARCHITECTURE.md §14](ARCHITECTURE.md#14-development-roadmap)'s
M1: connect a repo → clone → chunk → embed → store → hybrid search → cited
answers. This document records the decisions made while implementing it,
including where implementation deliberately simplifies what the top-level
architecture doc describes, and why. It follows the same format as
ARCHITECTURE.md — decision, alternatives considered, trade-off — scoped to
this milestone rather than repeating it.

No coding/planning agents, PR generation, authentication, or autonomous
execution are implemented — out of scope per the milestone brief, and
because none of them are needed to validate the RAG pipeline itself.

---

## AI provider constraints

**Requirement**: work completely offline except GitHub repo access; prefer
Ollama/Qwen3 and sentence-transformers; stay provider-agnostic so
OpenAI/Anthropic can be added later without touching the pipeline.

This shows up as three abstractions, each with an offline-safe default and
an Ollama-backed real implementation, selected via settings
(`EMBEDDING_PROVIDER`, `CHAT_PROVIDER`, `RERANKER_PROVIDER`):

| Abstraction | Default (zero-config) | Real implementation |
| --- | --- | --- |
| `EmbeddingProvider` (`infrastructure/embeddings/`) | `DeterministicEmbeddingProvider` — hash-seeded pseudo-random vectors | `OllamaEmbeddingProvider` (`/api/embed`, default model `nomic-embed-text`) |
| `ChatProvider` (`infrastructure/llm/`) | `ExtractiveChatProvider` — templates retrieved chunks into a citation list, no model call | `OllamaChatProvider` (`/api/generate`, default model `qwen3`) |
| `Reranker` (`infrastructure/retrieval/reranker/`) | `NoOpReranker` — keeps the fused ranking as-is | `CrossEncoderReranker` (sentence-transformers, opt-in only) |

**Why deterministic-by-default, not Ollama-by-default**: Ollama isn't
installed in every dev/CI environment, and pulling multi-gigabyte model
weights shouldn't be a prerequisite for `docker compose up` producing a
working pipeline. The deterministic provider is not a mock — it's a real,
documented implementation of the same interface (same input text always
produces the same unit-normalized vector, so re-indexing an unchanged chunk
is still correctly a no-op) — it's just not semantically meaningful, so
switching to Ollama is required for real search quality. Alternative
considered: make Ollama the default and require it for `docker compose up`
to fully succeed — rejected, it would mean a first-time user hits a wall
(or a silent multi-GB download) before seeing anything work.

**Why the cross-encoder reranker is opt-in, not the pipeline default**:
`sentence-transformers.CrossEncoder` downloads model weights from Hugging
Face on first use — a second network dependency beyond GitHub, which
directly conflicts with "works completely offline." The import is deferred
into `CrossEncoderReranker.__init__` specifically so that merely having the
package installed (it's a direct dependency, needed for the class to exist
at all) doesn't pull `torch` into every process; only explicitly setting
`RERANKER_PROVIDER=cross_encoder` does. Trade-off accepted: the default
pipeline skips a step ARCHITECTURE.md §5 says meaningfully improves
precision. Revisit once weight-caching/offline-bundling is worth the
complexity.

**Why extractive, not "no /chat until Ollama is set up"**: an endpoint that
only works after extra setup is a worse default than one that gives a
real, useful (if less fluent) answer immediately — a citation list with
file:line locations is often exactly what "cited answer" needs.

---

## Repository ingestion

**Shallow clones (`depth=1`), not full history.** ARCHITECTURE.md §6
describes incremental re-indexing via `git diff <last_sha>..HEAD`. That
needs history depth a shallow clone doesn't have. Instead, correctness is
driven by **content hashing**, not git diff: a file whose SHA-256 hash is
unchanged since the last index is never re-parsed, and a chunk whose hash
already exists for that file is never re-embedded or re-upserted (see
`application/indexing/index_repository.py`'s module docstring). This is
strictly more robust — it doesn't care whether the stored commit SHA is
still reachable — at the cost of hashing every tracked file on every index
run (cheap relative to parsing/embedding).

**File enumeration via `git ls-files`, not a hand-rolled ignore list.**
Gets `.gitignore` and `.git`-exclusion for free, correctly, without
reimplementing gitignore pattern matching. Layered on top: a binary sniff
(NUL byte in the first 8KB — the same heuristic git itself uses) and a
size cap (`MAX_FILE_SIZE_BYTES`), since a tracked file can still be binary
or huge.

**Language detection is a fixed extension table** (`domain/language.py`),
not content sniffing. Sufficient for the six required languages; revisit
only if a language without a reliable 1:1 extension shows up.

**No knowledge graph yet.** ARCHITECTURE.md §8's `symbol_edges` table
(call/import graph) isn't modeled — the milestone brief's metadata list is
chunk-level only (repository, file path, language, symbol, line range,
hash). Extracting call/import relationships is a separate, larger feature
for a later milestone.

**Chunk content is stored in Postgres** (`chunks.content`), not just
metadata — needed for BM25 (which needs the corpus text) and for chat
prompt assembly, and re-reading from disk per query would be fragile
(repo mutates between clone and query) and slow. It's also mirrored into
each chunk's Qdrant payload, so dense hits are self-contained without a
Postgres join — a deliberate storage/query-cost trade-off in favor of
query simplicity.

---

## AST-aware chunking

Chunk by declaration node, not fixed windows: `infrastructure/chunking/`
has one chunker per language family, selected in `registry.py`, with a
fixed-size line-window chunker (`fallback.py`) used only when no parser
exists for a language or the structural chunker finds nothing to split on
— the literal "never use fixed-size chunking unless no parser exists" rule.

- **Python** (`python_chunker.py`): `tree-sitter-python` via
  `tree-sitter-language-pack`. Classes and functions chunk individually;
  a `function_definition` nested inside a `class_definition`'s body is
  classified `method` instead of `function` by checking its ancestor
  chain — both the class *and* its methods become separate chunks
  (deliberate overlap: useful for both "what is this class" and "how does
  this method work" queries).
- **JavaScript/TypeScript/TSX** (`js_ts_chunker.py`): one chunker class,
  three grammar instances. TSX needs tree-sitter-typescript's separate
  `tsx` grammar for JSX support — plain `typescript` doesn't parse JSX;
  JavaScript's grammar handles JSX natively, so `.jsx` doesn't need a
  variant. Handles `export`-wrapped declarations (unwraps to classify the
  inner declaration, but keeps the *outer* node's span so the `export`
  keyword stays in the chunk) and `const x = (...) => ...` arrow functions
  (detected by walking `variable_declarator` nodes for an `arrow_function`
  value) — neither is a plain top-level declaration type, so both needed
  explicit handling beyond a simple node-type lookup table.
- **Markdown** (`markdown_chunker.py`): sections split at heading
  boundaries (`^#{1,6}\s`). Not a tree-sitter grammar — heading-splitting
  is simpler and equally not-fixed-size; a tree-sitter-markdown dependency
  wasn't justified for this.
- **JSON/YAML** (`json_chunker.py`, `yaml_chunker.py`): split by top-level
  key, with line ranges found by locating each key's token in source order
  (YAML matches at column 0 specifically to avoid confusing a top-level
  key with a same-named nested key). Falls back to one whole-file chunk for
  non-object JSON/YAML (arrays, scalars) or when key positions can't be
  located (e.g. minified JSON).

Field names and node types were verified empirically against the actual
installed grammars before writing the chunkers (see the exploration
scripts referenced in the PR/session notes) rather than assumed from
tree-sitter grammar documentation, which drifts across grammar versions.

---

## Retrieval

`application/search/search_repository.py` implements hybrid retrieval per
ARCHITECTURE.md §5:

1. **Dense**: query embedded via the active `EmbeddingProvider`, searched
   against Qdrant filtered by `repository_id` payload (single collection
   for all repos, per ARCHITECTURE.md §8 — not one collection per repo).
2. **BM25** (`infrastructure/retrieval/bm25_index.py`): built fresh per
   search from the repository's chunk corpus (already loaded from
   Postgres for the fusion step below), using `rank_bm25`. No persisted
   index — correct and fast enough at Milestone 1 scale (one repo,
   hundreds to low-thousands of chunks); revisit with a
   cached/persisted index if corpus size or query volume grows enough for
   rebuild cost to matter.
3. **Fusion** (`fusion.py`): Reciprocal Rank Fusion, not a weighted score
   sum — dense cosine similarity and BM25 scores aren't on a comparable
   scale, so RRF's rank-position-based combination is the correct tool,
   not a workaround.
4. **Rerank**: the active `Reranker` (no-op by default; see above).

`/chat` (`application/chat/chat_with_repository.py`) composes
`search_repository` rather than duplicating retrieval — chat is "search,
then generate," not a parallel pipeline.

---

## Indexing execution model

**Runs as a FastAPI `BackgroundTask`, not the Arq/Celery worker pool**
ARCHITECTURE.md §7/§12 describe. Endorsed scope decision, not a
shortcut: the full worker pool exists to support durable, resumable,
checkpointed, human-in-the-loop-interruptible execution — properties that
matter once agent orchestration (M3+) needs to pause a multi-step run for
approval. A bounded indexing job with no interruption points doesn't need
any of that yet. Revisit when M3/M4 introduce the LangGraph checkpointer
and the worker pool becomes necessary anyway — indexing can move onto it
then rather than justifying its own infrastructure now.

**Commits per file, not one transaction for the whole indexing run.** A
crash or error partway through a large repo preserves everything indexed
so far instead of losing it to a rollback, and `/status`'s running counts
reflect real progress instead of jumping from 0 to N at the end. Every
exit path (success, missing repository, clone failure, anything else)
writes a terminal `status` — `ready` or `failed` + `error_message` — so
`/status` never reports a stale `indexing` forever.

**Known consistency caveat**: Postgres and Qdrant are two separate
datastores with no distributed transaction between them. If the process
dies between a Qdrant upsert/delete and the following Postgres commit,
the two can briefly disagree for that one file. Out of scope for M1 — an
outbox/reconciliation pattern would fix it if it becomes a real problem at
higher indexing volume or failure rates.

---

## Testing strategy

- **Chunkers, BM25, RRF fusion, deterministic embeddings**: pure unit
  tests, no I/O.
- **`OllamaEmbeddingProvider` / `OllamaChatProvider`**: unit-tested against
  `httpx.MockTransport`, not a live Ollama server — verifies the exact
  request/response contract without requiring Ollama to be installed
  anywhere tests run, including CI.
- **Git ingestion**: tested against a real local git repository fixture
  (`tests/conftest.py`'s `sample_repo_path`) — a real `git clone` from a
  local path, not a mock, but no network access.
- **Indexing/search/chat integration tests**: run against real Postgres
  and Qdrant (a throwaway collection per test) with the deterministic
  embedding provider — this is the actual Milestone 1 gate from
  ARCHITECTURE.md §5's verification section: clone → chunk → embed →
  store → retrieve → cite, genuinely exercised end to end.
- **CI** (`.github/workflows/backend.yml`): Postgres and Qdrant run as
  service containers; `EMBEDDING_PROVIDER=deterministic` and
  `CHAT_PROVIDER=extractive` so the full suite runs without Ollama.

**What's explicitly unverified in this environment**: real Ollama
embedding and chat generation, and the cross-encoder reranker (both
require model downloads / a running Ollama instance not available here).
The abstractions and the offline paths through them are fully tested; the
Ollama-backed implementations are tested at the HTTP-contract level only.

---

## API

```
POST /api/v1/repositories                    register (no clone yet)
POST /api/v1/repositories/{id}/index          trigger clone + index (background)
GET  /api/v1/repositories/{id}/status         status, counts, error
POST /api/v1/repositories/{id}/search         hybrid search, no LLM
POST /api/v1/repositories/{id}/chat           RAG Q&A with citations
```

`POST /repositories` only registers a repo (stores the URL, derives a
name); it does not clone. Cloning/indexing is a separate, explicit,
independently-retriable step (`POST .../index`) — registration and "do the
expensive work" are different failure domains and shouldn't be coupled.

---

## Known gap: no retrieval eval harness

ARCHITECTURE.md §5 and §14 both call for a curated `(query, expected
file/chunk)` regression suite as part of Milestone 1, gating M2 — "without
this, there's no way to tell whether a retrieval change is an improvement
or a regression." This was not built. The integration tests exercise the
pipeline end-to-end (clone → chunk → embed → retrieve → cite) and confirm
it *works*, but they don't measure retrieval *quality* against a curated
ground truth, and with the deterministic embedding provider as the CI
default there's no meaningful precision/recall signal to gate on yet
anyway (that only becomes meaningful once Ollama-backed embeddings are the
baseline being evaluated). Flagging explicitly rather than silently
dropping it: this should be built before tuning chunking/embedding/
retrieval further, per the architecture doc's own reasoning.
