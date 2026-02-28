---
phase: 04-coverage-completion-and-mobile-polish
plan: "01"
subsystem: database, ui
tags: [sqlite, seed, htmx, daisyui, mobile, ios, safari]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: topics table schema and _bulk_generate() lifespan hook
  - phase: 03-progress-and-ai-chat
    provides: chat_panel.html and topic.html templates that needed patching
provides:
  - 39 total topics in DB: 15 biology, 14 chemistry, 10 physics/math
  - mitocondri topic row fixing 3 orphaned quiz questions
  - full Fisica e Matematica subject group (physics subject, 10 topics)
  - iPhone Safari 16px minimum body text in explainer
  - 44px minimum tap targets on chat input and language toggle buttons
affects: [04-02, index.html accordion groups, topic.html, explainer_content.html]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "INSERT OR IGNORE topic seeding pattern — safe to re-run, skips existing rows"
    - "Inline style overrides for iOS Safari tap targets — never rely on purged Tailwind JIT classes"

key-files:
  created: []
  modified:
    - seed_topics.py
    - app/templates/fragments/explainer_content.html
    - app/templates/fragments/chat_panel.html
    - app/templates/topic.html

key-decisions:
  - "physics subject string used for both physics and math topics — matches existing accordion mapping in index.html"
  - "prose-sm removed entirely (not just overridden) — prose alone gives 16px base, prose-sm forces 14px"
  - "min-h-[44px] Tailwind class kept in class attribute for readability but inline style added alongside — purged CSS means the class has no effect, inline style is the actual enforcement"

patterns-established:
  - "Inline style for mobile tap targets: always use style='min-height: 44px;' not Tailwind JIT classes on pre-compiled DaisyUI"
  - "New topic groups map to existing subject strings in DB: 'biology', 'chemistry', 'physics', 'logic'"

requirements-completed: [CONT-01, CONT-02]

# Metrics
duration: 2min
completed: 2026-02-28
---

# Phase 4 Plan 01: Topic Coverage and Mobile Polish Summary

**39 topics seeded across biology/chemistry/physics (mitocondri orphan fixed), plus three iPhone Safari tap-target and font-size fixes via inline styles**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-28T20:09:19Z
- **Completed:** 2026-02-28T20:11:30Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added 19 new topic rows: 5 biology (including mitocondri to fix 3 orphaned quiz questions), 4 chemistry, 10 physics/math — total now 39 topics across all subjects
- Introduced `physics` subject group (Fisica e Matematica, 10 topics) that was entirely absent from the DB
- Fixed three iPhone Safari mobile usability regressions: body text forced to 16px minimum, chat input and language toggle buttons enforced at 44px minimum tap target via inline styles

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend seed_topics.py with all missing topics** - `1233890` (feat)
2. **Task 2: Fix three iPhone Safari mobile polish issues** - `9880e79` (fix)

## Files Created/Modified

- `seed_topics.py` - Extended TOPICS list from 20 to 39 entries; added physics subject block
- `app/templates/fragments/explainer_content.html` - Replaced `prose-sm` with `prose`, added `style="font-size: 1rem;"`
- `app/templates/fragments/chat_panel.html` - Removed `input-sm`, added `min-height: 44px` to chat input inline style
- `app/templates/topic.html` - Added `style="min-height: 44px;"` to both IT/EN language toggle buttons

## Decisions Made

- Used `subject="physics"` for all physics and math topics — the index.html accordion already maps this string to the "Fisica e Matematica" group label, so no template changes needed
- Removed `prose-sm` entirely rather than overriding it — `prose` renders 16px body text by default, `prose-sm` forces 14px which triggers iOS Safari auto-zoom. Keeping both would be confusing
- Left `min-h-[44px]` Tailwind class in place alongside the new inline style attribute — this is intentional: the class has no effect (purged CSS) but documents intent; the inline style is the actual enforcement

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - `python3` required instead of `python` (Python 2 not installed). Script ran cleanly, 19 rows inserted.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 39 topics are seeded; `_bulk_generate()` kicked off on service restart to auto-generate NULL-content explainers for all 19 new topics
- Physics/math subject group will appear in the Fisica e Matematica accordion on the home page immediately
- mitocondri orphan quiz questions are now linked to a valid parent topic — quiz routing works
- Ready for 04-02 (mobile polish phase 2, if any) or direct exam prep use

---
*Phase: 04-coverage-completion-and-mobile-polish*
*Completed: 2026-02-28*
