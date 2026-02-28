---
phase: 01-foundation-and-content-pipeline
plan: "02"
subsystem: ui
tags: [fastapi, htmx, jinja2, anthropic, sqlite, tailwind, daisyui, markdown-it]

# Dependency graph
requires:
  - phase: 01-01
    provides: "FastAPI app scaffold, SQLite DB with Topic model, systemd service, templates_config.py with Jinja2 filters"
provides:
  - "Home page with subject accordion UI (lazy-loaded via HTMX)"
  - "Topic page with sticky header and IT/EN language toggle"
  - "generate_explainer() service — generates both languages in single Claude API call"
  - "Generate-once-cache pattern — content never regenerated if already in DB"
  - "Uncertainty markers rendered as amber inline callout blocks"
  - "Language preference saved to localStorage and restored on visit"
  - "All 20 seed topics pre-generated and cached in SQLite"
affects:
  - phase-02-flashcards
  - phase-03-quiz

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Generate-once-cache: check DB first, call Claude only when content IS NULL"
    - "HTMX fragment endpoints for lazy-loaded accordions and in-place language swap"
    - "Background generation with semaphore-controlled parallelism"
    - "XML tags for Claude output parsing (more robust than JSON with embedded markdown)"
    - "Schematic study note format with defined sections (Definizione, Struttura, Meccanismo, etc.)"

key-files:
  created:
    - app/services/claude.py
    - app/templates/index.html
    - app/templates/topic.html
    - app/templates/fragments/topic_list.html
    - app/templates/fragments/explainer_content.html
    - static/app.js
  modified:
    - app/routers/pages.py
    - app/routers/fragments.py

key-decisions:
  - "XML tags (<IT>/<EN>) used for Claude response parsing instead of JSON — avoids escaping issues with embedded markdown"
  - "Non-blocking background generation pattern (BackgroundTasks) with HTMX polling skeleton — page responds immediately rather than waiting 20s"
  - "Schematic study note format with mandatory sections (Definizione, Struttura, Meccanismo, Dati chiave, Perché importante, Connessioni, Focus esame) produces denser, more testable content"
  - "Bulk startup generation via lifespan() with asyncio.Semaphore(5) — pre-warms all 20 topics on first deploy"
  - "render_content Jinja2 filter: markdown-it rendering + uncertainty marker conversion chained together"
  - "Wikipedia image + link shown on topic page via optional httpx fetch (3s timeout, never blocks)"

patterns-established:
  - "Fragment endpoints return only the content div — enables HTMX innerHTML swap for language toggle"
  - "Polling skeleton: hx-trigger='every 2s' with hx-swap='outerHTML' replaces itself when content ready"

requirements-completed: [CONT-01, CONT-02, CONT-03, CONT-04]

# Metrics
duration: 40min
completed: 2026-02-28
---

# Phase 1 Plan 2: Topic Browsing UI and AI Content Pipeline Summary

**Subject accordion home page + topic explainer pages with generate-once-cache Claude content, HTMX language toggle, and amber uncertainty marker callouts — all 20 seed topics pre-generated**

## Performance

- **Duration:** ~40 min (including fixes across multiple sessions)
- **Started:** 2026-02-28T15:30Z
- **Completed:** 2026-02-28T16:40Z
- **Tasks:** 2 of 3 complete (Task 3 is human-verify checkpoint)
- **Files modified:** 8

## Accomplishments

- Home page renders Biology and Chemistry subject accordions, lazily loading topic lists via HTMX on first expand
- Topic pages generate explainers on first visit using Claude claude-haiku-4-5-20251001 (both IT and EN in one call), cached in SQLite forever after
- IT/EN language toggle swaps content in-place via HTMX with no full page reload; preference saved to localStorage
- Uncertainty markers `[UNCERTAIN: ...]` in Claude output rendered as amber inline callout spans
- All 20 seed topics pre-generated on startup via bulk lifespan task (semaphore=5)
- Non-blocking: page responds instantly, HTMX polls `/topic/{slug}/content` every 2s until generation completes

## Task Commits

Each task was committed atomically:

1. **Task 1: Claude explainer service and generate-once-cache routes** - `cb8537a` (feat)
2. **Task 2: Home page, topic page, and HTMX fragment templates** - `8ced277` (feat)
3. **Additional fixes (multi-session):**
   - `059627d` — Non-blocking generation, back button, wiki images, richer explainer prompt
   - `5c16136` — Self-hosted CSS, markdown rendering, schematic explainer prompt
   - `847b170` — BackgroundTasks generation, XML parsing, back button, polling skeleton
   - `ac065bc` — Fix layout width with inline styles, bulk startup generation
   - `6dd719b` — Fix XML parsing when Claude wraps response in markdown code fences

## Files Created/Modified

- `app/services/claude.py` — AsyncAnthropic client with XML-tagged output parsing and uncertainty rules in system prompt
- `app/routers/pages.py` — GET / (home), GET /topic/{slug} (topic page with background generation)
- `app/routers/fragments.py` — GET /subjects/{subject}/topics (accordion), GET /topic/{slug}/content (lang swap + polling)
- `app/templates/index.html` — Subject accordion with HTMX lazy-load on revealed
- `app/templates/topic.html` — Sticky header, back link, IT/EN segmented control, Wikipedia image, explainer-content div
- `app/templates/fragments/topic_list.html` — Topic link list with "Pronto" badge for cached topics
- `app/templates/fragments/explainer_content.html` — Polling skeleton or rendered content with uncertainty markers
- `static/app.js` — localStorage language preference restored via HTMX ajax on DOMContentLoaded

## Decisions Made

- **XML over JSON for Claude output**: `<IT>` / `<EN>` XML tags used instead of JSON — markdown in JSON requires escaping; XML tag extraction with regex is simpler and more robust.
- **Non-blocking generation**: Used FastAPI BackgroundTasks + HTMX polling instead of blocking the HTTP response. Pages load instantly, content appears when ready.
- **Schematic format**: Changed from prose explainers to structured study notes with mandatory sections (Definizione, Struttura, Meccanismo, etc.) — produces denser, exam-focused content.
- **Bulk startup generation**: Added `_bulk_generate()` in lifespan to pre-warm all missing topics on service start with asyncio.Semaphore(5) — ensures content is ready before users visit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] JSON parsing fragile with embedded markdown in Claude responses**
- **Found during:** Task 1 / follow-up testing
- **Issue:** Claude responses with markdown formatting broke JSON.loads() — backticks, newlines, special chars in markdown require escaping in JSON
- **Fix:** Switched to XML tag output format (`<IT>...</IT><EN>...</EN>`) parsed with regex — no escaping issues
- **Files modified:** app/services/claude.py
- **Verification:** All 20 topics successfully parsed; no parse failures in logs
- **Committed in:** 847b170, 6dd719b

**2. [Rule 1 - Bug] Blocking generation made topic page hang for 20-30 seconds**
- **Found during:** Task 1 / follow-up testing
- **Issue:** Synchronous `await generate_explainer()` in the route blocked the HTTP response; poor UX
- **Fix:** Moved to BackgroundTasks + polling skeleton (HTMX polls every 2s, replaces itself with content)
- **Files modified:** app/routers/pages.py, app/templates/fragments/explainer_content.html
- **Verification:** Page loads instantly, content appears after generation completes
- **Committed in:** 847b170

**3. [Rule 2 - Missing Critical] Markdown not rendered — raw `**bold**` shown to user**
- **Found during:** Task 2 / follow-up testing
- **Issue:** Content was stored with markdown but rendered as plaintext
- **Fix:** Added markdown-it rendering in templates_config.py as `render_content` filter (chained with uncertainty markers)
- **Files modified:** app/templates_config.py, app/templates/fragments/explainer_content.html
- **Verification:** Headers, bullets, bold text render correctly in browser
- **Committed in:** 5c16136

**4. [Rule 2 - Missing Critical] Explainer content was generic prose, not exam-focused**
- **Found during:** Task 2 / follow-up testing
- **Issue:** Initial prompt produced unstructured prose — not suitable for exam prep
- **Fix:** Rewrote system prompt with mandatory schematic sections (Definizione, Struttura, Meccanismo, Dati chiave, Perché importante, Connessioni, Focus esame)
- **Files modified:** app/services/claude.py
- **Verification:** Regenerated topics show structured format with exam focus bullets
- **Committed in:** 5c16136

**5. [Rule 2 - Missing Critical] Topics not pre-generated — users wait on first visit**
- **Found during:** Post-Task 2 review
- **Issue:** Only generates on demand; all 17 ungenereted topics would make users wait ~20s each on first visit
- **Fix:** Added `_bulk_generate()` in main.py lifespan() with asyncio.Semaphore(5) — pre-warms all missing content on service startup
- **Files modified:** app/main.py
- **Verification:** All 20/20 topics have content_it and content_en in DB
- **Committed in:** ac065bc

---

**Total deviations:** 5 auto-fixed (2 bugs, 3 missing critical)
**Impact on plan:** All fixes essential for correctness and UX. No scope creep.

## Issues Encountered

- Tailwind CSS purged CSS only contains classes from initial build — new Tailwind classes don't take effect. Fixed by using inline styles for layout changes (bypasses purged CSS issue). Documented in STATE.md as ongoing constraint.

## User Setup Required

None — all content generated automatically on service startup. No external service configuration required beyond ANTHROPIC_API_KEY (already set in service environment).

## Next Phase Readiness

- All 20 seed topics generated and cached in SQLite (WAL mode, persists across restarts)
- Topic slug, title_it, title_en, subject fields ready for Phase 2 FSRS flashcard generation
- Content pipeline pattern established — generate_explainer() reusable for flashcard content
- Blocker: Past exam question source PDFs not yet identified (pre-Phase 2 concern)

---
*Phase: 01-foundation-and-content-pipeline*
*Completed: 2026-02-28*
