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
