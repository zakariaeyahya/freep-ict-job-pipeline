# Solution Proposal — Scan Worker Architecture

Brief §9.1 requires "a solution proposal with at least two serious
options, trade-offs and a recommendation." This document covers the one
open architectural decision the frontend's CLAUDE.md flags explicitly:
where the long-running scan process (discovery, fetch, parse, validate,
store — potentially minutes long, with retries and rate-limited HTTP
calls to Freep) runs, given that it cannot run inside a serverless
Next.js API route.

## The constraint

Next.js API routes on common serverless hosts (Vercel and similar) have
execution time limits (seconds, not minutes) and no persistent process —
each invocation is stateless and can be killed at any point. A Freep scan
(discover the ICT route, fetch and parse every job detail page with a
self-imposed 0.5s delay between requests, per
[`../docs/DISCOVERY_REPORT.md`](../docs/DISCOVERY_REPORT.md)'s
robots.txt-driven rate limiting) routinely exceeds that. §9.2's
"Scheduler" responsibility ("starts scheduled and manual scans and
prevents conflicting runs") also needs a process that persists between
invocations, which a serverless function does not provide.

## Option A — Separate long-running Python worker (chosen)

A standalone Python service (`backend/`, this repository), triggered
manually today (`scripts/scrape.py`) or by an external scheduler, running
independently of the Next.js frontend. It owns discovery, fetching,
parsing, validation, storage, and publishes through its own FastAPI API
that the frontend calls as an HTTP client — no shared process, no shared
deploy, no shared runtime.

**Trade-offs:**

- (+) No serverless time-limit risk at all — the process runs for as long
  as a scan takes, with no external constraint.
- (+) Python's ecosystem for HTML parsing/scraping (BeautifulSoup,
  requests) is a better fit for this workload than doing the same in
  Node/TypeScript, and the pipeline's LLM-assisted extraction step
  (`extraction/`) already depends on Python-side libraries.
- (+) Clean separation of concerns: the frontend is a pure consumer of a
  versioned API/data contract (`contracts/*.schema.json`), so pipeline
  internals can change without touching the UI, and vice versa.
- (+) Testable in isolation with real dependency injection throughout
  (`ScanPipeline`'s constructor takes every collaborator), which is how
  AC10 (interrupted-scan recovery) and AC14 (publish-blocking) are proven
  today without a live Freep connection.
- (-) Two codebases/two deploy targets to operate instead of one —
  operational overhead this runbook exists to offset.
- (-) No scheduler or concurrency lock exists yet (see RUNBOOK.md "Known
  limitations") — this option requires building or wiring one in
  separately; it is not free with the architecture, only made possible by
  it.

## Option B — Serverless-triggered worker via a queue (e.g. a cloud task queue + a background compute target)

Next.js API routes only enqueue a scan request (a cheap, fast operation
well within serverless limits) onto a managed queue; a separate
long-running compute target (a container, a scheduled cloud function with
its own longer timeout, or similar) picks up the job and runs the actual
scan, writing results back to the same database the frontend reads from.

**Trade-offs:**

- (+) Keeps the entire stack in one language/repo if the worker is also
  written in TypeScript — no second Python codebase.
- (+) A managed queue gives natural retry/backoff and a built-in place to
  prevent conflicting runs (a lock keyed by "one in-flight scan job at a
  time" in the queue itself).
- (-) BeautifulSoup-equivalent HTML parsing in the Node ecosystem is
  weaker for this kind of ad-hoc structural parsing; the existing,
  already-built, already-tested Python parser (`parsing/job_parser.py`)
  would have to be rewritten rather than reused.
- (-) Introduces a new piece of infrastructure (the queue) and a second
  compute target, with its own configuration, IAM/access setup, and
  failure modes to operate — more moving parts than Option A for an
  equivalent outcome at this project's current scale (one source, one
  route, ~87 jobs per scan).
- (-) Harder to test end-to-end without either mocking the queue or
  standing up the real infrastructure locally.

## Recommendation

**Option A**, which is what this repository already implements. At this
project's current scale (a single source, a single known route, roughly
90 jobs per scan) the operational simplicity of one long-running process
outweighs a queue's retry/scaling benefits, and reusing Python's mature
HTML-parsing ecosystem avoided rewriting already-tested parsing logic.
Option B becomes more attractive if the pipeline later needs to scan
multiple independent sources in parallel or scale scan frequency well
beyond a daily cadence — worth revisiting then, not now.

**What Option A still needs** (tracked in `RUNBOOK.md` "Known
limitations", not yet built): a scheduler (cron-triggered, or a simple
`while True: sleep` loop process) and a concurrency lock so two scans
can't run against the same database at once. Both are additive on top of
the current architecture — `ScanPipeline` itself does not need to change
to add either.

## Field extraction: LLM-assisted vs. static-only (chosen: LLM-assisted)

A second, independent decision: how to derive the profile, engagement and
procedure fields (`education`, `experience`, `skills`, `methods`,
`certifications`, `languages`, `zzp_allowed`, `screening`, `vog`,
`positions`, `max_candidates` — brief §4.2) that Freep exposes only as
prose mixed into the free-text requirements/wishes, not as separate HTML
elements (e.g. "Geen ZZP", "afgeronde HBO opleiding" are sentences, not
structured fields anywhere in the page markup).

### Option 1 — Static-only extraction (regex/keyword rules, no LLM)

Every one of these fields would be derived with hand-written regex or
keyword-matching rules against the requirements/wishes text (the same
approach already used for `contract_type`'s HTML badge, extended to prose
fields it does not currently cover).

**Trade-offs:**

- (+) Fully deterministic and free to run — no third-party API dependency,
  no per-request cost, no rate limit, no outage risk from an external
  provider.
- (+) Trivially reproducible: the exact same input text always yields the
  exact same output, with no model version drift to account for over time.
- (+) No risk of a hallucinated value ever reaching a published record —
  the class of failure this project's never-fabricate rule exists to
  prevent (CLAUDE.md; `LlmFieldExtractor`'s anti-fabrication verification
  pass) cannot occur if there is no generative step at all.
- (-) **Loses information the LLM-assisted step currently recovers.**
  Requirements are free Dutch prose with unbounded phrasing
  ("Kandidaat heeft minimaal 3 jaar ervaring met programmeren in python",
  "diepgaande kennis van huisvestingswetgeving", "in team verband aan het
  project werken door gebruik te maken van de juiste tools en werkwijze")
  — a fixed rule set only catches phrasings it was written to catch.
  Every synonym, word order, or way of expressing the same requirement
  that the rules did not anticipate is silently missed, not flagged as
  uncertain: the field is simply left empty even though the information
  is present in the source text.
- (-) High and growing maintenance cost: each new client/agency posting on
  Freep tends to phrase the same requirement differently, so the rule set
  would need continual expansion as new phrasings are observed in
  production, with no way to know how much is being missed without manual
  sampling.
- (-) Structured, multi-concept fields degrade the most. `skills`,
  `methods` and `education` in particular are not single keywords but
  concepts embedded in full sentences (see the "Ai developer" example in
  the project report: "sterke kennis van prompt engineering, agents en
  Retrieval-Augmented Generation" correctly yields three separate skills
  today) — regex reliably extracts isolated keywords but struggles to
  segment a sentence into the right number of distinct, correctly-bounded
  items without either over-splitting or merging unrelated concepts.

### Option 2 — LLM-assisted extraction with source-verification (chosen)

An LLM (`LlmFieldExtractor`, OpenAI primary / Groq fallback per
`FallbackLlmClient`) reads the same free text and proposes structured
values, but every value it returns is verified to be an exact substring
of the source text before being trusted — a paraphrase or invented value
is discarded, never published (see the module's docstring for the
anti-fabrication guarantee this rests on).

**Trade-offs:**

- (+) Recovers far more of the information actually present in the
  source, because it generalizes across phrasing instead of matching
  fixed patterns — the same reason it correctly segments multi-concept
  sentences into distinct skills/requirements that a keyword rule would
  either merge or miss entirely.
- (+) The verification step keeps the static-only option's core safety
  property: nothing reaches a published record unless it is a literal,
  checkable excerpt of the source — the LLM is a *proposal* mechanism, not
  a trusted source of truth by itself.
- (+) `_enrich_with_llm_fields_unless_source_unchanged` (pipeline.py)
  reuses the previous scan's extraction when a job's source text has not
  changed, so the LLM is only called once per distinct piece of source
  text, not on every scan.
- (-) Depends on two external services (OpenAI, Groq) — cost per call,
  rate limits, and an outage of both leaves that scan's new/changed jobs
  with these fields empty until a later scan succeeds (best-effort, never
  blocks the scan — see RUNBOOK.md "Known limitations").
- (-) Not perfectly deterministic across model versions: the *verification
  pass* is deterministic (a value is either a substring of the source or
  it is not), but the *set* of values a given model proposes for the same
  input can vary slightly between model versions or providers, so which
  correct values are recovered (never which incorrect ones are published)
  can shift slightly over time.
- (-) Adds two provider integrations and their secrets (`OPENAI_API_KEY`,
  `GROQ_API_KEY`) to operate, versus zero for the static-only option.

### Recommendation for field extraction

**Option 2 (LLM-assisted, with source-verification)**, which is what this
repository already implements. The static-only option's core problem is
not cost or complexity — it is that it **silently loses real information
already present in the source**, which directly works against the brief's
own completeness goals (§6.3 "Source coverage": critical fields with
evidence references divided by available critical fields, target 100
percent) far more than the LLM option's operational trade-offs (cost, two
external dependencies) work against it. The anti-fabrication verification
pass specifically closes the one risk a static-only approach would
otherwise "win" on (never publishing an invented value), so Option 2 gets
both properties — recovered information *and* no fabrication — rather
than trading one for the other.

Static-only extraction remains the correct fallback in one narrow case
already handled today: `contract_type`, which Freep exposes as a real
HTML badge rather than free text, is read directly by `JobParser` and
always takes priority over the LLM's text-based guess when the badge is
present (`pipeline.py`'s `_enrich_with_llm_fields`) — a structural signal
is used when one exists, and the LLM is reserved for fields that only
ever exist as prose.
