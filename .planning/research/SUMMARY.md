# Project Research Summary

**Project:** OsteoPrep — Italian Osteopathy/Medicine Entry Exam Prep App
**Domain:** AI-powered single-user exam preparation web app (Italian "Professioni Sanitarie" / osteopathy)
**Researched:** 2026-02-28
**Confidence:** HIGH

## Executive Summary

OsteoPrep is a private, single-user web app that helps one person prepare for the Italian osteopathy entry exam in roughly 3 weeks. The exam follows the standardized "Test Professioni Sanitarie" format: 60 multiple-choice questions across Biology, Chemistry, Physics/Math, and Logic, administered nationally. The right architectural framing is a simple Python monolith (FastAPI + SQLite) with server-side rendering (HTMX + Jinja2), no auth layer, no JS build pipeline, and no separate database process. All complexity that doesn't directly produce exam-ready content is out of scope. The tech stack is fully verified against current package versions and official documentation; all recommended choices are high-confidence.

The recommended approach delivers three core loops in priority order: (1) read AI-generated topic explanations organized by exam syllabus; (2) practice with AI-generated multiple-choice quizzes and past exam questions; (3) review flashcards via FSRS spaced repetition tuned for a hard 3-week deadline. The AI differentiator — generating on-demand explanations calibrated to the exam level — is absent from all Italian platforms (Testbusters, JustQuiz, AlphaTest), making it the app's primary value over static book content. Bilingual support (Italian primary, English secondary) is baked into the data model from day 1, not retrofitted.

The principal risks are not technical: they are AI hallucination on chemistry/anatomy facts (4–15% error rate in medical domains), scope creep consuming development time that should go to content coverage, and SRS scheduling that sends cards past the exam date. All three are solvable with clear rules applied in Phase 1: a strict system prompt with uncertainty-acknowledgment instructions, a hard content-coverage checklist gating all phase completions, and a 7-day maximum interval cap on the FSRS scheduler.

---

## Key Findings

### Recommended Stack

The stack is a cohesive Python-first monolith optimized for a solo developer under time pressure. FastAPI (0.115.x) provides async-native routing with built-in Jinja2 templating, making it the right backbone for an app that needs SSE streaming for Claude responses and server-side HTML rendering for HTMX. SQLite (with WAL mode via aiosqlite + SQLAlchemy 2.0) is the correct database choice: zero-configuration, single-file, trivially backed up — PostgreSQL adds operational overhead with zero benefit for a single-user deployment. The Anthropic Python SDK (0.84.0) is used directly without LangChain abstraction; for a single-provider, single-use-case integration, the SDK alone is cleaner and better documented. The FSRS-5 algorithm (py-fsrs / `fsrs` on PyPI) replaces SM-2 because it delivers 20–30% fewer daily reviews for equivalent retention — critical when study time is limited. The frontend stack (HTMX 2.0 + DaisyUI 4 + Tailwind CDN) eliminates the npm build pipeline entirely; all three are loaded from CDN in the base template.

**Core technologies:**
- FastAPI 0.115.x: HTTP API + SSE streaming + Jinja2 templates — async-native Python framework, ideal for Claude API streaming
- Uvicorn + Gunicorn: ASGI server with process management — standard production setup for FastAPI on Linux
- SQLite + aiosqlite + SQLAlchemy 2.0: primary data store — zero-config, single-file, WAL mode handles async reads
- Alembic 1.13.x: schema migrations — safe schema changes without data loss during development
- anthropic 0.84.0: Claude API client — official SDK, AsyncAnthropic for non-blocking streaming
- py-fsrs (fsrs on PyPI): FSRS-5 spaced repetition algorithm — more accurate and actively maintained vs SM-2
- HTMX 2.0 + DaisyUI 4 + Tailwind CDN: mobile-first frontend — no build step, works with server-rendered HTML fragments
- Nginx + Tailscale: HTTPS reverse proxy + private iPhone access — server already on Tailscale, MagicDNS cert provisioned via `tailscale cert`

See `.planning/research/STACK.md` for complete rationale and installation commands.

### Expected Features

The Italian exam prep market (Testbusters, JustQuiz, AlphaTest, QuizAmmissione.it) universally provides question banks, exam simulations, subject filtering, and progress stats. OsteoPrep's AI-generated explanations, SRS flashcards, and bilingual toggle are genuine differentiators — none appear in any Italian platform surveyed. The exam is a breadth test (60 questions across 4 subjects), not a depth test, which means content coverage across all topics is more important than depth on any single topic.

**Must have (table stakes):**
- Multiple-choice practice questions with correct/incorrect feedback — mirrors the exam format
- Per-subject filtering (Biology, Chemistry, Physics/Math, Logic/General Culture) — users need to drill weak areas
- Progress visibility (quiz scores, cards mastered per subject) — prevents anxiety from invisible progress
- Past exam questions — Italian platforms universally include these; adds credibility
- Mobile-friendly UI with large tap targets — app is used on iPhone; broken mobile means broken app
- Session persistence (SRS state, quiz scores survive page reload) — progress loss is demoralizing
- Topic-organized content following the exam syllabus — users study one topic at a time

**Should have (differentiators):**
- AI-generated topic explainers on demand — Italian platforms serve static books; Claude generates calibrated, current explanations
- AI chat for concept clarification — students get stuck at 11pm with no one to ask; 95.7% effectiveness in research
- Spaced repetition flashcards with FSRS (exam-deadline mode, 7-day cap) — no Italian platform offers SRS
- Exam-deadline-aware scheduling — FSRS with interval cap ensures all cards surface before exam, not after
- Bilingual content toggle (Italian primary, English secondary) — no Italian platform offers this
- AI-generated quiz questions on specific sub-topics — unlimited practice on any sub-topic beyond past papers

**Defer (v2+):**
- Physics and Mathematics deep coverage — lower exam weight; cover basics only in MVP
- Logic and General Culture section — lowest ROI for 3-week prep
- Gamification (badges, streaks, XP) — 1-2 weeks of UI work for marginal study value
- Offline mode — requires service workers and sync complexity; server is always accessible
- Native iOS app — web app on iPhone is equivalent for this use case

**Anti-features (never build):**
- User auth / accounts — single user, zero value, weeks of work
- Admin panel / content editor — AI generates content dynamically
- Social features, adaptive difficulty engine, full note-taking wiki

See `.planning/research/FEATURES.md` for subject coverage priorities and feature dependency tree.

### Architecture Approach

The architecture is a single Python monolith: FastAPI serves static files, HTML fragments (via Jinja2), and a REST + SSE API. All Claude API calls happen server-side (API key never in browser). SQLite stores all persistent state including fully normalized FSRS card state. There is no separate frontend server, no auth layer, and no build step. The SRS engine is a pure function (card state + rating → new card state) that touches no database directly; the router calls it and persists the result. AI-generated content (topic explainers, quiz questions, flashcards) is generated once and cached in SQLite permanently — subsequent page loads are instant with zero API cost. Streaming (SSE via `StreamingResponse`) is used only for the AI chat interface where latency is user-visible.

**Major components:**
1. FastAPI Router — routes HTTP requests, validates input, calls downstream services, returns HTML fragments or JSON
2. Claude Service — builds prompts, calls Anthropic API, streams responses; prompt templates are the primary engineering surface
3. SRS Engine — pure FSRS logic module (no DB access); takes card state + rating, returns updated state for the router to persist
4. DB Layer (SQLAlchemy + SQLite) — CRUD for all state: topics, flashcards, card_state, review_log, quiz_questions, quiz_attempts, study_sessions, settings
5. Content Store — cached AI-generated content (topic explainers, quiz questions); generate-once pattern
6. Static Frontend — HTMX + Jinja2 templates rendered by FastAPI; no separate server

**Key data models:** `topics` (slug, title_it/en, content_it/en, subject), `flashcards` (front_it/en, back_it/en, card_type), `card_state` (all FSRS fields: stability, difficulty, due, state, reps, lapses), `review_log` (audit trail for analytics/optimizer), `quiz_questions` (source: generated | past_exam, all options + correct + explanations in both languages), `quiz_attempts`, `study_sessions`, `settings`.

See `.planning/research/ARCHITECTURE.md` for full data models, API endpoint list, and data flow diagrams.

### Critical Pitfalls

1. **AI hallucination on medical/science content** — Claude generates fluent but wrong facts in medical domains (4–15% error rate). Prevention: system prompt with explicit uncertainty-acknowledgment instructions ("say 'I am not certain' rather than guessing"); chain-of-thought prompting for explanations; never treat AI output as ground truth for specific numerical values. Address in Phase 1 before generating any content.

2. **SRS scheduling past the exam deadline** — Standard FSRS is designed for multi-year retention; most cards scheduled past a 3-week window are wasted effort. Prevention: cap all intervals at 7 days maximum; show upcoming review load prominently; limit new cards per day to 20–30. Address in Phase 1 (algorithm design decision).

3. **Scope creep consuming development time** — Developer is also user; every test session surfaces "small" improvements that each cost 2–4 hours. Prevention: hard rule — all exam topic areas must have at least one explainer and one quiz before any polish work; maintain a "parking lot" for features; time-box phases strictly. Affects every phase.

4. **Bilingual content as afterthought** — Building English-first then retrofitting Italian requires changing schema, prompts, and 10+ code paths. Prevention: design `content_it`/`content_en` dual columns into every model from day 1; language preference in a single settings location; Italian is the default and primary language. Address in Phase 1.

5. **API cost runaway** — Regenerating Claude content on every page load or adding chatty generation triggers inflates costs unpredictably. Prevention: generate-once-and-cache pattern for all content; "regenerate" is an explicit user action; log token usage during development. Address in Phase 1.

---

## Implications for Roadmap

Based on combined research, the natural phase structure follows the critical dependency chain: **persistence and schema** → **content pipeline** → **active learning** → **polish and AI chat**. Content coverage (having explainers and quizzes for all exam topics) is the only non-negotiable deliverable; everything else is secondary.

### Phase 1: Foundation and Content Pipeline

**Rationale:** The entire app depends on the data schema and the AI content generation pipeline. Building these incorrectly (missing language columns, no caching, wrong SRS algorithm choice) forces rewrites. The schema must be bilingual from day 1. The generate-once-and-cache pattern must be established before any content is generated.

**Delivers:** Working FastAPI app with SQLite, mobile-responsive base template, topic list with subject groupings, AI-generated topic explanations (Biology + Chemistry priority), generate-and-cache pattern, language toggle wired to settings.

**Addresses (from FEATURES.md):** Topic-organized content, AI-generated explainers, bilingual toggle foundation, mobile-friendly UI baseline.

**Avoids (from PITFALLS.md):** Bilingual schema omission (Pitfall 5), API cost runaway from re-generation (Pitfall 7), SRS wrong algorithm choice (Pitfall 2), persistence failure (Pitfall 8). System prompt with uncertainty-acknowledgment instructions established here (Pitfall 1).

**Research flag:** Standard patterns — FastAPI + SQLite + Jinja2 is a well-documented combination. No additional research needed. Prompt engineering quality for topic explainers should be validated empirically.

### Phase 2: Active Learning (SRS + Quizzes)

**Rationale:** Once content exists, the active recall loop (flashcards and quizzes) is the primary study mechanism. SRS state persistence is a hard dependency for all future study sessions — establishing it early prevents data loss risk. Past exam questions add credibility and exam familiarity.

**Delivers:** FSRS flashcard system with 7-day interval cap and exam-deadline awareness, card review session UI (tap to flip, 4-button rating), AI-generated multiple-choice quiz questions per topic, correct/incorrect feedback with explanation, past exam question import, quiz history.

**Addresses (from FEATURES.md):** Spaced repetition flashcards, exam-deadline SRS scheduling, multiple-choice practice questions, past exam questions, session persistence.

**Avoids (from PITFALLS.md):** SRS scheduling past exam date (Pitfall 2 — 7-day cap), SRS card debt from over-generation (Pitfall 6 — 20 cards/topic cap), bad distractor quality (Pitfall 3 — explicit prompting for plausible-but-wrong answers with explanations), past exam questions with wrong answers (Pitfall 9 — Claude-verified explanations), flashcard front-back confusion (Pitfall 12 — bidirectional cards for nomenclature).

**Research flag:** FSRS integration is straightforward (20 lines of Python, documented in ARCHITECTURE.md). Quiz prompt engineering quality needs empirical testing — generate a sample batch and verify distractor quality before scaling. No additional research phase needed.

### Phase 3: Progress Tracking and AI Chat

**Rationale:** Progress visibility is table stakes (users need to feel they're advancing) but depends on quiz and SRS data existing first. AI chat is the highest-complexity feature (SSE streaming + prompt caching) and the most differentiating one — but it only works well once topic content exists to inject as context.

**Delivers:** Progress dashboard (topics covered, SRS due/total, quiz accuracy by subject), study session logging, SSE streaming AI chat with topic context injection, Claude prompt caching for system prompts, typing indicator in chat UI.

**Addresses (from FEATURES.md):** Progress visibility, AI chat for concept clarification, per-subject progress stats.

**Avoids (from PITFALLS.md):** Progress state loss (Pitfall 8 — all state persisted in SQLite before this phase). API costs managed via prompt caching for repeated system prompts (Pitfall 7).

**Research flag:** SSE streaming in FastAPI is well-documented (code pattern in STACK.md). Claude prompt caching setup is documented in official Anthropic docs. No additional research phase needed.

### Phase 4: Content Coverage Completion and Mobile Polish

**Rationale:** Content coverage (every exam topic area has at least one explainer and quiz) is the only deliverable that directly determines exam performance. This phase ensures the app is complete as a study tool, not just as software. Mobile polish is validated on real iPhone since DaisyUI mobile defaults are a baseline, not a guarantee.

**Delivers:** All exam topic areas from the official MUR curriculum list have explainers and quizzes generated. Physics/Math basics added. Logic/General Culture stub content. iPhone Safari tested for every interaction (flashcard flip, quiz submission, AI chat). Touch target audit (44px minimum). Font size audit (16px minimum body, 18px for content).

**Addresses (from FEATURES.md):** Full subject coverage (Biology P1, Chemistry P2, Physics/Math P3, Logic P4), mobile-friendly UI.

**Avoids (from PITFALLS.md):** Topic coverage gaps discovered late (Pitfall 11 — official curriculum checklist), mobile UX broken on iPhone (Pitfall 10 — test on real device each session), content regeneration changing answers mid-study (Pitfall 13 — regenerate is explicit user action only), scope creep (Pitfall 4 — no new features until coverage is 100%).

**Research flag:** Content coverage is a curriculum knowledge problem, not a software problem. The official MUR topic list (publicly available) should be imported as a checklist in Phase 1. No research phase needed.

### Phase Ordering Rationale

- Phase 1 before everything: schema changes later are expensive; bilingual columns and caching strategy must be correct from the first line of code.
- Phase 2 before Phase 3: AI chat needs topic content to inject as context; progress tracking needs quiz and SRS data to display.
- Phase 4 last: content coverage completion is only possible after the generation pipeline (Phase 1) and quiz/flashcard systems (Phase 2) are working end-to-end. Mobile polish done last because DaisyUI handles most of it, but real-device validation reveals the exceptions.
- Biology and Chemistry content in Phase 1: highest exam weight, must be covered first in case time runs short.

### Research Flags

Phases with well-documented patterns (no `research-phase` needed):
- **Phase 1:** FastAPI + SQLite + Jinja2 + HTMX is a proven combination with reference implementations. Prompt templates are the creative work, not the integration.
- **Phase 2:** py-fsrs integration is 20 lines of Python. Quiz generation follows documented MCQ prompting patterns.
- **Phase 3:** SSE streaming pattern documented in STACK.md. Claude prompt caching in official Anthropic docs.
- **Phase 4:** Curriculum coverage is content work, not engineering research.

Phases needing empirical validation (not external research, but internal testing):
- **Phase 1 prompt quality:** Generate 5–10 topic explainers and manually check for hallucinations before generating the full set.
- **Phase 2 distractor quality:** Generate a sample quiz batch and review distractor plausibility before scaling to all topics.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified against PyPI (Feb 2026). Official docs consulted for FastAPI, SQLAlchemy, py-fsrs, Anthropic SDK, HTMX, Tailscale. Reference implementations exist. |
| Features | MEDIUM-HIGH | Italian exam platforms verified via direct research. Exam syllabus sourced from official MUR program documents. AI chat effectiveness from peer-reviewed MDPI study. Feature priorities are well-reasoned but depend on one user's study style. |
| Architecture | HIGH | Patterns are well-established for this problem type. Data models are complete and internally consistent. FSRS integration code verified against py-fsrs docs. |
| Pitfalls | HIGH | Hallucination risk rates sourced from 2025 medRxiv and BMC Medical Education peer-reviewed papers. SRS deadline pitfall sourced from algorithm comparison literature. Scope creep advice is universal and confirmed in domain literature. |

**Overall confidence:** HIGH

### Gaps to Address

- **Exact topic list for content generation:** The official MUR curriculum list should be imported as a structured checklist (JSON or DB seed) in Phase 1 before generating any content. Do not rely on memory or approximation of the syllabus.
- **Prompt quality validation:** The hallucination mitigation strategy (chain-of-thought, uncertainty prompting) needs empirical testing on 5–10 sample topics before scaling. No amount of system-prompt engineering is a substitute for human review of the first batch of generated content.
- **FSRS interval cap tradeoff:** The 7-day cap sacrifices FSRS's long-term optimization in exchange for deadline-aware behavior. This is the right tradeoff for a 3-week sprint, but should be confirmed with the user before implementing — a user who plans to continue studying after the exam might prefer a different setting.
- **Past exam question sources:** Sourcing high-quality past exam questions requires identifying authoritative Italian repositories (official MUR PDFs, Alpha Test materials). This is a content sourcing task, not a software task, but it gates Phase 2's past-exam feature. Verify sources before building the import mechanism.

---

## Sources

### Primary (HIGH confidence)
- FastAPI official docs: https://fastapi.tiangolo.com/deployment/server-workers/
- Anthropic Python SDK: https://github.com/anthropics/anthropic-sdk-python
- Anthropic Streaming docs: https://platform.claude.com/docs/en/build-with-claude/streaming
- Anthropic Prompt Caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Anthropic Reduce Hallucinations: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
- py-fsrs GitHub: https://github.com/open-spaced-repetition/py-fsrs
- SQLAlchemy async docs: https://fastapi.tiangolo.com/tutorial/sql-databases/
- Tailscale HTTPS certs: https://tailscale.com/docs/how-to/set-up-https-certificates
- DaisyUI + HTMX guide: https://daisyui.com/docs/install/htmx/
- Italian MUR exam program (official): https://www.mim.gov.it/documents/20182/1390866/DM+n.277+del+28-03-2019+-+allegatoA+e+B.pdf

### Secondary (MEDIUM confidence)
- Medical hallucination in foundation models (2025 medRxiv): https://www.medrxiv.org/content/10.1101/2025.02.28.25323115v1.full
- AI-generated MCQ quality in health science (2025 BMC Medical Education): https://bmcmededuc.biomedcentral.com/articles/10.1186/s12909-025-06881-w
- FSRS vs SM-2 comparison: https://memoforge.app/blog/fsrs-vs-sm2-anki-algorithm-guide-2025/
- Testbusters platform review: https://www.testbusters.it/test-ammissione/professioni-sanitarie
- JustQuiz platform review: https://www.justquiz.it/app/professioni-sanitarie.html
- Programma test professioni sanitarie 2025: https://www.ammissione.it/area-sanitaria/programma-materie-studio/22116/
- AI chatbot effectiveness study (MDPI 2025): https://www.mdpi.com/2227-7102/15/1/26
- RemNote Exam Scheduler: https://help.remnote.com/en/articles/9102040-understanding-the-exam-scheduler

### Tertiary (informational)
- FastAPI HTMX DaisyUI reference app: https://github.com/sunscrapers/fastapi-htmx-daisyui
- FSRS awesome list: https://github.com/open-spaced-repetition/awesome-fsrs
- Feature creep mitigation: https://www.designrush.com/agency/software-development/trends/feature-creep

---

*Research completed: 2026-02-28*
*Ready for roadmap: yes*
