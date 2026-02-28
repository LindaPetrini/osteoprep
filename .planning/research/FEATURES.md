# Feature Landscape

**Domain:** Science/medicine entry exam preparation web app (Italian context)
**Researched:** 2026-02-28
**Confidence:** MEDIUM-HIGH — Italian platforms verified via search, SRS features verified via official docs, AI chat features from academic research.

---

## Context: The Italian Exam Landscape

The target exam is the Italian osteopathy entry test, structurally identical to the **Test Professioni Sanitarie** and the Italian-language medicine exam. These are standardized multiple-choice exams administered nationally.

**Exam format (Professioni Sanitarie / Osteopatia):**
- 60 multiple-choice questions, 5 options, single correct answer
- Duration: ~100 minutes
- Subjects by weight (approximate):
  1. **Biology** (most questions) — cell biology, genetics, molecular biology, biochemistry, human anatomy and physiology, animal tissues, homeostasis
  2. **Chemistry** (second most) — atomic structure, periodic table, bonding, stoichiometry, equilibrium, acids/bases, redox, organic chemistry (alcohols, amines, aldehydes, esters)
  3. **Physics and Mathematics** — kinematics, dynamics, thermodynamics, electricity, algebra, geometry, probability
  4. **Logic and General Culture** — logical-verbal and logical-mathematical reasoning

**Key insight:** This is a breadth test, not a depth test. The goal is covering all topic areas adequately, not mastering any single topic deeply. This has significant implications for feature priority.

---

## What Italian Exam Prep Platforms Actually Include

Research into major Italian platforms (Testbusters, JustQuiz, AlphaTest, QuizAmmissione.it):

| Platform | Core Features | Differentiators |
|----------|--------------|-----------------|
| **Testbusters** | Large question banks, full exam simulations, theory manuals, past papers from 2017+, online courses | Simulator shows if you'd pass a specific university, personalized statistics |
| **JustQuiz** | 2,300+ quizzes offline, per-subject drill, exam simulation, "Diary" with subject thermometer | Choose university/faculty for simulation, Nursing Glossary, per-subject progress visualization |
| **AlphaTest (Italian)** | Theory + exercise books, 8,000 quizzes, official past papers, simulation software | Printed materials primary, digital secondary |
| **QuizAmmissione.it** | Free online simulation, subject-filtered practice | Free tier, web-only |

**Pattern across all Italian platforms:** question banks, exam simulations, subject filtering, and progress statistics are ubiquitous. Theory content (explanations) is typically in book/PDF form, NOT dynamically generated. This is where OsteoPrep's AI generation is genuinely differentiating.

---

## Table Stakes

Features users expect from any credible exam prep tool. Missing these means the app feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Multiple-choice practice questions** | Every Italian exam prep platform has this. It's the core loop. | Low | MCQs are the exam format — practice must mirror it |
| **Correct/incorrect feedback with explanation** | Users need to learn from wrong answers, not just see a score | Low-Medium | Show why wrong answers are wrong |
| **Per-subject filtering** | Users have uneven knowledge; they need to drill weak areas | Low | Biology, Chemistry, Physics/Math, Logic/Culture |
| **Progress visibility** | Users must feel they're advancing; without this, anxiety spikes | Medium | Quiz scores, sections completed, cards mastered |
| **Past exam questions** | Italian platforms universally include official past papers | Medium | Adds credibility and exam familiarity |
| **Mobile-friendly UI** | This app is used on iPhone; small screen reading must work | Low-Medium | Responsive layout, large tap targets |
| **Session persistence** | Progress lost between sessions is demoralizing | Medium | SRS state, quiz scores, completed sections |
| **Topic-organized content** | Users expect to study one topic at a time, not random content | Low | Organized by the exam syllabus structure |

---

## Differentiators

Features that set OsteoPrep apart from the Italian platforms above. None of these are common in the Italian exam prep market.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **AI-generated topic explainers (on demand)** | Italian platforms serve static books/PDFs. AI generates clear, current explanations calibrated to exam level. | Medium | Claude API; prompt engineering is the real work |
| **AI chat for clarification** | Students get stuck and have no one to ask at 11pm. Immediate explanation of any concept. Research shows 95.7% effectiveness for concept understanding. | Medium | Claude API conversation with context |
| **Spaced repetition flashcards (SRS)** | No Italian exam prep platform includes SRS. Anki-style review is proven superior for nomenclature retention. | Medium | Use ts-fsrs (TypeScript FSRS implementation); exam-deadline mode is particularly useful here |
| **Bilingual content (IT/EN)** | The user thinks in English on some concepts and Italian on others. No Italian platform offers this. | Low-Medium | Toggle per section or globally; store both in content model |
| **Exam-deadline-aware SRS scheduling** | FSRS with a 3-week deadline horizon ensures all cards surface before the exam date, not after | Medium | RemNote calls this "Exam Scheduler" mode; FSRS supports it natively |
| **AI-generated questions on specific topics** | Can generate unlimited practice questions on any sub-topic, not just past paper bank | Medium | Useful when past papers on a specific subtopic are exhausted |

---

## Anti-Features

Things to deliberately NOT build for a 3-week deadline. These are scope traps that cost time without returning study value.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **User authentication / accounts** | Single user. Auth adds sessions, password recovery, security surface. Weeks of work for zero value. | Static single-user app, no login |
| **Content editor / admin panel** | Tempting but unnecessary — AI generates content dynamically. | Direct Claude API calls per request |
| **Social features (leaderboards, sharing)** | Single user. Zero value. | Skip entirely |
| **Offline mode** | Requires service workers, cache invalidation, sync logic. The server is always accessible. | Require internet; server is on Hetzner |
| **Video content** | Production is slow, files are large, playback is complex. Text explanations from Claude are faster to build and consume. | Text + diagrams only |
| **Native iOS app** | App Store submission is days/weeks. Web app on iPhone is equivalent for this use case. | PWA-capable web app |
| **Gamification (badges, streaks, XP)** | Nice but consumes 1-2 weeks of UI work. Progress stats are enough for a solo user. | Simple percentage/score display |
| **Adaptive difficulty engine** | SRS already adapts. A separate difficulty model adds complexity with marginal gain for a 3-week prep. | Trust FSRS to handle it |
| **Full note-taking / wiki** | Out of scope. The user needs to practice and understand, not take free-form notes. | AI chat covers Q&A needs |
| **Physics/Math quizzes (full depth)** | Biology and Chemistry are highest-weight. Physics/Math are lower priority for time-constrained prep. | Include basics, defer deep coverage to phase 2 |

---

## Feature Dependencies

```
Topic Content (AI explainers)
    └── Section Quizzes (need topic context to generate relevant questions)
        └── Past Exam Questions (adds to quiz pool; can be separate section)
            └── Wrong-answer Explanations (need question + answer to explain)

Flashcard System (SRS)
    └── SRS State Persistence (cards are useless without state)
        └── Exam-deadline Scheduling (needs exam date + SRS state)

Progress Tracking
    ├── Quiz Score History (depends on quiz completion events)
    └── SRS Card State Summary (depends on SRS state persistence)

AI Chat
    └── Topic Context Injection (chat is much better with current topic context)

Bilingual Toggle
    ├── Topic Content (needs IT + EN variants or translation layer)
    └── Flashcards (question/answer in both languages)
```

**Critical path for MVP:** Topic content → Section quizzes → SRS flashcards → Progress tracking. AI chat and bilingual can be layered on top.

---

## MVP Recommendation

Given 3 weeks to exam, prioritize in this order:

**Must ship first (Week 1 of dev):**
1. Topic explainers — Biology, Chemistry (AI-generated, organized by exam syllabus)
2. Multiple-choice section quizzes after each topic (AI-generated + past paper questions)
3. Correct/incorrect feedback with explanation
4. SRS flashcard system with FSRS algorithm and exam-date horizon

**Must ship before exam (Week 2 of dev):**
5. Progress tracking — quiz scores, cards mastered per subject
6. Past exam questions section with official paper questions
7. AI chat for concept questions
8. Session persistence (all state survives page reload)

**Nice-to-have if time permits:**
9. Bilingual toggle (IT/EN)
10. Physics and Mathematics topic coverage (lower exam weight)
11. Logic and General Culture section

**Defer entirely:**
- Physics deep-dive
- Any social/gamification features
- Native app

---

## Subject Coverage Priority

Based on exam weight for professioni sanitarie / osteopatia:

| Subject | Exam Weight | Dev Priority | Notes |
|---------|-------------|--------------|-------|
| Biology | Highest | P1 | Cell biology, genetics, biochemistry, anatomy/physiology |
| Chemistry | Second | P2 | Organic chemistry is commonly tested and confusing |
| Anatomy | Embedded in Biology | P1 | Human systems — covered under Biology section |
| Physics/Math | Lower | P3 | Basics sufficient; not the differentiating subject |
| Logic/General Culture | Lowest for science | P4 | Less prep-able; lower ROI for 3-week window |

---

## Sources

- Testbusters professioni sanitarie platform: https://www.testbusters.it/test-ammissione/professioni-sanitarie
- JustQuiz professioni sanitarie: https://www.justquiz.it/app/professioni-sanitarie.html
- Italian MUR exam program (official topics): https://www.mim.gov.it/documents/20182/1390866/DM+n.277+del+28-03-2019+-+allegatoA+e+B.pdf
- Programma test professioni sanitarie 2025: https://www.ammissione.it/area-sanitaria/programma-test-professioni-sanitarie/22116/
- Struttura syllabus Professioni Sanitarie 2025: https://testbuddy.it/test-medico-sanitari/test-professioni-sanitarie-italiano/struttura-syllabus
- FSRS JavaScript implementation (ts-fsrs): https://github.com/open-spaced-repetition/fsrs.js
- RemNote Exam Scheduler: https://help.remnote.com/en/articles/9102040-understanding-the-exam-scheduler
- AI chatbot effectiveness in exam prep (MDPI study): https://www.mdpi.com/2227-7102/15/1/26
- Best flashcard apps comparison 2025: https://notigo.ai/blog/best-flashcard-apps-students-anki-remnote-quizlet-2025
- IMAT syllabus topics: https://medschool.it/blog/imat/imat-topics-list
