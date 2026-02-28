# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-28)

**Core value:** Cover the key Italian osteopathy exam topics effectively in 3 weeks through AI-generated explanations, spaced repetition, and practice with real exam formats.
**Current focus:** Phase 1 complete — ready for Phase 2

## Current Position

Phase: 1 of 4 (Foundation and Content Pipeline) — COMPLETE
Plan: 2 of 2 complete (awaiting human-verify checkpoint)
Status: Checkpoint — awaiting device verification
Last activity: 2026-02-28 — Completed 01-02 (topic UI + AI content pipeline)

Progress: [██░░░░░░░░] 25%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: 22 min
- Total execution time: 0.7 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 2/2 | 44 min | 22 min |

**Recent Trend:**
- Last 5 plans: 01-01 (4 min), 01-02 (40 min)
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Bilingual schema (content_it/content_en) must be in DB from Phase 1 — retrofitting is expensive
- [Roadmap]: FSRS interval cap at 7 days enforced from Phase 1 algorithm design — prevents cards scheduling past exam
- [Roadmap]: Hallucination mitigation system prompt established in Phase 1 before any content generation
- [Roadmap]: Generate-once-and-cache pattern for all AI content — avoids API cost runaway
- [Roadmap]: PROG-03 (persistence) assigned to Phase 1 — SQLite must be correct before any data is generated
- [01-01]: templates_config.py pattern to avoid circular import between main.py and routers using Jinja2Templates
- [01-01]: Port 8443 with Tailscale TLS cert — avoids conflict with Open WebUI on 3000, provides real HTTPS
- [01-01]: WAL mode confirmed via async engine event listener (not direct sqlite3 connect)
- [01-02]: XML tags (<IT>/<EN>) used for Claude output parsing — more robust than JSON with embedded markdown
- [01-02]: Non-blocking background generation (BackgroundTasks + HTMX polling every 2s) — page responds immediately
- [01-02]: Schematic study note format with mandatory sections — denser, exam-focused content
- [01-02]: Bulk startup generation via lifespan() with asyncio.Semaphore(5) — pre-warms all 20 topics

### Pending Todos

- Human device verification of Phase 1 UI (checkpoint:human-verify pending)

### Blockers/Concerns

- [Pre-Phase 2]: Past exam question sources need identification before Phase 2 import work — find authoritative Italian MUR PDFs or Alpha Test materials
- [Pre-Phase 4]: Official MUR curriculum topic list should be seeded as DB checklist in Phase 1 to gate Phase 4 completion
- [Ongoing]: Tailwind purged CSS — new Tailwind classes don't take effect; use inline styles for layout changes

## Session Continuity

Last session: 2026-02-28T16:40Z
Stopped at: 01-02-PLAN.md — checkpoint:human-verify (Task 3). All code complete, awaiting device verification.

### Next steps

1. Visit http://91.98.143.115:8443 on iPhone Safari (or desktop browser)
2. Verify: subject accordions expand, topic pages load, IT/EN toggle works, sticky header stays fixed, uncertainty markers appear as amber callout blocks
3. Type "approved" to close the checkpoint and proceed to Phase 2 planning
