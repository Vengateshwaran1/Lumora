# Milestone 2 — Incremental Indexing + GitHub Webhooks

## Context

Builds the vertical slice from [ARCHITECTURE.md §14](ARCHITECTURE.md#14-development-roadmap)'s
M2: keep indexed repository knowledge synchronized with GitHub without a
full re-index on every push. Follows the same format as
[milestone-1-rag-pipeline.md](milestone-1-rag-pipeline.md) — decision,
alternatives considered, trade-off — scoped to this milestone.

```
GitHub Push → Webhook → Verify HMAC → Deduplicate delivery
  → Identify repo + commit SHA → Compare with last_indexed_sha
  → Git diff → Re-index only affected files
  → Update Postgres → Update Qdrant → Update index status
  → Publish progress events (SSE, best-effort)
```

---

## Deviations from the milestone brief, and why

**§7 symbol graph updates — not applicable.** M1 never modeled
`symbols`/`symbol_edges` (`infrastructure/models.py`'s module docstring
records this as a deliberate deferral). There is no graph to go stale, so
there's nothing to update. Building extraction now would be a larger
feature than the rest of this milestone combined; it belongs with whichever
later milestone actually needs call/import graph queries.

**§8 `org_id` on Qdrant points — not applicable.** No tenancy model exists
until M6 (RLS, org/user). Points continue to carry `repository_id`
(unchanged key name — the payload index and `search()`'s filter are built
on it) plus two new fields: `file_id` and `content_hash`, additive only.

**Route prefix stays `/repositories`, not `/repos`.** M1 already
established `/api/v1/repositories`; this milestone adds `GET /{id}`,
`GET /{id}/index-status`, and `POST /{id}/reindex` under that same prefix
rather than standing up a second prefix for one resource.

**Diff source is local git (`git diff --name-status -M`), not the GitHub
Compare API.** See [Incremental diff algorithm](#incremental-diff-algorithm)
below — this is the decision with the most downstream consequences in the
milestone, so it gets its own section rather than a one-line note here.

**The worker pool arrives one milestone earlier than M1's doc predicted.**
M1's `index_repository` runs as a FastAPI `BackgroundTask`, explicitly
scoped that way because nothing yet needed durable/resumable execution.
This milestone's own requirement — "never index inside the HTTP request"
for the webhook path — forces the Redis-queued worker pool
(ARCHITECTURE.md §7/§12) into existence now. Once it exists, the manual
`POST /{id}/index` trigger stays on `BackgroundTasks` (unchanged, still
correct for a bounded, uninterruptible job) but the new
`POST /{id}/reindex` alias and the webhook path both go through the
worker — see [Execution model](#execution-model).

**CI stays Redis-free.** `JobQueue` and `EventPublisher` are ports
(`application/jobs/`); the webhook and worker tests use an in-process fake
queue and invoke the worker's task functions directly, the same pattern
M1 used for `OllamaEmbeddingProvider`/`OllamaChatProvider` (HTTP-contract
tests against `httpx.MockTransport`, not a live server). `.github/workflows/backend.yml`
keeps its Postgres + Qdrant service containers only.

---

## GitHub webhook endpoint

`POST /webhooks/github` (`api/webhooks.py`) — deliberately outside
`/api/v1`, matching ARCHITECTURE.md §10's API list (GitHub calls this path
directly; it isn't part of the versioned frontend contract).

Request handling, in order:

1. **Read the raw body** (`await request.body()`) before any JSON
   parsing — signature verification needs the exact bytes GitHub signed,
   not a re-serialization of a parsed payload (which can differ in key
   order/whitespace and would make every signature check fail).
2. **Verify `X-Hub-Signature-256`** (`domain/webhook_security.py`):
   HMAC-SHA256 over the raw body, keyed with `GITHUB_WEBHOOK_SECRET`,
   compared with `hmac.compare_digest`. **Fails closed** — an empty/unset
   secret rejects every request rather than skipping verification; a
   missing or malformed header is rejected the same way as a wrong one.
3. **Require `X-GitHub-Delivery` and `X-GitHub-Event`.** Missing either
   is a 400 — there's nothing correct to do without them.
4. **Insert into `webhook_deliveries`, dedup by the UNIQUE constraint.**
   See [Deduplication](#deduplication) below.
5. **Unsupported event → acknowledge, don't process.** Only `push` runs
   the indexing path; anything else (issues, PRs, ...) is marked
   `ignored` and answered 200 — GitHub should never see a webhook it sent
   correctly treated as an error.
6. **Parse the push payload** (`application/webhooks/schemas.py` — a
   deliberately small subset of GitHub's actual payload, `ref`, `before`,
   `after`, `deleted`, `repository.{id,full_name,default_branch}`,
   optional `sender`). A payload that fails to parse marks the delivery
   `failed` and returns 400.
7. **Decide + enqueue** (`application/webhooks/handle_github_webhook.py`):
   branch/tag/deletion filtering, repository lookup, and — on a match —
   `job_queue.enqueue_incremental_index(...)`. This function has no
   FastAPI/HTTP dependency, so it's unit-tested directly.
8. **Always return fast.** Every path returns within the request/response
   cycle; the only thing that happens after the webhook responds is a
   background job picking up the enqueued work.

### Push event filtering

- `deleted: true` (branch deletion push) → ignored.
- `ref` not under `refs/heads/` (i.e. a tag push, `refs/tags/...`) →
  ignored.
- Repository not found by `github_repo_id` (preferred) or case-insensitive
  `full_name` (fallback, for repos M1 registered by URL only and never
  seen a webhook for yet) → ignored, logged, still 200 (no information
  leak about which repos Lumora tracks).
- Branch doesn't match the tracked branch (`repository.default_branch`,
  falling back to the payload's `repository.default_branch` for a repo
  that's never been indexed yet, so `default_branch` is still `NULL`) →
  ignored.
- Otherwise → enqueue.

On a match, `github_repo_id`/`full_name`/`default_branch` are
opportunistically backfilled onto the `Repository` row if unset — this is
what lets a repo registered in M1 by plain URL (`POST /repositories
{"url": ...}`, no GitHub App installation) start responding to webhooks
the first time GitHub actually sends one, without a separate "connect via
GitHub App" flow that this milestone doesn't build.

---

## Deduplication

`webhook_deliveries.github_delivery_id` is `UNIQUE` — that constraint, not
application logic, is what makes dedup race-safe. Two concurrent requests
for the same redelivered `X-GitHub-Delivery` both attempt an insert;
exactly one commits, the other hits `IntegrityError`, which the handler
catches, rolls back, logs "already processed", and returns 200. There is
no read-then-write window because there's no read — the insert itself is
the atomic check.

```
repository POST 1 ─┐
                    ├─→ INSERT github_delivery_id (unique) ─→ one wins, one IntegrityErrors
repository POST 2 ─┘
```

---

## Incremental diff algorithm

**Base SHA comes from `repository.last_indexed_commit` in Postgres, not
the webhook payload's `before` field.** This is the single most important
correctness decision in the milestone:

- `before` is all-zeros on branch creation.
- `before` is not necessarily an ancestor of `after` after a force-push.
- Using the DB's last-indexed commit instead of the webhook's `before`
  makes the job **self-healing**: if a prior delivery was dropped, or a
  prior job died partway through, the next push still diffs from the true
  last-indexed state — no work is silently skipped, and nothing needs a
  manual reconciliation step.
- If `after_sha == last_indexed_commit` already, the job is a no-op —
  this is the concrete mechanism behind "the same commit queued twice
  must not corrupt the index" (§9 of the milestone brief).
- If there's no prior indexed commit (repo never indexed) or no local
  clone yet, this **falls back to a full `index_repository` run** —
  correctness over cleverness; there's nothing to diff against.

**Diff source is local git, not the GitHub Compare API.**
`GitService.fetch_commit` (`infrastructure/vcs/git_service.py`) fetches
exactly the two commits a push diff needs:

```bash
git fetch origin <base_sha> --depth=1
git fetch origin <after_sha> --depth=1
git diff --name-status -M <base_sha> <after_sha>
```

GitHub.com allows fetching an arbitrary reachable commit SHA this way
(`uploadpack.allowReachableSHA1InWant`, on by default) — verified
empirically against `octocat/Hello-World` while building this, not
assumed. `-M` is what makes git report a delete+add pair as a single
rename instead of two unrelated entries. Changed file **content** is read
directly from the git object store (`git show <sha>:<path>`), not via a
working-tree checkout — no `reset --hard` of the whole repo, so a small
push touches a small amount of I/O regardless of repo size.

This was chosen over the GitHub Compare API for one deciding reason: it
lets the integration test for this exact code path run against a local
git fixture with zero GitHub credentials (milestone brief §14 — "do not
require real GitHub credentials for the test suite"), the same pattern M1
used for its git ingestion tests. A Compare-API path is a reasonable
future addition behind the same interface for repos where local history
isn't available (shallow clones missing the base commit, cross-fork
diffs) — not needed yet.

**Two real bugs found and fixed building this** (both would have silently
broken "unchanged content is never re-embedded" for real users, so
recorded here rather than only in commit history):

1. **`core.autocrlf`.** On a machine with autocrlf enabled, a working-tree
   read (full index) and a `git show` read (incremental index, which
   never applies checkout filters) hash the *same* committed content
   differently. Fixed by cloning with `-c core.autocrlf=false` —
   Lumora's clones are read-only, so there's no reason to want
   OS-native line endings on checkout.
2. **GitPython's stdout newline stripping.** `Git.execute(...)` strips a
   trailing newline from captured stdout by default
   (`strip_newline_in_stdout=True`), which silently truncates blob
   content read via `git show` by one byte for any file ending in `\n`
   (nearly all of them) — hashing differently from the same content read
   off the working tree. Fixed by passing `strip_newline_in_stdout=False`
   explicitly in `GitService.read_blob`.

Both were caught by the integration test in
`tests/application/test_incremental_index_repository.py`, which asserts a
rename with unchanged content produces zero new embeddings and the exact
same Qdrant point IDs before and after — not just "the status code was
200."

### Per-file handling

| git status | Handling |
| --- | --- |
| Added / Modified | Read blob at `after_sha`. If content hash matches the existing `IndexedFile.content_hash`, skip (git can report a change — e.g. a mode bit — with byte-identical content). Otherwise chunk + embed only chunks whose *chunk-level* content hash is new (`application/indexing/file_indexer.py::index_file_content`, shared with the full-index path). |
| Deleted | Delete the `IndexedFile` row (cascades to its `Chunk` rows) and the matching Qdrant points. |
| Renamed, content unchanged | Update `IndexedFile.path`, every `Chunk.file_path`, and the Qdrant payload's `file_path` — **no re-embedding**, since nothing about the content changed (`file_indexer.py::rename_file_path`, backed by the new `QdrantVectorStore.set_payload`). |
| Renamed, content changed | Same as Modified, but reusing the existing `file_id`/row rather than delete+recreate. |
| Renamed → unsupported extension | Treated as a delete. |
| Renamed, old path was never indexed (was binary/oversized/unsupported) | Treated as an add. |

**Path safety** (`domain/file_filter.py::is_safe_relative_path`): diff
paths come from a git diff on the pushed commit, not from `git ls-files`
on a trusted checkout — reject `..`, a leading `/`, a leading `~`, or an
empty segment before the path is used to key any Postgres row or Qdrant
payload.

**Per-repository advisory lock** (`pg_advisory_lock(hashtext(:repo_id))`,
held for the whole incremental run, session-scoped so it survives the
per-file commits inside the loop): two pushes seconds apart would
otherwise enqueue two overlapping jobs writing the same
`IndexedFile`/`Chunk` rows concurrently.

**Per-file fault isolation**: each diff entry's processing is wrapped
individually — a malformed file that fails to parse/chunk/embed is
recorded in `IncrementalIndexStats.errors` and logged, and the job
continues with the rest of the push rather than failing the whole run
(milestone brief §12 — "a single malformed source file should not
necessarily destroy the entire indexing job").

---

## Execution model

Both full and incremental indexing move onto an arq worker pool, backed
by Redis (`workers/settings.py`, `workers/tasks.py`). Why arq over Celery
(ARCHITECTURE.md §1 names either as acceptable): asyncio-native, matching
the rest of the backend's stack, and the project already depends on Redis
for the queue role — no new datastore.

```
POST /webhooks/github ──enqueue──► Redis ──dequeue──► arq worker
                                                          │
                                          incremental_index_repository()
                                                          │
                                          Postgres + Qdrant + progress events
```

- `application/jobs/queue.py::JobQueue` — the port the webhook handler and
  `POST /{id}/reindex` depend on. Real implementation:
  `infrastructure/jobs/arq_queue.py::ArqJobQueue`. Test implementation:
  `tests/fakes.py::FakeJobQueue`, an in-process recorder.
- `application/jobs/events.py::EventPublisher` — fire-and-forget Redis
  pub/sub progress events, published from *inside*
  `incremental_index_repository` (`index.files.discovered`,
  `index.file.completed`) and from the worker task wrapper
  (`index.started`, `index.completed`, `index.failed`); `index.queued` is
  published by `ArqJobQueue` itself at enqueue time, since `ArqRedis`
  already *is* a Redis client.
- **Idempotency**: the same commit queued twice is a no-op (see
  [Incremental diff algorithm](#incremental-diff-algorithm) above) —
  this is what makes at-least-once delivery + at-least-once job
  processing safe without a separate idempotency-key mechanism.
- **`POST /{id}/reindex` always runs a full index**, not incremental — a
  user pressing "re-index" wants a known-good baseline, and
  `index_repository`'s content hashing already means an unchanged repo
  re-run costs a git fetch + a per-file hash compare, not a re-embed of
  everything. Incremental jobs are reserved for the case that actually
  needs the cheaper path: a webhook-driven push where the prior indexed
  commit is known. `POST /{id}/index` (M1's original endpoint) is
  unchanged — both still run as a `BackgroundTask`, since a manual trigger
  from an authenticated admin action doesn't have the "never touch the
  request thread" constraint the webhook path does.

---

## Index status

`RepositoryStatus` gains `QUEUED` (M1 had `PENDING → CLONING → INDEXING →
READY/FAILED`); `Repository` gains `index_started_at`, `index_completed_at`
(alongside M1's `error_message`, reused rather than duplicated as
`index_error`).

```
GET /api/v1/repositories/{id}              full resource
GET /api/v1/repositories/{id}/status        (M1, unchanged)
GET /api/v1/repositories/{id}/index-status  alias of /status
POST /api/v1/repositories/{id}/reindex      manual full re-index
GET /api/v1/repositories/{id}/events        SSE progress stream
```

`/status` and `/index-status` return the identical shape — the alias
exists because the milestone brief names both spellings, not because
they mean different things.

### Progress events are fire-and-forget, not durable

`GET /{id}/events` subscribes to a Redis pub/sub channel
(`repo:{id}:events`) and streams `text/event-stream`. **A client that
connects after an event fired sees nothing before it** — there's no
replay buffer. `/index-status` is the source of truth the frontend
reconciles from (poll it while `status` is `queued`/`cloning`/`indexing`,
per `apps/web/src/features/repos/repo-card.tsx`'s `refetchInterval`); the
SSE stream is decoration for an already-open tab, not something to build
retry/ack logic on top of. If durable event history becomes a real
product need, that's an outbox-into-Postgres change, not a pub/sub tweak.

---

## Security

- **HMAC verification, fail closed** — see [GitHub webhook
  endpoint](#github-webhook-endpoint) above. An unset
  `GITHUB_WEBHOOK_SECRET` rejects every request.
- **Never trust the payload pre-verification** — signature check happens
  before any JSON parsing or repository lookup.
- **GitHub App installation tokens**: `GitHubAppAuth` never logs the app
  JWT or an installation token, and nothing persists a token anywhere —
  see [Testing strategy](#testing-strategy) for why this primitive exists
  but isn't yet wired into the clone path (no `installation_id` is ever
  populated yet, so there is nothing to wire it *to*).
- **Path containment**: `domain/file_filter.py::is_safe_relative_path`
  rejects any diff-reported path that isn't a clean repo-relative path
  before it's used anywhere.
- **org_id/repo_id isolation**: unchanged from M1 — no org model yet
  (M6), but every query is already scoped by `repository_id`, and Qdrant
  points are filtered the same way.

---

## Failure handling

| Failure | Behavior |
| --- | --- |
| Invalid/missing webhook signature | 401, nothing recorded, nothing enqueued. |
| Missing delivery/event header | 400. |
| Duplicate delivery | 200, no re-enqueue (see [Deduplication](#deduplication)). |
| Unknown repository | 200, delivery marked `ignored`, nothing enqueued. |
| Untracked branch / tag / branch deletion | 200, delivery marked `ignored`. |
| Malformed push payload | 400, delivery marked `failed`. |
| Exception inside `process_push_event` | Delivery marked `failed`, still 200 (GitHub redelivers on non-2xx; redelivering into the same application bug doesn't help, and the delivery is already recorded so a genuine redelivery would dedup away). |
| Git fetch/diff failure inside the worker job | Job marked `failed`, `repository.error_message` set, `repository.status = FAILED`. Exception re-raised so arq's own retry/backoff applies. |
| One malformed file mid-job | Recorded in `IncrementalIndexStats.errors`, job continues; the *job* only fails on infra-level errors (git, DB, Qdrant), not per-file parse/embed errors. |
| Base commit unreachable / repo never indexed | Falls back to a full `index_repository` run. |

---

## Testing strategy

Same split as M1 (`docs/architecture/milestone-1-rag-pipeline.md`'s
Testing section): pure-function unit tests where possible, real
Postgres+Qdrant integration tests for the actual pipeline, no live
GitHub/Redis required anywhere in the suite.

- **`domain/webhook_security.py`**: HMAC verify/reject, pure unit tests.
- **`domain/git_diff.py`**: `parse_name_status` pure unit tests (added,
  modified, deleted, renamed, copied, blank lines).
- **`domain/file_filter.py`**: `is_safe_relative_path` pure unit tests.
- **`infrastructure/vcs/git_service.py`**: `fetch_commit`/
  `diff_name_status`/`read_blob` against a real local two-commit git
  fixture (`tests/conftest.py::sample_repo_with_history`) — genuinely
  exercises the same fetch-by-SHA mechanism verified against
  `octocat/Hello-World`, just against `file://`-equivalent local paths so
  CI needs no network access.
- **`application/webhooks/handle_github_webhook.py`**: `process_push_event`
  unit tests against a real Postgres session + `FakeJobQueue` — every
  branch/tag/deletion/unknown-repo/untracked-branch outcome, plus
  case-insensitive full_name matching and `github_repo_id` backfill.
- **`application/indexing/incremental_index_repository.py`**: the
  milestone's actual verification-gate test — full index at commit A,
  then a real second commit (modify + add + delete + rename) via the
  `sample_repo_with_history` fixture's `push_commit_b()`, incremental
  index to commit B, and assert: only the four changed files were
  touched, the renamed file kept its exact chunk IDs (proving no
  re-embed), the deleted file's rows/points are gone, `last_indexed_commit`
  advanced, and re-running the same `after_sha` is a no-op. Also a
  fallback-to-full-index test for a never-indexed repo.
- **`api/webhooks.py`**: full HTTP-level tests through the real FastAPI
  app — signature rejection, missing headers, duplicate delivery (posted
  twice, asserts exactly one enqueue), unsupported event acknowledged,
  untracked branch acknowledged, valid push enqueues with the right
  repository/SHAs. `get_job_queue` is overridden with `FakeJobQueue` for
  every test in this file — including signature-rejection tests — because
  FastAPI resolves all of a route's dependencies before the handler body
  runs, so even a rejected request touches `JobQueueDep`; see the test
  file's module docstring.
- **`infrastructure/models.WebhookDelivery`**: a direct test that a
  duplicate `github_delivery_id` insert raises `IntegrityError` —
  confirms the actual DB-level guard, not just the application code that
  catches it.
- **`infrastructure/vector_store/qdrant_store.py::set_payload`**: direct
  test against a real throwaway Qdrant collection — payload updates,
  vector untouched.
- **`infrastructure/github/app_auth.py`**: JWT construction and
  installation-token exchange, tested against a throwaway RSA key
  generated at test time (`cryptography`) and an `httpx.MockTransport` —
  no real GitHub App credentials needed or used.

**What's built but not wired end-to-end**:
`infrastructure/github/app_auth.py`'s `GitHubAppAuth` (mints an
installation access token from `GITHUB_APP_ID`/`GITHUB_APP_PRIVATE_KEY`,
tested in `tests/github/test_app_auth.py` against a throwaway
test-generated RSA key + `httpx.MockTransport` — no real GitHub App
needed) and `authenticated_clone_url` (injects a token into an `https://`
clone URL) are real, tested units, satisfying the milestone brief's §9.2
"acquire the appropriate GitHub installation credentials" step in
isolation. They are **not** called from the clone path yet, because
nothing in this milestone (or M1) ever populates `Repository
.installation_id` — there is no "install the GitHub App on this repo"
flow, only `POST /repositories {"url": ...}`. Wiring installation-token
auth into `index_repository`/`incremental_index_repository`'s clone calls
is a small, mechanical follow-up once that connection flow exists (it
naturally belongs with M6's auth work, or a dedicated increment before
it) — building it now against a code path nothing can ever reach would be
untestable speculation, not a finished feature. Public repos and all
local/CI testing are unaffected: cloning uses the repository's plain
`url`, exactly as in M1.

---

## Performance

The milestone's stated goal: a small push produces a small indexing job,
not a full re-embed. What actually bounds the work:

- **Files touched** = files in the git diff, not files in the repo —
  `incremental_index_repository` never walks the tracked-file list the
  way `index_repository` (full index) does.
- **Chunks re-embedded** = chunks whose *content hash* is new, not
  chunks in the changed files — a file with one changed function still
  reuses every other chunk's existing embedding (same mechanism M1 built
  for content-hash-driven full reindex, `file_indexer.py::index_file_content`).
- **A pure rename embeds zero chunks** — proven by the integration test,
  not just asserted in a docstring.
- `IncrementalIndexStats` (returned by `incremental_index_repository`,
  logged by `workers/tasks.py::run_incremental_index`) reports exactly
  the metrics the brief asks for: `files_discovered`, `files_added`/
  `files_modified`/`files_deleted`/`files_renamed`, `chunks_created`
  (== embedding-provider calls made), `chunks_deleted`, plus wall-clock
  duration from the worker task wrapper.

---

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `GITHUB_WEBHOOK_SECRET` | *(empty)* | HMAC secret for `X-Hub-Signature-256`. Every webhook is rejected while unset. |
| `GITHUB_APP_ID` | *(empty)* | Optional — GitHub App id, only needed to mint installation tokens for private repos. |
| `GITHUB_APP_PRIVATE_KEY` | *(empty)* | Optional, paired with `GITHUB_APP_ID`. |

All other configuration (`REDIS_HOST`/`REDIS_PORT`/`REDIS_DB`,
`QDRANT_URL`, embedding/chat provider settings) is unchanged from M1 — see
`apps/api/.env.example`.

---

## Local development

### Running the worker

```bash
# Docker Compose — a `worker` service now runs alongside `api`:
docker compose up --build

# Host-run, from apps/api:
uv run arq lumora_api.workers.settings.WorkerSettings
```

### Setting up a real GitHub webhook

1. Create (or reuse) a GitHub App, or a plain repo webhook for testing —
   this milestone doesn't require a full GitHub App installation flow
   (no user-facing "connect via GitHub App" UI yet; that's bundled with
   M6's auth work). A repo-level webhook (Settings → Webhooks → Add
   webhook) is enough to exercise this milestone end-to-end:
   - **Payload URL**: `https://<your-tunnel>/webhooks/github` (a tunnel
     — ngrok, Cloudflare Tunnel, etc. — since GitHub needs to reach your
     machine; there's no ingress requirement beyond "reachable over
     HTTPS").
   - **Content type**: `application/json`.
   - **Secret**: any value — set the same value as `GITHUB_WEBHOOK_SECRET`.
   - **Events**: "Just the push event" (this milestone only handles
     `push`; other event types are acknowledged and ignored).
2. Register the target repo with Lumora first (`POST /api/v1/repositories
   {"url": "https://github.com/owner/repo.git"}`) and run an initial full
   index (`POST /{id}/index`) — a webhook for a repo Lumora has never
   indexed falls back to a full index anyway (see [Incremental diff
   algorithm](#incremental-diff-algorithm)), but starting from a real
   baseline is what actually exercises the incremental path on the next
   push.
3. Push a small change to the tracked branch. Watch worker logs
   (`docker compose logs -f worker`) for `incremental index metrics
   repo=... files_discovered=... chunks_created=...`.

### Testing signature verification manually

```bash
BODY='{"ref":"refs/heads/main","before":"...","after":"...","deleted":false,"repository":{"id":1,"full_name":"owner/repo","default_branch":"main"}}'
SIG="sha256=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$GITHUB_WEBHOOK_SECRET" | cut -d' ' -f2)"

curl -X POST http://localhost:8000/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-GitHub-Delivery: $(uuidgen)" \
  -H "X-Hub-Signature-256: $SIG" \
  -d "$BODY"
```

### Without any GitHub App credentials at all

Everything in this milestone works against public repos and local
testing without `GITHUB_APP_ID`/`GITHUB_APP_PRIVATE_KEY` — cloning uses
the repository's plain `url` (M1 behavior), same as before, and nothing
in the test suite requires them (milestone brief §14).
`GitHubAppAuth`/`authenticated_clone_url` exist and are unit-tested
against a locally-generated key, but private-repo cloning via an
installation token isn't reachable yet — see [Testing
strategy](#testing-strategy) for why.
