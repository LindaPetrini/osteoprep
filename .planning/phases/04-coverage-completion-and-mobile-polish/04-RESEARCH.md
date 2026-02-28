# Phase 4: Coverage Completion and Mobile Polish - Research

**Researched:** 2026-02-28
**Domain:** Content seeding (MUR syllabus gaps), quiz seeding, iPhone Safari mobile compatibility
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONT-01 | User can browse study topics organized by subject (Biology, Chemistry, Physics/Math, Logic) | Gap analysis: 20 topics exist (Biology + Chemistry only). Physics/Math topics are missing entirely. |
| CONT-02 | User can read an AI-generated explainer for each topic, generated on first access and cached in the database | All 20 existing topics have content. Gap: new topics seeded in Phase 4 will auto-generate via existing `_bulk_generate()` lifespan hook in `main.py`. No code changes needed for this requirement — only seeding. |
| QUIZ-01 | User can take a multiple-choice quiz after completing a topic section | Gap analysis: 14 of 20 existing topics have zero quiz questions. Physics/Math topics (not yet seeded) will also need quiz questions. |
</phase_requirements>

---

## Summary

Phase 4 has two distinct work streams: (1) content coverage completion, which is primarily a data problem, and (2) mobile polish, which is primarily a CSS/JS problem. Both streams are well-understood from the current codebase.

The MUR professioni sanitarie exam covers 23 biology questions, 15 chemistry questions, and 13 physics/math questions out of 60 total. The current DB has 10 biology and 10 chemistry topics, all with explainers. Missing entirely: Physics/Math topics, which account for 22% of exam questions. Also missing: quiz questions for 14 of 20 existing topics (none for mitosi-meiosi, respirazione-cellulare, fotosintesi, genetica-mendeliana, evoluzione-selezione, sistema-nervoso, atomo-struttura, tavola-periodica, ossidoriduzione, carboidrati, lipidi, proteine-struttura, enzimi — and a "mitocondri" slug exists in quiz_questions but has no corresponding topic row).

The app already has all the infrastructure needed: `seed_topics.py` pattern, `seed_quiz_questions.py` pattern, `_bulk_generate()` startup hook that auto-generates explainers for any topic with `content_it IS NULL`. New topics can be seeded and the app will self-populate content on next restart.

For mobile polish: the base.html already has `viewport-fit=cover` and `env(safe-area-inset-bottom)` applied to the bottom nav. The SSE chat endpoint correctly sets `media_type="text/event-stream"` which is what Safari requires. Most tap targets already use `min-height: 44px`. The main risks are: (a) the `prose prose-sm` class on explainer content may render body text below 16px on Safari, (b) the flashcard flip region needs tap target verification, and (c) the chat input area may have Safari keyboard-push layout issues.

**Primary recommendation:** Seed Physics/Math topics (8-10 topics covering kinematics, dynamics, thermodynamics, electromagnetism, algebra, functions, geometry, probability), add quiz questions to all 20 existing topics (5 per topic minimum), then do a focused iPhone Safari manual test pass against the 6 interactive surface areas.

---

## Standard Stack

No new libraries needed. This phase uses the existing stack exclusively.

### Core (already in use)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115.14 | Web framework | Already in use |
| SQLAlchemy async | 2.0.47 | DB ORM | Already in use |
| Anthropic Python | 0.84.0 | Claude API | Already in use |
| Jinja2 | 3.1.6 | Templating | Already in use |
| DaisyUI | pre-compiled | CSS components | Already in use — inline styles for layout |

### No Installation Required
All needed tools are already installed. Phase 4 does not introduce any new dependencies.

---

## Architecture Patterns

### Pattern 1: Topic Seeding (existing pattern)

**What:** Add new topic rows to the `topics` table with `content_it = NULL`. The `_bulk_generate()` lifespan hook in `main.py` will pick them up on next app restart and generate explainers via Claude API with `asyncio.Semaphore(5)`.

**When to use:** Adding new Physics/Math topics (and any other missing Biology/Chemistry subtopics).

**Example:**
```python
# Source: seed_topics.py (existing pattern in project)
# Direct sqlite3 INSERT OR IGNORE — no SQLAlchemy needed for seed scripts
{"slug": "cinematica", "title_it": "Cinematica", "title_en": "Kinematics",
 "subject": "physics", "order_in_subject": 1}
```

**Key constraint:** `subject` field must match the index.html template mappings:
- `"biology"` → "Biologia"
- `"chemistry"` → "Chimica"
- `"physics"` → "Fisica e Matematica" (already mapped in index.html)
- `"logic"` → "Logica" (already mapped)

### Pattern 2: Quiz Question Seeding (existing pattern)

**What:** Add rows to `quiz_questions` table: `(topic_slug, question_it, choices_json, correct_index)`. The `explanation_json` starts as `NULL` — explanations are generated on first quiz submission via `generate_quiz_explanation()`.

**When to use:** Adding 5+ MCQ questions per topic to all 14 currently-uncovered topics.

**Structure:**
```python
# Source: seed_quiz_questions.py (existing pattern in project)
("topic-slug",
 "Domanda in italiano?",
 ["Opzione A", "Opzione B", "Opzione C", "Opzione D"],
 correct_index)  # 0=A, 1=B, 2=C, 3=D
```

**Note:** The quiz router samples up to 5 questions randomly. Seed at minimum 5, ideally 8-10, per topic for variety.

### Pattern 3: iPhone Safari Mobile Polish (CSS/inline style)

**What:** DaisyUI is pre-compiled (no JIT) — new Tailwind classes don't work. Use inline styles for all layout fixes.

**Known working patterns in this codebase:**
```html
<!-- Tap target: works on Safari -->
style="min-height: 44px;"

<!-- Bottom nav safe area: already correct in base.html -->
padding-bottom: env(safe-area-inset-bottom);

<!-- Text size: must use inline style to guarantee 16px -->
style="font-size: 1rem;"  <!-- = 16px, never smaller for body text -->

<!-- Fixed footer with viewport-fit=cover: already in base.html -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
```

### Recommended Project Structure (additions only)

No new files or directories needed. Additions are:
```
osteoprep/
├── seed_topics.py          # Extend TOPICS list with Physics/Math entries
└── seed_quiz_questions.py  # Extend QUESTIONS list with all missing topics
```

The `app/templates/index.html` already maps `physics` subject → "Fisica e Matematica". No template changes needed to display Physics/Math topics once seeded.

### Anti-Patterns to Avoid

- **Using Tailwind classes that aren't in the pre-compiled CSS:** DaisyUI is pre-compiled. `text-base` (1rem) works; arbitrary values like `text-[16px]` do not. Use `style="font-size: 1rem;"` for explicit sizing.
- **Generating explainers synchronously at seed time:** The `_bulk_generate()` hook handles this automatically. Do not call `generate_explainer()` in seed scripts.
- **Adding quiz questions without verifying topic_slug exists:** The `quiz_questions.topic_slug` has a foreign key to `topics.slug`. Seeding quiz questions for a non-existent topic slug will fail silently or raise FK constraint error.
- **The orphan "mitocondri" slug:** There are quiz questions with `topic_slug = "mitocondri"` but no corresponding `topics` row. Either add a topic row for `mitocondri` or delete those orphan quiz questions during Phase 4.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Explainer content generation | Manual seeding of content_it/content_en | Leave as NULL, let `_bulk_generate()` handle it | Already implemented: lifespan hook runs on startup with Semaphore(5) concurrency |
| Mobile viewport height | Custom JS to compute window.innerHeight | `env(safe-area-inset-bottom)` + `viewport-fit=cover` (already in base.html) | Already implemented correctly |
| SSE MIME type for Safari | Custom response headers in each route | FastAPI `StreamingResponse(media_type="text/event-stream")` (already in chat.py) | Already correct |
| Text rendering markdown | Custom parser | `render_content` Jinja2 filter (already implemented) | Already implemented |

**Key insight:** Most infrastructure for this phase already exists. Phase 4 is primarily data work (seeding) plus a manual verification pass on mobile, not new code.

---

## MUR Syllabus Gap Analysis

### Current State (20 topics in DB)

**Biology (10 topics — all have explainers):**
- cellula-eucariotica, membrana-cellulare, nucleo-cellulare, mitosi-meiosi, dna-rna-proteine, respirazione-cellulare, fotosintesi, genetica-mendeliana, evoluzione-selezione, sistema-nervoso

**Chemistry (10 topics — all have explainers):**
- atomo-struttura, tavola-periodica, legami-chimici, acidi-basi-ph, reazioni-chimiche, ossidoriduzione, carboidrati, lipidi, proteine-struttura, enzimi

**Physics/Math: 0 topics — ENTIRE SUBJECT MISSING**

### Missing Biology Topics (from official MUR syllabus, not yet seeded)

The official syllabus includes anatomy/physiology topics not currently covered:
- Tessuti animali (animal tissues)
- Sistemi d'organo umani - apparato cardiovascolare, respiratorio, digestivo, escretore, endocrino, immunitario (human organ systems)
- Biotecnologie: DNA ricombinante (recombinant DNA biotechnology)
- Virus e procarioti (viruses and prokaryotes — cell theory basis)

**Recommendation:** Add 4-6 additional biology topics. The current 10 cover cell biology and genetics well; anatomy/physiology is the main gap.

### Missing Chemistry Topics

- Soluzioni e proprietà (solutions: concentration methods, solubility)
- Equilibrio chimico e tamponi (chemical equilibrium and buffers)
- Nomenclatura composti inorganici (inorganic nomenclature: oxides, hydroxides, acids, salts)
- Chimica organica: idrocarburi e gruppi funzionali (organic: hydrocarbons, functional groups)

**Recommendation:** Add 2-4 chemistry topics. Current 10 cover the core well; organic chemistry detail is the main gap.

### Physics/Math Topics to Seed (NEW — entire subject)

Based on the official MUR decree Allegato A (13 questions from physics/math):

**Physics:**
1. Grandezze fisiche e misura (physical quantities and measurement)
2. Cinematica (kinematics: velocity, acceleration, uniform/accelerated motion)
3. Dinamica (dynamics: Newton's laws, forces, momentum, work, energy)
4. Meccanica dei fluidi (fluid mechanics: pressure, Archimedes, Pascal, Bernoulli)
5. Termodinamica (thermodynamics: temperature, heat, gas laws, principles)
6. Elettromagnetismo (electromagnetism: charges, fields, Ohm's law, circuits)

**Mathematics:**
7. Algebra e aritmetica (algebra: equations, inequalities, powers, logarithms)
8. Funzioni (functions: polynomial, exponential, logarithmic, trigonometric)
9. Geometria (geometry: coordinate systems, conic sections, trigonometry)
10. Probabilità e statistica (probability and statistics)

### Quiz Coverage Gap

Topics with ZERO quiz questions (14 of 20):
- mitosi-meiosi, respirazione-cellulare, fotosintesi, genetica-mendeliana, evoluzione-selezione, sistema-nervoso
- atomo-struttura, tavola-periodica, ossidoriduzione, carboidrati, lipidi, proteine-struttura, enzimi

**Note:** "mitocondri" has 3 quiz questions but NO topic row. This slug is orphaned. Recommend: add a topic row for mitocondri (as a subtopic of respirazione-cellulare, or as standalone), or delete the orphan quiz questions.

---

## iPhone Safari Compatibility Analysis

### Current State Assessment

The codebase already has many correct mobile patterns:

| Element | Current State | Assessment |
|---------|---------------|------------|
| Viewport meta | `width=device-width, initial-scale=1.0, viewport-fit=cover` | CORRECT |
| Bottom nav safe area | `padding-bottom: env(safe-area-inset-bottom)` | CORRECT |
| Bottom nav height | Fixed 4rem + safe area | CORRECT |
| Content padding-bottom | `calc(4rem + env(safe-area-inset-bottom))` | CORRECT |
| Tap targets (most) | `min-height: 44px` on buttons, links | CORRECT |
| SSE MIME type | `media_type="text/event-stream"` | CORRECT — Safari compatible |
| SSE Cache-Control | `Cache-Control: no-cache` | CORRECT — required for SSE |
| Language toggle buttons | `min-h-[44px]` DaisyUI class | VERIFY — DaisyUI pre-compiled, this class may not render |
| Explainer prose text | `prose prose-sm` — sm is 0.875rem (14px) | RISK — below 16px minimum |
| Chat input field | `input-sm` class | RISK — may be under 44px height |
| Radio buttons in quiz | Wrapped in `<label>` with `min-height: 44px` | CORRECT pattern |

### Identified Mobile Risks

**Risk 1: prose-sm renders 14px text (below 16px minimum)**
- Location: `app/templates/fragments/explainer_content.html`
- Current: `class="prose prose-sm max-w-none ..."`
- Fix: Override body text size with `style="font-size: 1rem;"` on the prose container, or switch to `prose` (base) instead of `prose-sm`

**Risk 2: Chat input height below 44px on Safari**
- Location: `app/templates/fragments/chat_panel.html`
- Current: `class="input input-bordered input-sm w-full"` — `input-sm` in DaisyUI is ~2rem (32px)
- Fix: Add `style="min-height: 44px;"` to the input element, or use `input` instead of `input-sm`

**Risk 3: Language toggle min-h-[44px] may not work (purged Tailwind class)**
- Location: `app/templates/topic.html`
- Current: `class="join-item btn btn-sm min-h-[44px] ..."`
- The `min-h-[44px]` arbitrary value class is NOT in the pre-compiled Tailwind — it will be ignored
- Fix: Add `style="min-height: 44px;"` alongside the class

**Risk 4: Sticky header on topic.html with overflow ancestors**
- Location: `app/templates/topic.html`
- Comment says "iPhone Safari: no overflow on ancestor elements" — this is already handled correctly
- No fix needed — the comment documents existing correct behavior

**Risk 5: Safari SSE EventSource reconnection behavior**
- Safari has been known to close EventSource connections on network fluctuation
- The current implementation uses vanilla `EventSource` (not HTMX SSE extension) — this is the correct approach for Safari compatibility
- No fix needed — current implementation is already the Safari-compatible pattern

### Interactive Elements to Verify on iPhone Safari

| Element | Location | Key Behavior | Test Action |
|---------|----------|--------------|-------------|
| Flashcard flip | review.html + card_front/back.html | HTMX GET swap on button tap | Tap "Mostra risposta" |
| Rating buttons (4-col grid) | card_back.html | 4 small buttons in grid, 44px min | Tap each rating |
| Quiz radio selection | quiz.html | Radio in label row | Tap each choice |
| Quiz submit | quiz.html | Form POST | Submit quiz |
| Language toggle IT/EN | topic.html | HTMX GET swap | Tap IT, tap EN |
| Chat input + send | chat_panel.html | EventSource stream | Type question, tap Invia |

---

## Common Pitfalls

### Pitfall 1: Seeding quiz questions for non-existent topic slugs
**What goes wrong:** The `quiz_questions.topic_slug` column has a foreign key constraint to `topics.slug`. If you seed quiz questions referencing a slug that doesn't exist in topics, SQLite will raise an error (or silently fail with FK enforcement off).
**Why it happens:** The seed script creates topic rows and quiz question rows separately; if the topic seed fails or is skipped, FK constraint violation follows.
**How to avoid:** Always run `seed_topics.py` before `seed_quiz_questions.py`. Verify all slugs exist before running quiz seed.
**Warning signs:** `seed_quiz_questions.py` reports 0 inserted despite providing new data.

### Pitfall 2: DaisyUI pre-compiled class vs. inline style confusion
**What goes wrong:** Adding Tailwind utility classes like `text-base` or `min-h-[44px]` that aren't present in the pre-compiled tailwind.min.css — they have no effect and mobile issues persist.
**Why it happens:** Tailwind normally purges unused classes at build time. The pre-compiled file only includes classes used at original build time.
**How to avoid:** Use inline `style="..."` for any layout, sizing, or color that isn't already working in the app. Test on a real device, not just browser DevTools.
**Warning signs:** Style change in template has no visual effect.

### Pitfall 3: Mistaking "mitocondri" orphan for a missing topic
**What goes wrong:** There are 3 quiz questions with `topic_slug = "mitocondri"` but no corresponding `topics` row. The quiz router returns 404 if you navigate to `/topic/mitocondri/quiz` because there's no Topic row.
**Why it happens:** Quiz questions were seeded with a slug that was never added to the topics table.
**How to avoid:** Either (a) add a topic row for "mitocondri" (mitochondria, a valid exam topic — it's part of cellular respiration), or (b) delete the orphan quiz questions and re-add them under `respirazione-cellulare`.
**Recommendation:** Option (a) — mitocondri is a distinct, important exam topic. Add it as a biology topic.

### Pitfall 4: Font size in prose content appears fine on desktop but too small on iPhone
**What goes wrong:** `prose-sm` renders at 0.875rem (14px) which passes visual inspection on desktop but is below the 16px minimum for comfortable reading on iPhone without zoom.
**Why it happens:** `prose-sm` is the "small" typography preset — fine for desktop sidebars, too small for mobile main content.
**How to avoid:** Either remove the `-sm` modifier from `prose prose-sm` and add `style="font-size: 1rem;"` to ensure 16px body text, or override the base font size explicitly.

### Pitfall 5: Safari EventSource and service going down
**What goes wrong:** If the server restarts while a user has the chat panel open on Safari, the EventSource may not reconnect (Safari's reconnect behavior is less reliable than Chrome).
**Why it happens:** Safari's EventSource retry behavior has historically been inconsistent.
**How to avoid:** This is a known limitation. The current implementation closes the EventSource on `[DONE]` or `[ERROR]`. No persistent connection is maintained between questions. This is acceptable for the use case.

---

## Code Examples

Verified patterns from existing codebase:

### Adding a topic to seed_topics.py
```python
# Source: seed_topics.py (project file)
# Add to TOPICS list — content_it/content_en left NULL for auto-generation
{"slug": "cinematica", "title_it": "Cinematica", "title_en": "Kinematics",
 "subject": "physics", "order_in_subject": 1},
{"slug": "dinamica", "title_it": "Dinamica", "title_en": "Dynamics",
 "subject": "physics", "order_in_subject": 2},
```

### Adding quiz questions to seed_quiz_questions.py
```python
# Source: seed_quiz_questions.py (project file)
# Format: (topic_slug, question_it, [4 choices], correct_index)
("cinematica",
 "Qual è la formula per la velocità media?",
 ["v = a × t", "v = s / t", "v = F / m", "v = P × t"], 1),
```

### Fixing 16px body text in explainer (inline style override)
```html
<!-- Source: app/templates/fragments/explainer_content.html -->
<!-- Change from: -->
<div class="prose prose-sm max-w-none text-base-content ...">
<!-- Change to: -->
<div class="prose max-w-none text-base-content ..." style="font-size: 1rem;">
```

### Fixing chat input tap target
```html
<!-- Source: app/templates/fragments/chat_panel.html -->
<!-- Change from: -->
<input type="text" id="chat-input" ... class="input input-bordered input-sm w-full" ...>
<!-- Change to: -->
<input type="text" id="chat-input" ... class="input input-bordered w-full" style="min-height: 44px;">
```

### Fixing language toggle tap target (pre-compiled Tailwind issue)
```html
<!-- Source: app/templates/topic.html -->
<!-- Change from: class="join-item btn btn-sm min-h-[44px] ..." -->
<!-- Change to: class="join-item btn btn-sm ..." style="min-height: 44px;" -->
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HTMX SSE extension | Vanilla `EventSource` JS | Phase 3 decision | Safari compatibility — no CDN, no HTMX SSE bug on iOS 17.4 |
| 100vh for full-screen | `env(safe-area-inset-bottom)` + `viewport-fit=cover` | Phase 1 decision | Handles iPhone home bar correctly |
| `scroll-behavior: smooth` | Not used | Always | Smooth scroll causes HTMX fragment scroll issues on Safari |

**Deprecated/outdated patterns this project does NOT use:**
- HTMX SSE extension (`hx-sse`): Has known Safari iOS 17.4 issues — project correctly uses vanilla EventSource instead
- WebSockets for chat: Overkill for unidirectional streaming — SSE is the right tool

---

## Open Questions

1. **Should mitocondri be a standalone topic or absorbed into respirazione-cellulare?**
   - What we know: 3 orphan quiz questions reference `topic_slug = "mitocondri"`. Mitocondri is a distinct, exam-tested concept (cristae, ATP synthase, Krebs cycle).
   - What's unclear: Whether to make it standalone (adds a topic row) or to re-slug the quiz questions to `respirazione-cellulare` (loses the standalone entry point).
   - Recommendation: Add a `mitocondri` topic row — it's a high-value exam topic. The 3 existing quiz questions become live immediately.

2. **How many Physics/Math topics are needed?**
   - What we know: 13 exam questions come from physics/math (out of 60 total). The official syllabus has ~10 distinct topic areas.
   - What's unclear: Exact priority order. Physics mechanics + fluids + thermodynamics are highest frequency. Math topics (algebra, functions, geometry) appear less frequently.
   - Recommendation: Seed 8-10 Physics/Math topics covering the highest-frequency areas first. Kinematics, dynamics, fluids, thermodynamics for Physics; algebra+functions, geometry for Math.

3. **Is the existing viewport configuration sufficient for iPhone Safari 17+ with the home indicator?**
   - What we know: `viewport-fit=cover` + `env(safe-area-inset-bottom)` is the correct Apple-documented approach. The base.html already implements this correctly.
   - What's unclear: iOS 26 introduced new viewport behavior (per search results). If the exam falls before iOS 26 ships, this is irrelevant.
   - Recommendation: Test on an actual iPhone in the current iOS version. The existing implementation follows Apple's documented best practice.

---

## Sources

### Primary (HIGH confidence)
- Project codebase (direct read): `seed_topics.py`, `seed_quiz_questions.py`, `app/main.py`, `app/routers/quiz.py`, `app/routers/chat.py`, `app/services/claude.py`, `app/models.py`, all templates
- Live DB query (direct read): `topics` table — 20 topics, all with content; `quiz_questions` table — 7 topics covered, 14 with no questions

### Secondary (MEDIUM confidence)
- [ammissione.it - Programma Test Professioni Sanitarie](https://www.ammissione.it/area-sanitaria/programma-test-professioni-sanitarie/22116/) — complete official Biology/Chemistry/Physics/Math topic list, cross-referenced with sheryaar.net and thefacultyapp.com
- [WebKit blog - Designing for iPhone X](https://webkit.org/blog/7929/designing-websites-for-iphone-x/) — `env(safe-area-inset-bottom)` and `viewport-fit=cover` documentation (official Apple/WebKit source)
- [MDN - Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) — SSE MIME type requirements

### Tertiary (LOW confidence)
- [HTMX GitHub issue #2388](https://github.com/bigskysoftware/htmx/issues/2388) — HTMX SSE not working on Safari iOS 17.4 (confirms project's decision to use vanilla EventSource)
- [WebSearch results] — iOS Safari 100vh and safe area inset behavior; multiple sources agree on `env(safe-area-inset-bottom)` approach

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all existing libraries already in use and verified
- Architecture patterns: HIGH — patterns taken directly from working codebase code
- Syllabus coverage gaps: MEDIUM — topic list from multiple prep sites cross-referencing official MUR decree structure; exact physics/math frequency is estimated
- Mobile pitfalls: MEDIUM — CSS issues identified from static analysis; confirmation requires live iPhone testing
- SSE Safari compatibility: HIGH — confirmed via official MDN + HTMX issue tracker; current implementation is already correct

**Research date:** 2026-02-28
**Valid until:** 2026-03-30 (stable: iOS Safari behavior and MUR syllabus don't change on short timescales)
