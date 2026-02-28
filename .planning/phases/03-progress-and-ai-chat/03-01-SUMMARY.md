---
phase: 03-progress-and-ai-chat
plan: 01
subsystem: progress-dashboard
tags: [progress, srs, quiz, htmx, dashboard]
dependency_graph:
  requires: []
  provides: [progress-dashboard, topic-completion-badges]
  affects: [index, fragments, topic-list]
tech_stack:
  added: []
  patterns: [sqlalchemy-aggregate-queries, daisyui-stat-component, group-by-no-n+1]
key_files:
  created:
    - app/services/progress_service.py
    - app/routers/progress.py
    - app/templates/progress.html
  modified:
    - app/routers/fragments.py
    - app/templates/fragments/topic_list.html
    - app/templates/index.html
    - app/main.py
decisions:
  - "Single GROUP BY query for best_scores in fragment router to avoid N+1 per topic"
  - "SRS new_cards computed as total_cards - reviewed_cards (no SRSState row = never reviewed)"
  - "learned_cards clamped with max(0,...) to guard against edge cases where due > reviewed"
metrics:
  duration: 2 min
  completed_date: "2026-02-28"
  tasks_completed: 2
  files_changed: 7
---

# Phase 3 Plan 01: Progress Dashboard Summary

Progress dashboard at /progress showing SRS counts and per-subject completion stats, with three-state topic completion badges (Completato/In corso/Non iniziato) in the subject accordion.

## What Was Built

- **`app/services/progress_service.py`** — `get_progress_summary(db)` runs three aggregate queries: topics by subject (total/generated), quiz accuracy by subject, and SRS counts (due/learned/new/total).
- **`app/routers/progress.py`** — `GET /progress` route rendering progress.html with full dashboard context.
- **`app/templates/progress.html`** — Dashboard with DaisyUI stat components for SRS counts (in scadenza oggi, apprese, nuove) and per-subject cards showing topic completion ratio and quiz accuracy percentage.
- **`app/routers/fragments.py`** — Extended `subject_topics_fragment()` with a single `GROUP BY` query to get best quiz score per topic slug; passes `best_scores` dict to template.
- **`app/templates/fragments/topic_list.html`** — Three-state completion badge: Completato (best >= 60%), In corso (content exists, no passing quiz), Non iniziato (no content yet).
- **`app/templates/index.html`** — "Vedi progressi" `btn btn-outline btn-sm w-full` button above the subject accordions.
- **`app/main.py`** — `progress.router` imported and registered.

## Verification Results

All plan checks passed:
1. App restarts cleanly: active (running)
2. GET /progress returns 200 with rendered stats
3. GET /subjects/biology/topics returns "In corso" badges (content exists, no passing quiz)
4. GET / contains `href="/progress"`
5. Fragment uses single GROUP BY query (no N+1)

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | dafb3f6 | feat(03-01): add progress_service and progress router |
| 2 | 7eff63a | feat(03-01): progress dashboard template, topic badges, index link |

## Self-Check: PASSED

All created files exist and all task commits are present in git history.
