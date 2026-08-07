# Milestone 1: RAG Fundamentals — What's Actually Happening

This document explains the ideas behind Milestone 1's pipeline: connect a
repo → clone it → chunk it → embed it → store it → search it → answer
questions about it with citations. Each section builds on the last, the
same order the pipeline actually runs in. Every concept links to the real
file and line implementing it — read the explanation, then go read that
code.

**Goal**: understand *why* each piece exists, not just that it exists.
Tutorials usually skip the "why not the obvious simpler thing" — that's
included deliberately here, because that reasoning is most of what makes
someone an AI engineer instead of someone who can call an API.

---

## 1. What is an embedding, and why does it capture meaning?

An **embedding** is a function that turns a piece of text into a fixed-
length list of numbers (a **vector**) — say, 768 numbers for
`nomic-embed-text`. That's it mechanically. The interesting part is what
those numbers *mean*.

A neural network (the embedding model) is trained on huge amounts of text
so that texts with similar *meaning* end up with vectors that point in
similar *directions* in that 768-dimensional space. "The cat sat on the
mat" and "A feline rested on the rug" would produce vectors close
together, even though they share almost no words — the model learned
meaning, not just vocabulary.

**Why does "close together" work?** Similarity between two vectors is
usually measured with **cosine similarity**: the cosine of the angle
between them. Two vectors pointing the same direction have cosine
similarity 1 (identical meaning); perpendicular vectors have similarity 0
(unrelated); opposite vectors have similarity -1. This is why embeddings
are almost always **normalized** to unit length (length 1) — with unit
vectors, cosine similarity becomes just the dot product, which is cheap to
compute at scale. Look at
[`infrastructure/embeddings/deterministic.py`](../apps/api/lumora_api/infrastructure/embeddings/deterministic.py) —
`_embed_one` explicitly divides the vector by its norm at the end. Real
embedding models (like Ollama's `nomic-embed-text`) are trained to
already output roughly-unit-length vectors.

**Why not just use the words themselves (keyword matching)?** Because
"function to add two numbers" and "def sum_pair(a, b): return a + b"
share almost no words, but mean the same thing. Embeddings capture that;
plain keyword matching can't. (Keyword matching still matters — see §5,
BM25 — it's just not *sufficient* alone.)

**The abstraction in this codebase**: `EmbeddingProvider`
([`infrastructure/embeddings/base.py`](../apps/api/lumora_api/infrastructure/embeddings/base.py))
is just `embed(texts: list[str]) -> list[list[float]]`. Two
implementations:
- [`OllamaEmbeddingProvider`](../apps/api/lumora_api/infrastructure/embeddings/ollama.py) —
  calls a real local model via Ollama's HTTP API. This is what produces
  *meaningful* embeddings.
- [`DeterministicEmbeddingProvider`](../apps/api/lumora_api/infrastructure/embeddings/deterministic.py) —
  hashes the text and uses that hash to seed a pseudo-random number
  generator. Same text → same vector, always (so re-indexing an unchanged
  chunk is still correctly a no-op — see §7) — but *unrelated* texts get
  *unrelated* vectors and similar texts do **not** reliably land near each
  other. It's a real, correct implementation of the interface; it's just
  not doing the semantic part. It exists so the whole pipeline (chunk →
  embed → store → search) can be tested and run with zero setup, no
  network, no multi-GB model download. This is a genuinely useful
  engineering pattern: separate "does the plumbing work" from "is the
  model good," and test them independently.

---

## 2. Why fixed-size chunking breaks code, and what AST chunking does instead

A document is too big to embed as one vector and search well — you'd lose
precision (one vector representing an entire 2000-line file is a blurry
average of everything in it) and you couldn't cite a specific location
anyway. So you split it into **chunks** first, embed each chunk
separately.

**The naive approach**: split every N lines (or N characters), regardless
of content. Simple, but for code, this is actively bad — a fixed window
routinely cuts a function signature off from its body, or a class
declaration from its methods. The chunk's text becomes syntactically
meaningless, which makes its embedding meaningless too (garbage in,
garbage out), *and* the resulting citation ("see file.py:45-104") doesn't
correspond to a coherent unit of code a human or LLM can reason about.

**What this pipeline does instead**: parse the code into an **Abstract
Syntax Tree (AST)** — a tree representation of the code's actual grammar
(this class contains these methods; this function has this body) — and
chunk along AST boundaries: one chunk per class, one per function, one
per method, one per interface. The tool doing the parsing is
[**tree-sitter**](https://tree-sitter.github.io/tree-sitter/), a
fast, incremental parser generator with grammars for dozens of languages.

Walk through [`infrastructure/chunking/tree_sitter_base.py`](../apps/api/lumora_api/infrastructure/chunking/tree_sitter_base.py):
`chunk()` parses the source into a tree, then `_walk()` recursively visits
every node. At each node it asks the language-specific `_classify()`
method "is this a chunkable declaration?" — if yes, it records a chunk
(using the node's own start/end line as the boundary — this is what makes
citations exact) and, for classes/interfaces, keeps walking *inside* that
node to also find its methods as separate chunks. This is why a class
becomes both one chunk (useful for "what does this class do") *and* each
of its methods becomes its own chunk (useful for "how does this specific
method work") — deliberate overlap, not a bug.

Two per-language subtleties worth understanding because they show what
"parsing real code" actually involves:
- [`python_chunker.py`](../apps/api/lumora_api/infrastructure/chunking/python_chunker.py):
  a `function_definition` node is ambiguous — it's used for both
  top-level functions *and* methods inside a class. The chunker
  disambiguates by checking whether any of the node's *ancestors* in the
  tree is a `class_definition` — a method is textually "inside" its
  class in the tree, a standalone function isn't.
- [`js_ts_chunker.py`](../apps/api/lumora_api/infrastructure/chunking/js_ts_chunker.py):
  `export function foo() {}` wraps the real declaration inside an
  `export_statement` node — the chunker "unwraps" it to classify the
  inner node, but keeps the *outer* node's line span so the `export`
  keyword stays part of the chunk text. And `const foo = () => {...}` is
  a totally different tree shape (a variable assignment whose *value*
  happens to be a function) — there's no single "arrow function
  declaration" node type to look for; the chunker has to walk into
  `variable_declarator` nodes and check whether their value is an
  `arrow_function`.

**What about Markdown/JSON/YAML — they don't have functions/classes.**
For those, "structural" still applies, just with a different notion of
structure: Markdown splits at heading boundaries
([`markdown_chunker.py`](../apps/api/lumora_api/infrastructure/chunking/markdown_chunker.py)),
JSON/YAML split at top-level keys
([`json_chunker.py`](../apps/api/lumora_api/infrastructure/chunking/json_chunker.py),
[`yaml_chunker.py`](../apps/api/lumora_api/infrastructure/chunking/yaml_chunker.py)).
Still not fixed-size — a section's length is however long that section
actually is.

**The fallback**: [`fallback.py`](../apps/api/lumora_api/infrastructure/chunking/fallback.py)
implements the fixed-size window chunker — used *only* when there's no
parser for a language, or the structural chunker finds nothing to split
on (e.g. a Python file that's just top-level statements, no functions or
classes). This is the explicit, narrow exception to "never use fixed-size
chunking," not a fallback used by default.

---

## 3. What Qdrant stores, and what vector search actually computes

Once you have chunks and their embeddings, you need to store them
somewhere that can answer: "given this query vector, which stored vectors
are closest?" — fast, even across millions of vectors. That's what a
**vector database** like [Qdrant](https://qdrant.tech/) is for.

**The naive approach**: compute cosine similarity between the query
vector and *every* stored vector, sort, take the top K. This is called
**exact** nearest-neighbor search. It's simple and always correct — but
it's O(n) per query, which becomes too slow once you have millions of
vectors.

**What Qdrant does instead**: **Approximate Nearest Neighbor (ANN)**
search, using an index structure (Qdrant uses a graph-based algorithm
called HNSW — Hierarchical Navigable Small World). The intuition: build a
graph where each vector is connected to its approximate neighbors, so a
search can "walk" toward the query vector's neighborhood through a small
number of hops instead of checking every point. This trades a small,
tunable amount of accuracy (you might miss the *exact* single best match
occasionally) for a massive speedup — sublinear instead of linear in the
number of stored vectors. At this project's current scale (one repo,
maybe a few thousand chunks), the speed difference doesn't matter much
yet — it matters once this scales to many repos and many users querying
concurrently, which is exactly why choosing a real vector database now
(rather than "just loop over a list") is the right call even though it's
overkill today.

**What actually gets stored**: look at
[`infrastructure/vector_store/qdrant_store.py`](../apps/api/lumora_api/infrastructure/vector_store/qdrant_store.py).
Each "point" in Qdrant has three parts:
- an **id** (here, the same UUID as the chunk's Postgres row — see §7)
- a **vector** (the embedding)
- a **payload** — arbitrary metadata (`repository_id`, `file_path`,
  `symbol`, `start_line`, `end_line`, and even the chunk's `content`
  itself, so a search hit is self-contained without a database join)

`ensure_collection()` creates the collection sized to whatever dimension
the *active* embedding provider actually produces (not a hardcoded
number) — because different embedding models produce different-sized
vectors (768 for `nomic-embed-text`, different for another model), and a
collection's vector size is fixed once created.

**Filtering**: search isn't just "find the closest vectors globally" — it
needs to be scoped to one repository (`search()` passes a `Filter` on
`repository_id`). This is why `create_payload_index` is called on
`repository_id` — a payload index lets Qdrant filter efficiently instead
of scanning every point's payload.

---

## 4. Why dense (embedding) search alone isn't enough — BM25

Embeddings are great at *semantic* similarity but bad at one specific,
common case: **exact identifier or literal matches**. If you search for
the exact function name `calculate_total`, you want the chunk containing
that literal identifier to rank first — but an embedding model doesn't
"know" `calculate_total` is special versus any other similar-sounding
name; it's reasoning about meaning, not exact tokens. A developer
searching for a specific error message, variable name, or function they
already know exists wants exact-match behavior, not semantic
approximation.

**BM25** (Best Match 25) is the classical answer to this — a **lexical**
(keyword-based) ranking algorithm, the same family as what search engines
used before embeddings existed, still extremely effective for exact-term
matching. The intuition: score a document higher if it contains the
query's terms more often (**term frequency**), but discount terms that
appear in *almost every* document anyway (**inverse document
frequency** — a word like "the" appearing everywhere tells you nothing,
so it's weighted down; a rare term like a specific function name that
appears in only a few chunks is a strong signal when it matches).

Look at
[`infrastructure/retrieval/bm25_index.py`](../apps/api/lumora_api/infrastructure/retrieval/bm25_index.py):
`Bm25Index.build()` takes the repository's chunk texts, tokenizes them
(splits into words, lowercased), and builds a `BM25Okapi` index (from the
`rank_bm25` library) over that token corpus. `search()` tokenizes the
query the same way and scores every chunk. The unit test
`test_search_ranks_exact_identifier_match_first` demonstrates exactly the
case above: a chunk literally containing `calculate_total` outranks
chunks that don't, regardless of any semantic similarity.

This index is rebuilt fresh on every search call, from whatever chunks
are already being loaded from Postgres for that search — a deliberate
simplicity trade-off, documented in the file, that's fine at this
project's current scale (rebuilding from a few thousand short texts takes
milliseconds) and would need revisiting (a persisted/cached index) if
corpus size or query volume grew a lot.

---

## 5. Combining two ranked lists: Reciprocal Rank Fusion

Now there are two *independent* ranked lists for the same query: dense
search's ranking (by cosine similarity) and BM25's ranking (by lexical
score). How do you combine them into one final ranking?

**The naive approach**: normalize both sets of scores to [0, 1] somehow
and add them together (a weighted sum). The problem: cosine similarity
and BM25 scores aren't on comparable scales, and their *distributions*
differ too (cosine similarities cluster in a narrow band; BM25 scores can
vary wildly based on corpus statistics) — there's no principled way to
pick weights that work well in general, and naive min-max normalization
is fragile (dominated by outliers).

**What this pipeline does instead**: **Reciprocal Rank Fusion (RRF)** — a
much simpler, remarkably effective trick that ignores the raw scores
entirely and uses only each item's **rank position** in each list.

```
fused_score(item) = Σ over each list containing item of  1 / (k + rank)
```

where `rank` is the item's position (0 = best) in that list, and `k` is a
constant (60, the standard value from the original paper — see
[`fusion.py`](../apps/api/lumora_api/infrastructure/retrieval/fusion.py)).
An item ranked #1 in a list contributes `1/(60+1) ≈ 0.0164`; an item
ranked #20 contributes `1/(60+21) ≈ 0.0123` — a smooth, diminishing
contribution as rank gets worse, and the same formula applies regardless
of what the underlying scores actually meant. An item that ranks well in
*both* lists accumulates a higher fused score than one that only appears
in one — which is exactly the desired behavior (agreement between two
independent signals is stronger evidence than either alone). The `k`
constant dampens how much any single #1 ranking dominates, so one list
having a very confident top result doesn't completely drown out the
other list's signal.

`search_repository()`
([`application/search/search_repository.py`](../apps/api/lumora_api/application/search/search_repository.py))
calls `reciprocal_rank_fusion(dense_ranked_ids, bm25_ranked_ids)`, then
sorts chunk ids by fused score, descending.

---

## 6. Reranking — a second, more expensive pass

Dense + BM25 + RRF gets you a good *candidate* list quickly. Reranking is
an optional final pass that looks at each candidate *together with the
query* and rescoring more carefully — trading speed for precision on a
small candidate set (typically the top 10-50, not the whole corpus).

**Why is this a *separate* step instead of just "make the first search
better"?** Because of a fundamental architecture difference between two
kinds of models:

- Embedding models (§1) are **bi-encoders**: they encode the query and
  each document *independently* into vectors, then compare vectors. This
  is what makes them fast enough to search millions of documents — you
  precompute every document's vector once, offline, and only the query
  needs encoding at search time.
- A **cross-encoder** (used for reranking) encodes the query *and* a
  candidate document *together*, as one input, letting the model's
  attention mechanism directly compare them token-by-token. This is much
  more accurate — the model can reason about exactly how this specific
  query relates to this specific document — but it's far more expensive:
  you can't precompute anything, and it has to run once per
  (query, candidate) pair. Fine for reranking 20 candidates; far too slow
  to use as the *first* pass over thousands of chunks.

Look at
[`infrastructure/retrieval/reranker/base.py`](../apps/api/lumora_api/infrastructure/retrieval/reranker/base.py) —
the `Reranker` abstraction is just `rerank(query, chunks) -> chunks`
(possibly reordered). Two implementations:
- [`NoOpReranker`](../apps/api/lumora_api/infrastructure/retrieval/reranker/noop.py) —
  the default; keeps the RRF-fused order as-is.
- [`CrossEncoderReranker`](../apps/api/lumora_api/infrastructure/retrieval/reranker/cross_encoder.py) —
  uses a real cross-encoder model (via `sentence-transformers`) to score
  each (query, chunk) pair and re-sort by that score. Off by default
  specifically because loading that model downloads weights from Hugging
  Face on first use — see the file's docstring for the "offline by
  default" reasoning.

---

## 7. From retrieved chunks to a cited answer

Once you have a final ranked list of chunks, two things happen with it:

**Search** ([`SearchResultItem`](../apps/api/lumora_api/api/v1/schemas.py))
returns the chunks directly — file path, symbol, line range, score,
content. No LLM involved. This is "show me the code," not "explain the
code."

**Chat**
([`application/chat/chat_with_repository.py`](../apps/api/lumora_api/application/chat/chat_with_repository.py))
does the same retrieval, then hands the chunks to a `ChatProvider` to
generate a natural-language answer. This is the actual "Retrieval-
Augmented Generation" — an LLM's answer is *grounded* in retrieved
context, rather than relying purely on what the model happened to
memorize during training (which for a specific private/local codebase is
nothing at all — the model has never seen this code). Look at
[`infrastructure/llm/ollama.py`](../apps/api/lumora_api/infrastructure/llm/ollama.py)'s
`_format_context()`: each chunk gets formatted as
`[file.py:12-34] symbol_name\n<chunk content>` before being inserted into
the prompt, with an instruction telling the model to cite file/line for
every claim. **This is how citations survive the round trip**: the file
path and line numbers travel with the chunk all the way from Qdrant's
payload → `RetrievedChunk` → the formatted prompt → (ideally) the model's
answer text. The model is *asked* to cite, not structurally forced to —
that's a real limitation of prompt-based grounding worth understanding:
nothing mechanically guarantees the LLM's prose actually references the
right chunk correctly, only that it *had* the right information available
with clear citation markers to use.

The offline default,
[`ExtractiveChatProvider`](../apps/api/lumora_api/infrastructure/llm/extractive.py),
sidesteps that limitation entirely by not generating prose at all — it
templates the retrieved chunks directly into a citation list. Guaranteed
accurate citations, at the cost of not being able to *synthesize* an
answer across multiple chunks the way a real LLM can.

---

## 8. Why re-indexing doesn't duplicate everything

One more concept worth understanding, because it's the kind of correctness
detail that's easy to get subtly wrong: how does re-indexing a repo avoid
re-embedding (expensive) and duplicating (wrong) chunks that haven't
changed?

Look at
[`application/indexing/index_repository.py`](../apps/api/lumora_api/application/indexing/index_repository.py)'s
module docstring and `_index_file()`. The mechanism is **content
hashing**, at two levels:
- Each **file**'s SHA-256 hash is compared to the last-indexed hash
  (stored in `IndexedFile.content_hash`). If unchanged, the file is
  skipped entirely — not even re-parsed.
- Within a changed file, each **chunk**'s SHA-256 hash (of its own text)
  is compared against the hashes already stored for that file. A chunk
  whose hash already exists is left alone — not re-embedded, not
  re-upserted into Qdrant. Only genuinely new/changed chunk text triggers
  a fresh embedding call (the expensive part) and a Qdrant upsert.
  Chunks whose hash *used to* exist but no longer does (the code was
  edited or removed) get deleted from both Postgres and Qdrant.

This is why editing one function in a 500-function file only costs one
embedding call, not 500 — and why running the same index twice with no
changes costs (almost) nothing at all beyond hashing.
