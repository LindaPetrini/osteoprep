# Roadmap: OsteoPrep

## Overview

OsteoPrep delivers four phases under a 3-week hard deadline. Phase 1 establishes the bilingual schema, AI content pipeline, and persistence layer — the foundation everything else depends on. Phase 2 adds the active learning loop: FSRS flashcards, topic quizzes, and past exam questions. Phase 3 completes the study experience with a progress dashboard and streaming AI chat. Phase 4 ensures full exam syllabus coverage across all topic areas and validates the mobile experience on real iPhone hardware.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation and Content Pipeline** - Bilingual schema, AI explainer generation with caching, mobile base UI, topic browsing
- [x] **Phase 2: Active Learning** - FSRS flashcards (7-day cap), topic quizzes, past exam question bank (completed 2026-02-28)
- [x] **Phase 3: Progress and AI Chat** - Study dashboard, streaming chat with topic context injection (completed 2026-02-28)
- [x] **Phase 4: Coverage Completion and Mobile Polish** - All MUR exam topics covered, iPhone Safari validated (completed 2026-02-28)

## Phase Details

### Phase 1: Foundation and Content Pipeline
**Goal**: User can browse exam topics and read AI-generated explainers in Italian or English, with all content cached on first generation
**Depends on**: Nothing (first phase)
**Requirements**: CONT-01, CONT-02, CONT-03, CONT-04, PROG-03
**Success Criteria** (what must be TRUE):
  1. User can open the app on iPhone Safari and see topics organized by subject (Biology, Chemistry)
  2. User can tap a topic and read an AI-generated explainer — subsequent loads are instant (served from cache, no API call)
  3. User can toggle between Italian and English versions of any explainer without losing their place
  4. Explainers include explicit uncertainty markers where AI confidence is low (no fabricated facts stated as certain)
  5. Progress data (SRS state, quiz scores, completed sections) survives a server restart
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Project scaffold, SQLite schema with bilingual columns, Alembic migrations, Nginx/Uvicorn/systemd setup
- [x] 01-02-PLAN.md — Topic browsing UI, subject accordions, AI explainer generation + caching, language toggle, uncertainty markers

### Phase 2: Active Learning
**Goal**: User can reinforce knowledge through FSRS flashcard reviews, topic quizzes with explanations, and practice with real past exam questions
**Depends on**: Phase 1
**Requirements**: QUIZ-01, QUIZ-02, QUIZ-03, QUIZ-04, CARD-01, CARD-02, CARD-03, CARD-04, EXAM-01, EXAM-02, EXAM-03, EXAM-04
**Success Criteria** (what must be TRUE):
  1. User can review flashcards for nomenclature (cell parts, compounds, anatomical terms), rate each card (Again / Hard / Good / Easy), and cards are rescheduled — no card is scheduled more than 7 days out
  2. SRS card state (due date, stability, difficulty) is intact after a server restart
  3. User can take a multiple-choice quiz after a topic section and see per-answer explanations for both correct and wrong options
  4. Quiz scores are saved and visible (user can see their score history)
  5. User can access past Italian exam questions and take a timed practice test; after completing, they see correct answers with AI-generated explanations
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — FSRS engine integration (py-fsrs, 7-day interval cap), flashcard schema, card review UI (flip, 4-button rating)
- [ ] 02-02-PLAN.md — Topic quiz: 15+ seeded Italian MCQs, quiz router, per-answer AI explanations, score history (QUIZ-01 through QUIZ-04)
- [ ] 02-03-PLAN.md — Practice exam: 20+ seeded Italian MCQs, timed exam UI with countdown, auto-submit, AI explanations, attempt persistence (EXAM-01 through EXAM-04)

### Phase 3: Progress and AI Chat
**Goal**: User can see their overall study progress at a glance and ask Claude questions about any topic with responses that stream in real time
**Depends on**: Phase 2
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, PROG-01, PROG-02
**Success Criteria** (what must be TRUE):
  1. User can open a dashboard and see completed topics, quiz accuracy by subject, and SRS card counts (due today, learned, new)
  2. Each topic in the topic list shows completion status (not started / reading / quiz passed)
  3. User can open an AI chat panel from any topic page and ask a question — Claude's response streams in word by word (no waiting for full response)
  4. When chat is opened from a topic page, Claude already knows which topic is being studied without the user having to explain
  5. User can ask "which topics am I weakest on?" and Claude responds with accurate context from their quiz and SRS history
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md — Progress dashboard (/progress): topic completion counts, quiz accuracy by subject, SRS card counts; topic list completion badges (PROG-01, PROG-02)
- [x] 03-02-PLAN.md — Streaming AI chat: SSE endpoint, topic context injection, progress-aware system prompt, chat panel on topic pages (CHAT-01 through CHAT-04)

### Phase 4: Coverage Completion and Mobile Polish
**Goal**: Every topic area on the official MUR exam syllabus has an explainer and at least one quiz, and the full app is verified to work on iPhone Safari
**Depends on**: Phase 3
**Requirements**: CONT-01, CONT-02 (full syllabus scope), QUIZ-01 (full syllabus scope)
**Success Criteria** (what must be TRUE):
  1. Every topic area from the official MUR professioni sanitarie curriculum (Biology, Chemistry, Physics/Math basics) has an AI-generated explainer and at least one quiz available
  2. All interactive elements (flashcard flip, quiz submission, chat input, language toggle) work correctly on iPhone Safari without layout breakage
  3. All tap targets are at minimum 44px and body text is at minimum 16px (readable without zoom on iPhone)
**Plans**: 2 plans

Plans:
- [ ] 04-01-PLAN.md — Seed all missing topics (mitocondri fix, anatomy/physiology biology, extra chemistry, full physics/math set); fix 3 iPhone Safari mobile issues (prose font size, chat input tap target, language toggle inline style)
- [ ] 04-02-PLAN.md — Seed quiz questions for all 14 previously-uncovered biology/chemistry topics and all 10 new physics/math topics

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Content Pipeline | 2/2 | Complete   | 2026-02-28 |
| 2. Active Learning | 3/3 | Complete   | 2026-02-28 |
| 3. Progress and AI Chat | 2/2 | Complete   | 2026-02-28 |
| 4. Coverage Completion and Mobile Polish | 2/2 | Complete   | 2026-02-28 |
