# Domain Pitfalls

**Domain:** AI-powered exam preparation web app (Italian osteopathy/medicine entry exam)
**Researched:** 2026-02-28
**Project:** OsteoPrep — 3-week deadline, Claude API, SRS flashcards, single user, self-hosted

---

## Critical Pitfalls

Mistakes in this category cause rewrites, wasted study time, or a broken app on exam day.

---

### Pitfall 1: Trusting AI-Generated Factual Content Without Verification

**What goes wrong:** Claude generates biology, chemistry, and anatomy explanations that are fluent, coherent, and confidently stated — but factually wrong. In medical/science domains, hallucination rates for top LLMs average 4.3% in best cases and reach up to 15.6% in specialized subdomains. For narrow topics underrepresented in training data (e.g., Italian-specific osteopathy curriculum details, specific enzyme nomenclature), error rates are higher. The user studies this content and internalizes the wrong information before the exam.

**Why it happens:** LLMs optimize for linguistic coherence, not factual accuracy. "Long-tail knowledge" — niche topics not heavily represented in training data — shows the highest hallucination rates. The model produces plausible-sounding answers with no mechanism for self-correction unless explicitly prompted to express uncertainty.

**Consequences:** Wrong answers learned as correct on a multiple-choice exam. Confidence in incorrect knowledge. No way to detect the error if the wrong information was studied only from Claude output.

**Prevention:**
- Add a permanent system prompt instruction: "If you are uncertain about a specific fact, say so explicitly. Never guess on anatomy, chemistry, or biology facts — state 'I am not certain about this detail'."
- For explainer content, prompt Claude to cite the specific biological/chemical principle being applied, which surfaces flawed reasoning.
- Use "chain-of-thought" prompting for explanations: ask Claude to derive the answer step-by-step from first principles rather than recalling it directly.
- Treat AI-generated content as a first draft, not ground truth. Flag any content about specific values (enzyme concentrations, exact anatomical measurements, specific molecule counts) for cross-referencing.
- When generating quiz questions, always include an explanation of why each wrong answer is wrong — this forces Claude to reason more carefully and makes errors easier to spot.
- Consider a "confidence score" system prompt instruction where Claude labels each factual claim HIGH/MEDIUM/LOW confidence inline.

**Detection (warning signs):**
- Answer explanations that contradict each other across different quiz questions on the same topic.
- Specific numerical values (pH levels, molecular weights, chromosome counts) that feel imprecise or vary across sessions.
- Explanations that use correct terminology but in logically inconsistent ways.

**Phase:** Address in Phase 1 (content generation architecture) — get the system prompt right before generating any study material.

---

### Pitfall 2: SRS Scheduling Not Designed for a 3-Week Hard Deadline

**What goes wrong:** Standard SM-2 (and especially FSRS) is designed for long-term retention over months and years. With a 3-week deadline, the algorithm will schedule many cards for review after the exam date — making them effectively useless. A user adds 100 flashcards in week 1, and SM-2 schedules most of them for review in weeks 4-8. The user misses almost all scheduled reviews and learns nothing.

**Why it happens:** SRS algorithms assume open-ended study. SM-2's ease factor and interval multiplier produce intervals of 1 day, 6 days, 15+ days, 30+ days — fine for long-term learners but poorly matched to a 21-day hard stop. The algorithm has no concept of an exam date.

**Consequences:** Cards scheduled past the exam date are wasted effort. Review load becomes unpredictable. The user may feel "behind" even when studying correctly, causing discouragement.

**Prevention:**
- Cap intervals at 7 days maximum for the 3-week deadline. Any card that would normally be scheduled beyond that gets capped. This sacrifices long-term retention optimization but is irrelevant — the goal is exam day, not 6 months from now.
- Implement a simple due-today + overdue queue so the user always sees cards that need review, not cards that won't be relevant.
- Consider an even simpler approach: skip SM-2 entirely and use a 3-bucket "Leitner box" system (wrong → tomorrow, unsure → 3 days, correct → 7 days). This is far easier to implement, requires no floating point math, and is sufficient for a 3-week timeline.
- Limit new cards per day to a number the user can realistically review (20-30 new cards/day maximum). More than this creates a review backlog that becomes impossible to clear.

**Detection (warning signs):**
- Review queue grows instead of shrinking after a few days of use.
- User adds cards but stops seeing old ones return for review.
- Scheduling dates appear after the exam date.

**Phase:** Address in Phase 1 (SRS design decision) — choose algorithm before implementation, not after.

---

### Pitfall 3: AI-Generated Quiz Questions With Bad Distractors

**What goes wrong:** Multiple-choice questions have three wrong answers that are either obviously wrong (trivially easy) or actually correct (ambiguous). Research on AI-generated MCQs in health science education shows that distractor quality is the primary failure mode — AI tends to produce implausible wrong answers ("the mitochondria is the powerhouse of the plant cell") or subtly incorrect answers that are defensible as correct. Both break the learning value of the quiz.

**Why it happens:** Generating plausible distractors requires domain knowledge to understand what a student plausibly might confuse. LLMs generate wrong answers by slightly mutating correct ones, which can accidentally produce correct answers, or by inventing entirely implausible options.

**Consequences:** Easy questions don't test real understanding. Ambiguous questions create false negatives — the user gets marked wrong for a defensible answer. Over time, trust in the quiz system erodes.

**Prevention:**
- Prompt Claude explicitly: "Generate 3 wrong answers that are plausible but definitively incorrect. Each wrong answer should represent a common misconception or a close-but-wrong variation. Do not use answers that are obviously nonsensical."
- Always include an explanation for why each wrong answer is wrong — this forces Claude to validate its own distractors and surfaces cases where a "wrong" answer is actually defensible.
- Keep quiz question count per topic reasonable (5-10 questions per topic section). Over-generating questions for topics with limited content produces repetitive or low-quality questions.
- For anatomy questions, avoid "name this structure" questions with invented structure names as distractors — Claude fabricates plausible-sounding but non-existent anatomical terms.

**Detection (warning signs):**
- Wrong answers that contain obvious keywords from the question itself.
- All three wrong answers follow the same structural pattern (e.g., "the _____ enzyme" with three made-up enzyme names).
- Explanations for wrong answers that are shorter than 1 sentence and provide no reasoning.

**Phase:** Address in Phase 1 when designing quiz generation prompts.

---

### Pitfall 4: Scope Creep Consuming the 3-Week Development Window

**What goes wrong:** Each feature seems small and reasonable: "add a study timer," "show a heatmap of topics covered," "add notes on each flashcard," "let me mark cards as favourite," "add a dark mode toggle." Each takes 2-4 hours. After a week, the core study content still isn't complete and the exam is in 2 weeks. The user has a polished settings page but no chemistry content.

**Why it happens:** The developer is also the user. Every time the developer opens the app to test, they notice something "that would be really useful." The line between "this is blocking me from studying" and "this would be nice to have" collapses.

**Consequences:** Core content coverage (the actual point of the app) gets deprioritized. The exam arrives with some topics never generated. Polished but incomplete is worse than rough but complete for an exam prep tool.

**Prevention:**
- Hard rule: the only non-negotiable deliverable is content coverage across all exam topic areas. Every other feature is evaluated against "does this help cover more topics or retain content better?"
- Write out all exam topic areas on day 1. Don't mark a phase as done until every topic area has at least one explainer and one quiz.
- Use a strict "parking lot" for feature ideas: write them down, do not build them, revisit only if core topics are 100% covered.
- Features that are genuinely blocking study (content is hard to find, navigation is broken) get fixed immediately. Features that are "nice to have" get parked.
- Time-box development phases: 1 week setup + content pipeline, 1 week content coverage, 1 week polish/review. Do not start polishing until content coverage is done.

**Detection (warning signs):**
- More than 2 days spent on UI without adding new study content.
- Feature list grows between planning sessions.
- "I'll just add this one small thing" thoughts while testing.

**Phase:** Affects every phase — establish scope discipline in Phase 1 and maintain it.

---

### Pitfall 5: Bilingual Content as an Afterthought

**What goes wrong:** The app is built entirely in English, then "Italian mode" is added later as a toggle. This leads to: hardcoded English strings in components, AI prompts that always generate English content regardless of the mode switch, flashcard fronts/backs stored in one language only, UI labels not translated, and a confusing mix of languages in the same session.

**Why it happens:** It feels simpler to build one language first and "add Italian later." But content structure and storage schema need to be designed for bilingual from the start — retrofitting is harder than building right initially.

**Consequences:** Bilingual mode works partially or is abandoned. Study sessions switch languages unexpectedly. The exam is in Italian, so if Italian content is broken, the app is less useful.

**Prevention:**
- Design the data schema from day 1 with language as a first-class attribute: `{ content_it: string, content_en: string }` rather than `{ content: string }`.
- Have the language preference stored in a single location (user settings, localStorage) and pass it as a parameter to every AI generation call.
- Build language switching into the AI prompt templates from the start: "Generate in Italian" / "Generate in English" as a parameter, not an afterthought.
- For the Italian exam context, Italian should be the default and primary language. English is supplementary for when Italian technical terms are unclear.
- Accept that some content will only exist in one language — the exam is in Italian, so Italian-only content is acceptable. English-only content is not.

**Detection (warning signs):**
- AI-generated content appears in a different language than the UI language setting.
- Flashcard backs are in a different language than fronts.
- Adding a language column to the database requires updating 10+ different code paths.

**Phase:** Address in Phase 1 (data schema design) — do not build content storage without language fields.

---

## Moderate Pitfalls

Mistakes that cause friction, wasted time, or reduced study effectiveness — but don't require rewrites.

---

### Pitfall 6: SRS Card Debt From Undisciplined Card Creation

**What goes wrong:** The user (or AI) generates too many flashcards too quickly — 200+ cards in the first day. SM-2 schedules reviews for all of them, creating a review backlog of 50-100 cards/day within a week. The user stops doing reviews because the queue is overwhelming. Cards accumulate as "overdue" and the SRS stops being useful.

**Prevention:**
- Limit AI-generated flashcard batches to 15-20 cards per topic section.
- Show the user their upcoming review load (cards due today, tomorrow, day after) before adding new cards.
- Consider a hard cap: if the 3-day review queue exceeds 60 cards, block adding new cards until the queue clears.
- Design the UI to make the review queue visible and prominent — not hidden behind navigation.

**Phase:** Address in Phase 2 (SRS implementation).

---

### Pitfall 7: API Cost Runaway From Chatty AI Requests

**What goes wrong:** The AI chat feature and on-demand content generation are called on every page load, every topic open, every flashcard flip. Claude API costs add up quickly. A 3-week study session with heavy usage could cost significantly more than expected if requests are not rate-limited or cached.

**Prevention:**
- Generate content once and persist it to the database. Never regenerate content that already exists unless explicitly requested.
- Cache AI-generated explainers, quizzes, and flashcards server-side. Treat generated content as a permanent asset.
- Add a "regenerate" button as a deliberate action, not triggered automatically.
- For the AI chat feature, use a cheaper model (claude-haiku) for conversational turns and reserve sonnet/opus for content generation.
- Log token usage per session so costs are visible during development.

**Phase:** Address in Phase 1 (architecture decisions) and Phase 2 (caching implementation).

---

### Pitfall 8: Progress State Lost on Server Restart

**What goes wrong:** SRS card state (ease factor, interval, next review date), quiz scores, and completed section tracking are stored in memory or in a file that gets overwritten on server restart. The user returns the next day to find all progress gone. With a 3-week deadline, losing a week of SRS progress is devastating.

**Prevention:**
- Use SQLite as the persistence layer, not in-memory storage or JSON files that could be overwritten.
- Commit database writes synchronously for SRS state updates — do not batch or defer.
- Test data persistence on day 1: restart the server and verify all state survives.
- Keep the database file in a predictable location with a clear backup strategy — even a daily `cp` to another directory.
- For SRS specifically: every card review must write to disk before the UI advances to the next card.

**Phase:** Address in Phase 1 (persistence architecture).

---

### Pitfall 9: Past Exam Questions With Wrong Answers as Ground Truth

**What goes wrong:** Past exam questions are sourced from PDFs, websites, or unofficial repositories. These sources sometimes contain the wrong answer marked as correct, have outdated information, or contain OCR errors. The user studies from incorrect "official" questions and learns wrong answers with high confidence because they believe the source is authoritative.

**Prevention:**
- When adding past exam questions, use Claude to verify the answer and generate an explanation. If Claude's explanation contradicts the stated answer, flag the question for manual review.
- Prefer official MUR (Ministero dell'Università e della Ricerca) sources or well-established prep publishers (Alpha Test, Hoepli) over random web sources.
- Build a "flagged for review" state into the question model so unreliable questions can be excluded from study sessions.
- Do not trust unofficial question databases without cross-referencing at least 2 sources.

**Phase:** Address in Phase 2 (content sourcing and integration).

---

### Pitfall 10: Mobile UX That Requires Precise Tapping

**What goes wrong:** The app is developed on a desktop browser and works fine there. On iPhone, buttons are too small (below 44pt touch targets), flashcard flip actions are fiddly, the quiz interface requires precise taps that are hard on a phone screen, and text is too small to read without zooming. The user finds the app frustrating to use on mobile and abandons it.

**Why it matters:** This app will be used primarily on iPhone. If mobile UX is broken, the app is functionally broken.

**Prevention:**
- Use minimum 44px touch targets for all interactive elements (Apple's Human Interface Guidelines).
- Design for 375px viewport width (iPhone SE) as the minimum case.
- Make flashcard flip a full-card tap — the entire card surface should be the tap target, not a small button.
- Use large, readable font sizes (minimum 16px for body text, 18px for exam content).
- Test on an actual iPhone (or Safari mobile emulation) at the end of every development session, not just on desktop.
- Prefer CSS Flexbox column layouts over grid layouts for mobile — simpler and more reliable across iPhone viewports.

**Phase:** Address in Phase 1 (responsive design baseline) and validate after every phase.

---

## Minor Pitfalls

Low-severity issues that cause annoyance or minor inefficiency.

---

### Pitfall 11: Topic Coverage Gaps Discovered Late

**What goes wrong:** The developer generates content for topics they know well (e.g., cell biology) and skips or defers topics that seem less central (e.g., specific genetics problems, stoichiometry). On the exam, a disproportionate number of questions come from the skipped topics.

**Prevention:**
- Source the official Ministry curriculum list for "Professioni Sanitarie" (publicly available from MUR) and use it as a checklist.
- Generate at minimum one stub explainer for every topic on the curriculum list in week 1 — even a 3-sentence summary is better than nothing.
- Track topic coverage explicitly in the app (or a simple text file) rather than assuming "I've covered most things."

**Phase:** Address in Phase 1 (content planning) and Phase 2 (content generation).

---

### Pitfall 12: Flashcard Front-Back Confusion for Bidirectional Topics

**What goes wrong:** Flashcard fronts are always "Italian term → English translation" or "Definition → Term." For anatomy and cell biology, bidirectional recall is needed — both "what is the mitochondria?" and "what organelle produces ATP?" should be testable. An app that only tests in one direction creates an illusion of mastery.

**Prevention:**
- For nomenclature cards (cell organelles, anatomical structures, chemical compounds), generate both directions as separate cards: `[term → function]` and `[function → term]`.
- Label cards by direction type so the user can filter if needed.
- Keep it simple — do not try to build automatic bidirectional card generation as a complex feature. Just generate two cards manually for high-priority terms.

**Phase:** Address in Phase 2 (flashcard content generation).

---

### Pitfall 13: Regenerating Content Changes Answers Mid-Study

**What goes wrong:** The user has studied an explanation and taken a quiz. Later, they or the developer triggers content regeneration (e.g., to "improve" the explanation). The regenerated content has subtly different answers or frames concepts differently. The user is now confused about which version is correct.

**Prevention:**
- Treat generated content as immutable once studied. Add an explicit "regenerate" button that warns "this will replace the current content."
- Optionally: keep a version history of regenerated content (simple timestamp + content in a separate table) so rollback is possible.
- Never regenerate content automatically in the background.

**Phase:** Address in Phase 2 (content management).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 1: Data schema | Forgetting language fields | Design `content_it`/`content_en` from day 1 |
| Phase 1: SRS algorithm choice | Implementing full SM-2 for a 3-week app | Use simplified Leitner or capped-interval SM-2 |
| Phase 1: Persistence | SQLite write-ahead or in-memory | Test server restart persistence on day 1 |
| Phase 2: Content generation | Claude hallucinating biology/chemistry facts | System prompt with uncertainty permission + chain-of-thought |
| Phase 2: Quiz distractor quality | AI generating obviously wrong distractors | Explicit prompting for plausible-but-wrong answers + required explanations |
| Phase 2: Card creation | Generating 200+ cards before review system tested | Cap at 20 cards per topic, test review cycle first |
| Phase 2: Past exam questions | Wrong answers in sourced question banks | Claude-verified explanations for all questions + source quality gate |
| Phase 3: Mobile UX | Desktop-only testing | iPhone test after every feature |
| Every phase | Feature creep | Only build if it enables more topic coverage or better retention |
| Every phase | API costs from re-generation | Cache all AI content; regenerate only on explicit user request |

---

## AI Content-Specific Risk Matrix

| Content Type | Hallucination Risk | Reason | Mitigation |
|---|---|---|---|
| Cell biology explainers | Medium | Well-represented in training data | Chain-of-thought prompting |
| Chemistry reactions/stoichiometry | High | Specific values often wrong | Flag numerical claims for verification |
| Anatomy terms/structures | Medium-High | Niche Italian curriculum specifics | Cross-reference official sources |
| Osteopathy-specific content | High | Underrepresented in training data | Heavy uncertainty-permission prompting |
| Past exam question explanations | Medium | Constrained to provided question | Explicitly restrict to question context |
| AI chat responses | Medium | User-guided, bounded scope | Allow "I don't know" in system prompt |
| Flashcard content | Low-Medium | Short factual claims, easier to verify | User flags incorrect cards |

---

## Sources

- [Medical Hallucination in Foundation Models and Their Impact on Healthcare — medRxiv (2025)](https://www.medrxiv.org/content/10.1101/2025.02.28.25323115v1.full)
- [Reduce Hallucinations — Claude API Official Docs](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)
- [Quality Assurance and Validity of AI-Generated Single Best Answer Questions — BMC Medical Education (2025)](https://bmcmededuc.biomedcentral.com/articles/10.1186/s12909-025-06881-w)
- [AI versus Human-Generated MCQs for Medical Education — BMC Medical Education (2025)](https://bmcmededuc.biomedcentral.com/articles/10.1186/s12909-025-06796-6)
- [The SM-2 Algorithm Is Too Aggressive on Overdue Cards — Control-Alt-Backspace](https://controlaltbackspace.org/overdue-handling/)
- [FSRS vs SM-2: The Complete Guide — MemoForge Blog (2025)](https://memoforge.app/blog/fsrs-vs-sm2-anki-algorithm-guide-2025/)
- [A Better Spaced Repetition Algorithm: SM2+](https://www.blueraja.com/blog/477/a-better-spaced-repetition-learning-algorithm-sm2)
- [Why Most Spaced Repetition Apps Don't Work](https://universeofmemory.com/spaced-repetition-apps-dont-work/)
- [Spaced Repetition Algorithm: A Three-Day Journey from Novice to Expert — open-spaced-repetition](https://github.com/open-spaced-repetition/fsrs4anki/wiki/spaced-repetition-algorithm:-a-three%E2%80%90day-journey-from-novice-to-expert)
- [Integrating AI into Clinical Education: Evaluating Trainees' Proficiency in Distinguishing AI Hallucinations — PMC (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11924592/)
- [Feature Creep Is Killing Your Software: Here's How to Stop It — DesignRush](https://www.designrush.com/agency/software-development/trends/feature-creep)
- [Programma di studio per Ammissione Professioni Sanitarie](https://www.compitoinclasse.org/ammissione-universita-numero-chiuso/programma-materie-studio.php)
