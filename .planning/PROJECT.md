# OsteoPrep

## What This Is

A web-based study app for preparing for the Italian osteopathy entry exam (and related medicine/professioni sanitarie tests). It runs on a private server and is accessible via iPhone browser. It generates AI-powered study content on demand — explainers, quizzes, flashcards, and past exam questions — covering the biology, chemistry, and anatomy topics tested in Italian health profession entry exams.

## Core Value

Cover the key exam topics effectively in 3 weeks through AI-generated explanations, spaced repetition flashcards, and practice with real past exam question formats.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Study content: AI-generated explainers on biology, chemistry, and anatomy topics covered in Italian osteopathy/medicine entry exams
- [ ] Section quizzes: Multiple choice questions after each topic section to test understanding
- [ ] Flashcard system with spaced repetition (SRS) for nomenclature — cell parts, chemical compounds, anatomical terms
- [ ] Past exam questions: Questions drawn from online sources (Italian medicine and professioni sanitarie entry tests), with explanations for wrong answers
- [ ] AI chat: Ask Claude questions about study material or progress
- [ ] Bilingual content: Italian and English, switchable
- [ ] Progress tracking: Save quiz scores, SRS card state, and completed sections across sessions
- [ ] Mobile-friendly: Usable on iPhone via browser

### Out of Scope

- User accounts / login — single-user app, no auth needed
- Native iOS app — web app in browser is sufficient
- Video content — text-based explanations only for speed
- Offline mode — requires internet connection to server

## Context

- Exam date: ~3 weeks away — speed and coverage are the priority
- Server: Hetzner Ubuntu server (IP 91.98.143.115), accessible via Tailscale or direct browser
- AI: Claude API (Anthropic) with dedicated API key for this project
- Content sources: AI-generated on demand + past papers found online (Italian osteopathy, medicine, professioni sanitarie entry tests)
- Single user — no multi-tenancy needed

## Constraints

- **Timeline**: 3 weeks to exam — v1 must cover all main topic areas and be usable immediately
- **Stack**: Must be accessible via iPhone browser without any app install
- **AI**: Claude API for content generation and chat
- **Hosting**: Self-hosted on the existing Hetzner server, different port from existing services (Open WebUI on 3000)
- **Data**: Progress and SRS state must persist between sessions (server-side storage)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Web app (not native iOS) | No app store submission, instantly accessible on iPhone | — Pending |
| Claude API for content | Best quality explanations, already have API key | — Pending |
| Spaced repetition for flashcards | Most effective method for memorizing nomenclature | — Pending |
| Single-user, no auth | Just one person using it — simplifies everything | — Pending |

---
*Last updated: 2026-02-28 after initialization*
