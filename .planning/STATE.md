# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-28)

**Core value:** Cover the key Italian osteopathy exam topics effectively in 3 weeks through AI-generated explanations, spaced repetition, and practice with real exam formats.
**Current focus:** Phase 1 - Foundation and Content Pipeline

## Current Position

Phase: 1 of 4 (Foundation and Content Pipeline)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-02-28 — Completed 01-01 (scaffold + production server)

Progress: [█░░░░░░░░░] 13%

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 4 min
- Total execution time: 0.1 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 1/2 | 4 min | 4 min |

**Recent Trend:**
- Last 5 plans: 01-01 (4 min)
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

### Pending Todos

None yet.

### Blockers/Concerns

- [Pre-Phase 2]: Past exam question sources need identification before Phase 2 import work — find authoritative Italian MUR PDFs or Alpha Test materials
- [Pre-Phase 4]: Official MUR curriculum topic list should be seeded as DB checklist in Phase 1 to gate Phase 4 completion

## Session Continuity

Last session: 2026-02-28T16:22Z
Stopped at: Post-Phase-1 cleanup session. Phase 1 code complete. Making UI + pre-generation improvements outside GSD plan.
Resume file: .planning/phases/01-foundation-and-content-pipeline/.continue-here.md

### Current work in progress (outside GSD plan)

**Problem 1 — Tailwind purged CSS**: The static `tailwind.min.css` only contains classes present when it was first built. New Tailwind classes don't take effect. **Fix**: use inline styles instead of Tailwind classes for layout changes.

**Problem 2 — Long line width**: Content was spanning too wide. **Fix**: Changed base.html container to `style="max-width: 560px; margin: 0 auto; padding: 1rem 1.5rem;"` (inline style bypasses purged CSS issue). Also updated topic.html sticky header negative margins to match.

**Problem 3 — Topics generate on first visit only**: 17 of 20 topics still have no content. **Fix**: Added `_bulk_generate()` async task in main.py `lifespan()` — runs on startup, generates all missing topics in parallel (semaphore=5). Service restarted at 16:22, generation in progress.

**Files changed this session:**
- `app/templates/base.html` — inline style for narrow centered column
- `app/templates/topic.html` — sticky header margin fix
- `app/main.py` — bulk generation on startup

**Next after this session:**
- Verify bulk generation ran (check DB: 20/20 topics generated)
- Close Phase 1 GSD checkpoint: `/gsd:execute-phase 1` → type "approved"
- Plan Phase 2: FSRS flashcards, quizzes, past exam questions
