# Requirements: OsteoPrep

**Defined:** 2026-02-28
**Core Value:** Cover the key Italian osteopathy exam topics effectively in 3 weeks through AI-generated explanations, spaced repetition, and practice with real exam formats.

## v1 Requirements

### Content

- [x] **CONT-01**: User can browse study topics organized by subject (Biology, Chemistry, Physics/Math, Logic)
- [x] **CONT-02**: User can read an AI-generated explainer for each topic, generated on first access and cached in the database
- [x] **CONT-03**: User can toggle between Italian and English versions of any explainer
- [x] **CONT-04**: Explainers include hallucination mitigation (AI expresses uncertainty where appropriate, links to authoritative sources where possible)

### Quizzes

- [x] **QUIZ-01**: User can take a multiple-choice quiz after completing a topic section
- [x] **QUIZ-02**: Each quiz question shows which answers are correct and why (AI-generated explanation per answer choice)
- [x] **QUIZ-03**: Wrong answers are explained — user sees why each wrong option is incorrect
- [x] **QUIZ-04**: Quiz scores are saved and visible in progress tracking

### Flashcards

- [x] **CARD-01**: User can study flashcards for nomenclature (cell parts, chemical compounds, anatomical terms) using spaced repetition
- [x] **CARD-02**: SRS uses FSRS-5 algorithm with review intervals capped at 7 days (to keep reviews within exam study window)
- [x] **CARD-03**: User rates each card (Again / Hard / Good / Easy) and cards are rescheduled accordingly
- [x] **CARD-04**: SRS state (due date, stability, difficulty) persists across server restarts

### Past Exam Questions

- [ ] **EXAM-01**: User can access a bank of past exam questions from Italian medicina and professioni sanitarie entry tests
- [ ] **EXAM-02**: User can take a timed practice test from the question bank
- [ ] **EXAM-03**: After answering, user sees correct answer with AI-generated explanation of why it is correct and why each wrong option is wrong
- [ ] **EXAM-04**: User's practice test history and per-question results are saved

### AI Chat

- [ ] **CHAT-01**: User can open an AI chat interface to ask questions about any study topic
- [ ] **CHAT-02**: Chat responses stream in real time (SSE — no waiting for full response)
- [ ] **CHAT-03**: Chat is context-aware — when accessed from a topic page, Claude knows which topic the user is studying
- [ ] **CHAT-04**: User can ask about their own progress ("which topics am I weakest on?") and Claude can respond with context

### Progress

- [ ] **PROG-01**: User can view a dashboard showing completed topics, quiz scores per subject, and SRS card counts (due today, learned, new)
- [ ] **PROG-02**: Each topic shows completion status (not started / reading / quiz passed)
- [x] **PROG-03**: Progress data persists across sessions (server-side SQLite storage)

## v2 Requirements

### Enhanced Content

- **CONT-05**: User can request deeper explanations or simpler explanations for any topic
- **CONT-06**: Admin (self) can manually edit or override AI-generated content
- **CONT-07**: Physics and Math topic coverage (lower exam ROI — deprioritized per research)

### Enhanced Flashcards

- **CARD-05**: User can create custom flashcards from any explainer text
- **CARD-06**: Flashcard deck export (Anki-compatible format)

### Enhanced Practice

- **EXAM-05**: Adaptive quiz mode — questions prioritized by weakness areas
- **EXAM-06**: Full mock exam mode (timed, 60 questions, official format)

### Social / Sharing

- **SHAR-01**: Share a topic explainer link (for sharing with friends)

## Out of Scope

| Feature | Reason |
|---------|--------|
| User accounts / login | Single-user app — auth adds complexity with zero benefit |
| Native iOS app | Web app on iPhone is sufficient, avoids App Store process |
| Offline mode | Requires service workers + content sync — too much complexity |
| Video content | Adds storage/bandwidth complexity, text is sufficient for exam prep |
| Gamification (badges, streaks) | Nice-to-have but scope creep for 3-week deadline |
| Admin panel | Single user — direct DB access sufficient |
| Real-time collaboration | Single user |
| Note-taking / wiki | Out of core study loop |
| OpenRouter integration | May add later, but Claude API sufficient for now |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONT-01 | Phase 1 | Complete (01-01) |
| CONT-02 | Phase 1 | Complete (01-02) |
| CONT-03 | Phase 1 | Complete (01-02) |
| CONT-04 | Phase 1 | Complete (01-02) |
| QUIZ-01 | Phase 2 | Complete |
| QUIZ-02 | Phase 2 | Complete |
| QUIZ-03 | Phase 2 | Complete |
| QUIZ-04 | Phase 2 | Complete |
| CARD-01 | Phase 2 | Complete (02-01) |
| CARD-02 | Phase 2 | Complete (02-01) |
| CARD-03 | Phase 2 | Complete (02-01) |
| CARD-04 | Phase 2 | Complete (02-01) |
| EXAM-01 | Phase 2 | Pending |
| EXAM-02 | Phase 2 | Pending |
| EXAM-03 | Phase 2 | Pending |
| EXAM-04 | Phase 2 | Pending |
| CHAT-01 | Phase 3 | Pending |
| CHAT-02 | Phase 3 | Pending |
| CHAT-03 | Phase 3 | Pending |
| CHAT-04 | Phase 3 | Pending |
| PROG-01 | Phase 3 | Pending |
| PROG-02 | Phase 3 | Pending |
| PROG-03 | Phase 1 | Complete (01-01) |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

**Note on Phase 4:** Phase 4 (Coverage Completion and Mobile Polish) is an execution phase that ensures CONT-01, CONT-02, and QUIZ-01 are fulfilled at full MUR syllabus breadth. It introduces no new requirement IDs — it delivers on the scope already declared by those requirements.

---
*Requirements defined: 2026-02-28*
*Last updated: 2026-02-28 after roadmap creation*
