# Freep ICT Job Pipeline — Discovery Report

Deliverable required by brief §9.1 ("Discovery report covering source
analysis, assumptions, risks and open questions") and §3 ("Discovery:
Investigate Freep, accessibility, dynamics, risks, legal considerations
and AI data needs"). Written after the crawler, coverage check and pipeline
were already built and run successfully (87/87 ICT jobs, `scan_status =
COMPLETE_WITHIN_SCAN_WINDOW`) — this documents what was found and decided
during that work, as the deliverable the brief asks for.

## 1. Source structure

Freep (`https://www.freep.nl`) is a Nuxt.js server-rendered application.
The homepage embeds its full job listing — every segment, not only ICT —
as a single JSON payload inside `<script id="__NUXT_DATA__">`, encoded in
Vue's "devalue" format (values reference each other by array index instead
of nesting inline, to deduplicate repeats).

This means the entire current job list is available in **one HTTP request**
to the homepage, with no pagination, no "load more" button, and no
JavaScript execution required to reach it — the data is already in the
initial server response, not fetched client-side afterwards.

**Decision: read `__NUXT_DATA__` directly instead of driving a browser.**
`src/freep_pipeline/discovery/nuxt_data_decoder.py` decodes the devalue
array into plain Python values; `freep_discovery.py` walks the decoded
tree for any object shaped like a job record (`segment`, `slug`, `title`
keys present) and filters to `segment == "ICT Informatievoorziening"`.

Trade-off considered: crawl4ai/Playwright were already dependencies
available in this project (`requirements.txt`), and were the default
assumption going in. They were not needed for this step — driving a full
browser to render a page whose complete data is already in the raw HTML
response would add startup latency, memory, and a browser-crash failure
mode for no benefit. Playwright/crawl4ai remain available if a future
route requires genuine client-side interaction (e.g. a paginated route
that loads more data only after a click); none has been found so far
because there is exactly one known route (the homepage) covering all ICT
jobs currently listed.

## 2. Pagination / route inventory

At the time of this report, **one route is known**: the homepage
(`FREEP_START_URL = "https://www.freep.nl/"`). It was not necessary to
discover a second route because the homepage's `__NUXT_DATA__` payload
already contains every listed job, including all segments — there is no
"next page" of ICT jobs to reach, because there is no pagination in the
underlying data source at all (the pagination that exists in the *UI* is
client-side filtering of data already fully present in the initial
response).

This is recorded as a single `RouteVisit` per scan (AC01/AC02). If Freep
changes its architecture to paginate the underlying data (not just the
UI), this route inventory must grow, and `ScanPipeline._determine_scan_status`'s
`expected_route_count=1` must be updated accordingly — it is currently a
literal in `pipeline.py`, not derived, precisely because there is only one
known route today.

## 3. Coverage / stopping method (AC02/AC03)

Freep's listing page displays a filter checkbox with a live count next to
each segment name, e.g. `label[for="ICT Informatievoorziening"]` renders
as "ICT Informatievoorziening (87)". This count is extracted from the same
HTML response as the job data itself — no separate request, no
time-of-check/time-of-use gap between counting and discovering.

**Coverage rule:** a scan's discovery route counts as `success` only if
the number of unique ICT job slugs found in `__NUXT_DATA__` exactly equals
this displayed count (`CoverageChecker.check_coverage`). If they diverge,
the route is `partial`, an error is recorded, and the overall scan status
falls to `INCOMPLETE` — never silently treated as complete.

Per brief §1.4 ("any source count that may be visible is diagnostic
metadata only and does not determine whether the run is complete"), this
displayed count is **one signal**, not the sole basis for completeness:
completeness also requires every discovered job to have been successfully
fetched and parsed (`counts.processed >= counts.discovered`, zero
unresolved errors — see `_determine_scan_status`).

Verified against the live site twice during development: 87/87 both
times.

## 4. Robots.txt review

Checked `https://www.freep.nl/robots.txt` on 2026-09-28:

```
User-agent: *
Disallow: /account/*
Disallow: /alerts
Disallow: /bedankt-ervaring
Disallow: /bedankt
Disallow: /offerte-aangeleverd
Disallow: /reviews/*
Sitemap: https://www.freep.nl/sitemap_index.xml
```

No `Crawl-delay` directive is present. The homepage (`/`) and job detail
pages (`/opdracht/*`) are **not** in the disallowed list — both routes
this pipeline fetches are permitted.

**Compliance measures already in place**, independent of what robots.txt
requires:
- `HTTP_REQUEST_DELAY_SECONDS = 0.5` (`config/settings.py`) — a fixed
  delay between each job detail page fetch, so a full scan of ~87 jobs
  takes on the order of a minute of fetching, not a burst.
- A descriptive `HTTP_USER_AGENT` is sent on every request (currently a
  standard browser UA string — see "Open questions" below on whether this
  should instead identify the pipeline).
- Only two route *types* are ever fetched: the homepage (once per scan)
  and individual job detail pages under `/opdracht/` (paths never listed
  in `Disallow`).

## 5. Terms of use review

Checked `https://www.freep.nl/voorwaarden` ("Algemene voorwaarden",
linked from the site footer) on 2026-09-28. The document covers the
relationship between registered professionals, clients and the platform
(registration, confidentiality obligations in Article 4, Freep's right to
unilaterally amend the terms in Article 8.2). **No clause explicitly
addresses automated data collection, scraping, crawling, bots, or reuse
restrictions on publicly listed job content** was found in this review.

This is not the same as an explicit permission — the absence of a
prohibition is not a green light, and this review is not a legal opinion.
See "Open questions" below.

## 6. Privacy policy

A "Privacy verklaring" is linked from the footer (`/privacy`). Not yet
reviewed in detail — flagged for the same follow-up as terms of use.
Relevant because brief §7 requires: "Do not collect unnecessary personal
data; document retention periods and deletion." The pipeline currently
stores company names and job descriptions (business data), not personal
data about individuals — the data model has no field for a named
contact person, recruiter, or applicant. This should be re-confirmed once
`profile`/`engagement` fields (currently unpopulated — see CLAUDE.md "Not
done yet") are ever filled in, since some illustrative fields in brief
§4.2 (e.g. `screening`, `vog` — a Dutch background-check declaration) are
personal-data-adjacent if ever tied to a named individual.

## 7. Risks and open questions

1. **No explicit scraping permission or prohibition.** The terms of use
   reviewed do not mention automated access either way. Recommendation:
   before any production launch, get an explicit sign-off from Dreev
   (and ideally direct confirmation from Freep) rather than relying on
   silence in the terms — this is a business/legal risk-acceptance
   decision, not an engineering one, and brief §1.5 explicitly lists
   "No fabricated data and demonstrable source traceability" as something
   **Dreev decides**, with compliance review as a **shared** decision.
2. **User-Agent honesty.** The current UA string
   (`config/settings.py:HTTP_USER_AGENT`) identifies as a standard Chrome
   browser rather than disclosing this is an automated pipeline. Many
   scraping ethics guidelines (and some sites' acceptable-use policies)
   expect bots to self-identify, e.g. with a custom UA and a contact
   URL/email. Recommendation: discuss with Dreev whether to switch to a
   self-identifying UA — this is a policy trade-off (more transparent vs.
   higher chance of being blocked) that Dreev should weigh in on before
   production, not something to decide unilaterally.
3. **Single known route is a point-in-time fact, not a guarantee.** If
   Freep changes its site architecture (adds real pagination, moves ICT
   listings behind a different endpoint, stops embedding `__NUXT_DATA__`),
   discovery breaks in a way that should surface as `route.result =
   "failed"` (already handled — see `_discover`'s exception handling) but
   will need code changes, not just configuration, to recover. There is no
   automated alerting yet if this happens outside of manually reading a
   scan report or hitting `GET /health`.
4. **Coverage check depends on Freep's own UI markup.** If Freep renames
   the ICT filter label or removes the count display, `CoverageChecker`
   degrades to "coverage not confirmed" (route becomes `partial`, scan
   becomes `INCOMPLETE`) rather than failing outright — this is the
   intended degrade-safely behavior (brief §3.3: "a local problem must not
   unnecessarily block the entire run"), but it does mean coverage
   confirmation would silently stop working until someone notices the
   scan status change.
5. **No rate-limit or blocking response observed yet.** The pipeline has
   not yet been run at a frequency or volume that would reveal whether
   Freep enforces IP-based rate limiting or bot detection beyond what
   robots.txt states. This should be monitored once a recurring schedule
   is in place (brief §9.2 "Scheduler" responsibility — not yet built).

## 8. Summary

| Check | Status |
| --- | --- |
| robots.txt allows the two routes used (`/`, `/opdracht/*`) | ✅ Confirmed |
| Crawl-delay respected (none specified; self-imposed 0.5s delay in place) | ✅ In place |
| Terms of use reviewed for scraping restrictions | ✅ Reviewed — none found, not a legal clearance |
| Privacy policy reviewed for personal-data handling | ⚠️ Linked, not yet reviewed in full |
| Explicit business/legal sign-off from Dreev before production | ❌ Not yet obtained — recommended before launch (brief §7) |
