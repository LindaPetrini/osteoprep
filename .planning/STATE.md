---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: in-progress
last_updated: "2026-02-28T18:03:19Z"
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 6
  completed_plans: 5
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-28)

**Core value:** Cover the key Italian osteopathy exam topics effectively in 3 weeks through AI-generated explanations, spaced repetition, and practice with real exam formats.
**Current focus:** Phase 2, Plan 3 complete — timed practice exam live at /exam with AI explanations

## Current Position

Phase: 2 of 4 (Active Learning)
Plan: 3 of N complete
Status: Phase 2 in progress — 02-01, 02-02, 02-03 done
Last activity: 2026-02-28 — Completed 02-03 (timed practice exam, countdown timer, per-question AI explanations)

Progress: [█████░░░░░] 50%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: 22 min
- Total execution time: 0.7 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 2/2 | 44 min | 22 min |
| 2. Active Learning | 3/N | 12 min | 4 min |

**Recent Trend:**
- Last 5 plans: 01-01 (4 min), 01-02 (40 min), 02-01 (5 min), 02-02 (2 min), 02-03 (5 min)
- Trend: fast execution on DB + UI tasks

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
- [02-01]: Session state (session_ids, current_index, total) passed as GET query params to card_back, then embedded as hidden form fields — avoids relying on request.query_params in templates
- [02-01]: card_front and card_back fragments own their #card-container wrapper; review.html uses {% include %} without extra wrapper to avoid double-nesting with HTMX outerHTML swap
- [02-01]: maximum_interval=7 is a direct Scheduler attribute in py-fsrs 6.3.0, not scheduler.parameters.maximum_interval (parameters is a tuple of floats)
- [02-01]: due_count guard in base.html uses "is defined" check to handle routes that do not yet pass the context variable
- [02-02]: Radio button values use loop.index0 (Jinja2 zero-based loop counter) — Jinja2 has no enumerate filter
- [02-02]: answer_{question_id} form field naming — maps cleanly to DB question IDs regardless of display order
- [02-02]: QuizAttempt saved before fetching score history so results page includes current attempt
- [02-02]: generate-once-cache: explanation_json IS NULL check in router, db.flush() persists immediately, never regenerate
- [02-03]: start_time_epoch embedded server-side in form data-start-time; JS computes remaining = startTime + duration - Date.now()/1000 for drift-free countdown
- [02-03]: htmx.trigger(form, 'submit') used for timer auto-submit — bypasses neither HTMX nor hx-push-url; form.submit() would
- [02-03]: Hidden question_ids field in exam form — POST handler processes all questions (including unanswered) regardless of radio button state

### Pending Todos

- None

### Blockers/Concerns

- [Pre-Phase 2]: Past exam question sources need identification before Phase 2 import work — find authoritative Italian MUR PDFs or Alpha Test materials
- [Pre-Phase 4]: Official MUR curriculum topic list should be seeded as DB checklist in Phase 1 to gate Phase 4 completion
- [Ongoing]: Tailwind purged CSS — new Tailwind classes don't take effect; use inline styles for layout changes

## Session Continuity

Last session: 2026-02-28T18:03Z
Stopped at: Completed 02-03-PLAN.md — 2 tasks done, practice exam live at /exam with 22 MCQs and AI explanations.

### Next steps

1. Phase 2 plans 01-03 complete. Check for any remaining Phase 2 plans or advance to Phase 3.
2. Past exam question sources blocker resolved: 22 TOLC-B/TOLC-F style MCQs seeded directly — no external PDFs required for v1.
