import os
import re
import logging
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

# XML delimiters are robust with embedded markdown — no JSON escaping issues
EXPLAINER_SYSTEM_PROMPT = """You are a study assistant for Italian professional health qualification (professioni sanitarie) and osteopathy entry exams.

Generate detailed, schematic study notes. Dense with information. No filler.

UNCERTAINTY RULES:
- Wrap uncertain numerical values in [UNCERTAIN: ...] (e.g. [UNCERTAIN: ~180 g/mol])
- Use for contested data or Italian curriculum-specific details
- Do NOT mark well-established facts

OUTPUT STRUCTURE — each language must follow this markdown structure:

## Definizione
One precise sentence: what it is, where it exists, what its core purpose is.

## Struttura / Composizione
Bullet list. Each bullet = one component/layer/part with:
- Name + what it is made of or arranged as + its specific role
- Example: "- Membrana plasmatica: doppio strato fosfolipidico (~7 nm), delimita la cellula, permeabilità selettiva — i lipidi passano liberamente, gli ioni richiedono canali proteici"

## Meccanismo / Funzione
How it works. Numbered list if sequential, bullets if parallel.
Each point: what happens + why it matters. Name specific molecules, directions, results.

## Dati chiave
Testable numbers, sizes, counts, pH, temperatures — one datum per bullet.
Use [UNCERTAIN: ...] where not 100% certain.

## Perché è importante
2-3 sentences: why this matters in the bigger picture, what would break without it, how it connects to physiology or disease.

## Connessioni agli altri argomenti
3-4 bullets linking to other exam topics:
- "→ [Topic]: [one specific sentence on how they connect]"

## Focus esame
5-6 bullets of likely exam questions and key memorization points:
- "❓ [Question or fact to memorize]"

RULES:
- Every bullet must have at least one specific, verifiable detail — no vague statements
- Adapt section titles if needed (e.g. "Reazione" not "Meccanismo" for chemistry topics)
- English version uses English titles: Definition / Structure / Mechanism / Key Data / Why It Matters / Connections / Exam Focus

OUTPUT FORMAT — use these exact XML tags, nothing else before or after:
<IT>
[Italian markdown here]
</IT>
<EN>
[English markdown here]
</EN>"""


async def generate_explainer(title_it: str, title_en: str) -> tuple[str, str]:
    """
    Generate Italian and English explainers in a single Claude API call.
    Returns (content_it, content_en).
    Never call this when content already exists in DB.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")

    client = AsyncAnthropic(api_key=api_key)
    logger.info(f"Generating explainer for: {title_it}")

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=EXPLAINER_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Write study notes for: '{title_it}' (English: '{title_en}')."
        }]
    )

    raw = response.content[0].text

    # Strip markdown code fences if Claude wrapped the output (e.g. ```xml ... ```)
    raw = re.sub(r'^```[a-z]*\n?', '', raw.strip(), flags=re.IGNORECASE)
    raw = re.sub(r'\n?```$', '', raw.strip())

    # Extract IT block: from <IT> to </IT> or <EN> (Claude sometimes omits closing tags)
    it_match = re.search(r'<IT>\s*(.*?)\s*(?:</IT>|<EN>)', raw, re.DOTALL | re.IGNORECASE)
    # Extract EN block: from <EN> to </EN> or end of string
    en_match = re.search(r'<EN>\s*(.*?)\s*(?:</EN>|$)', raw, re.DOTALL | re.IGNORECASE)

    if it_match and en_match:
        content_it = it_match.group(1).strip()
        content_en = en_match.group(1).strip()
        if content_it and content_en:
            return content_it, content_en

    logger.error(f"Failed to parse response for '{title_it}'. Raw[:300]: {raw[:300]}")
    raise ValueError(f"Unexpected response format for '{title_it}'")


QUIZ_EXPLANATION_SYSTEM_PROMPT = """Sei un assistente per esami di ingresso italiani (professioni sanitarie, osteopatia).

Per una domanda a risposta multipla fornisci spiegazioni brevi e chiare IN ITALIANO.

REGOLE:
- Tutte le spiegazioni DEVONO essere in italiano
- Sii conciso: 2-3 frasi per la risposta corretta, 1-2 frasi per ogni risposta sbagliata
- Spiega il perché scientifico, non solo "è sbagliata perché..."
- Non usare "Risposta corretta:" o "Risposta sbagliata:" come intestazioni

OUTPUT FORMAT — usa questi tag XML esatti, nient'altro:
<CORRECT>
[Perché questa risposta è corretta — 2-3 frasi in italiano]
</CORRECT>
<WRONG_0>
[Perché la prima risposta sbagliata è errata — 1-2 frasi in italiano]
</WRONG_0>
<WRONG_1>
[Perché la seconda risposta sbagliata è errata — 1-2 frasi in italiano]
</WRONG_1>
<WRONG_2>
[Perché la terza risposta sbagliata è errata — 1-2 frasi in italiano]
</WRONG_2>"""


async def generate_quiz_explanation(
    question_it: str,
    choices: list[str],
    correct_index: int,
) -> dict[str, str]:
    """
    Generate per-choice explanation for a quiz question.
    Returns {"correct": "...", "wrong_0": "...", "wrong_1": "...", "wrong_2": "..."}
    where wrong_N corresponds to the Nth incorrect choice (in original order, skipping correct).

    IMPORTANT: Check explanation_json IS NULL in the DB before calling this.
    Generate-once-cache pattern — never regenerate if explanation already exists.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")

    client = AsyncAnthropic(api_key=api_key)

    # Build user message listing all choices with labels
    choice_labels = ["A", "B", "C", "D"]
    choices_formatted = "\n".join(
        f"  {choice_labels[i]}. {choice}" for i, choice in enumerate(choices)
    )
    correct_label = choice_labels[correct_index]
    user_msg = (
        f"Domanda: {question_it}\n\n"
        f"Opzioni:\n{choices_formatted}\n\n"
        f"Risposta corretta: {correct_label}. {choices[correct_index]}\n\n"
        "Fornisci le spiegazioni per tutte le opzioni."
    )

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=QUIZ_EXPLANATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text

    correct_match = re.search(r"<CORRECT>\s*(.*?)\s*</CORRECT>", raw, re.DOTALL | re.IGNORECASE)
    w0_match = re.search(r"<WRONG_0>\s*(.*?)\s*</WRONG_0>", raw, re.DOTALL | re.IGNORECASE)
    w1_match = re.search(r"<WRONG_1>\s*(.*?)\s*</WRONG_1>", raw, re.DOTALL | re.IGNORECASE)
    w2_match = re.search(r"<WRONG_2>\s*(.*?)\s*</WRONG_2>", raw, re.DOTALL | re.IGNORECASE)

    if not all([correct_match, w0_match, w1_match, w2_match]):
        logger.error(f"Quiz explanation parse failed. Raw[:300]: {raw[:300]}")
        raise ValueError("Unexpected response format for quiz explanation")

    return {
        "correct": correct_match.group(1).strip(),
        "wrong_0": w0_match.group(1).strip(),
        "wrong_1": w1_match.group(1).strip(),
        "wrong_2": w2_match.group(1).strip(),
    }


EXAM_EXPLANATION_SYSTEM_PROMPT = """Sei un assistente per esami di ingresso italiani (professioni sanitarie, TOLC-B/TOLC-F).

Per una domanda d'esame a risposta multipla fornisci spiegazioni chiare e didattiche IN ITALIANO.

REGOLE:
- Tutte le spiegazioni DEVONO essere in italiano
- La risposta corretta: 2-3 frasi che spiegano il concetto scientifico sottostante
- Le risposte sbagliate: 1-2 frasi che spiegano l'errore concettuale specifico
- Usa terminologia tecnica corretta, come atteso in un esame universitario

OUTPUT FORMAT — usa questi tag XML esatti, nient'altro:
<CORRECT>
[Perché questa è la risposta corretta — 2-3 frasi in italiano]
</CORRECT>
<WRONG_0>
[Errore specifico della prima opzione sbagliata — 1-2 frasi in italiano]
</WRONG_0>
<WRONG_1>
[Errore specifico della seconda opzione sbagliata — 1-2 frasi in italiano]
</WRONG_1>
<WRONG_2>
[Errore specifico della terza opzione sbagliata — 1-2 frasi in italiano]
</WRONG_2>"""


async def generate_exam_explanation(
    question_it: str,
    choices: list[str],
    correct_index: int,
) -> dict[str, str]:
    """
    Generate per-choice explanation for an exam question.
    Returns {"correct": "...", "wrong_0": "...", "wrong_1": "...", "wrong_2": "..."}

    IMPORTANT: Check explanation_json IS NULL before calling this.
    Generate-once-cache — never regenerate if explanation already exists.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")

    client = AsyncAnthropic(api_key=api_key)

    choice_labels = ["A", "B", "C", "D"]
    choices_formatted = "\n".join(
        f"  {choice_labels[i]}. {choice}" for i, choice in enumerate(choices)
    )
    correct_label = choice_labels[correct_index]
    user_msg = (
        f"Domanda d'esame: {question_it}\n\n"
        f"Opzioni:\n{choices_formatted}\n\n"
        f"Risposta corretta: {correct_label}. {choices[correct_index]}\n\n"
        "Fornisci le spiegazioni per tutte le opzioni."
    )

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=EXAM_EXPLANATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text

    correct_match = re.search(r"<CORRECT>\s*(.*?)\s*</CORRECT>", raw, re.DOTALL | re.IGNORECASE)
    w0_match = re.search(r"<WRONG_0>\s*(.*?)\s*</WRONG_0>", raw, re.DOTALL | re.IGNORECASE)
    w1_match = re.search(r"<WRONG_1>\s*(.*?)\s*</WRONG_1>", raw, re.DOTALL | re.IGNORECASE)
    w2_match = re.search(r"<WRONG_2>\s*(.*?)\s*</WRONG_2>", raw, re.DOTALL | re.IGNORECASE)

    if not all([correct_match, w0_match, w1_match, w2_match]):
        logger.error(f"Exam explanation parse failed. Raw[:300]: {raw[:300]}")
        raise ValueError("Unexpected response format for exam explanation")

    return {
        "correct": correct_match.group(1).strip(),
        "wrong_0": w0_match.group(1).strip(),
        "wrong_1": w1_match.group(1).strip(),
        "wrong_2": w2_match.group(1).strip(),
    }


async def build_chat_system_prompt(topic_slug: str, db) -> str:
    """Build context-aware system prompt for chat (CHAT-03 + CHAT-04)."""
    from sqlalchemy import select
    from app.models import Topic
    from app.services.progress_service import get_progress_summary

    parts = [
        "Sei un assistente per la preparazione all'esame di professioni sanitarie e osteopatia.",
        "Rispondi in italiano. Sii conciso e focalizzato sull'esame.",
    ]

    # CHAT-03: topic context
    if topic_slug:
        topic = await db.scalar(select(Topic).where(Topic.slug == topic_slug))
        if topic:
            parts.append(
                f"\nL'utente sta studiando: '{topic.title_it}' ({topic.title_en})."
                " Rispondi nel contesto di questo argomento."
            )

    # CHAT-04: progress context (compact — weak subjects + SRS state)
    try:
        summary = await get_progress_summary(db)
        weak = [
            s for s, q in summary["quiz_by_subject"].items()
            if q.avg_accuracy is not None and q.avg_accuracy < 0.5
        ]
        if weak:
            subject_names = {"biology": "Biologia", "chemistry": "Chimica",
                             "physics": "Fisica/Matematica", "logic": "Logica"}
            weak_it = [subject_names.get(s, s) for s in weak]
            parts.append(f"\nArgomenti deboli dell'utente (quiz < 50%): {', '.join(weak_it)}.")
        srs = summary["srs"]
        parts.append(
            f"\nStato ripasso: {srs['due']} carte in scadenza oggi, "
            f"{srs['learned']} apprese, {srs['new']} nuove."
        )
    except Exception:
        pass  # Progress context is best-effort — never break chat for a DB error

    return "\n".join(parts)


async def stream_chat_generator(question: str, system_prompt: str):
    """
    Async generator yielding SSE-formatted text chunks from Claude streaming.
    Yields: "data: <escaped_chunk>\\n\\n" for each text token
    Yields: "data: [DONE]\\n\\n" on completion
    Handles GeneratorExit (client disconnect) cleanly.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        yield "data: [ERROR: ANTHROPIC_API_KEY not set]\n\n"
        return

    client = AsyncAnthropic(api_key=api_key)
    try:
        async with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": question}],
        ) as stream:
            async for text in stream.text_stream:
                # Escape newlines — SSE uses \n\n as message delimiter
                safe = text.replace("\n", "\\n")
                yield f"data: {safe}\n\n"
    except GeneratorExit:
        pass  # Client disconnected — clean exit, context manager closes stream
    finally:
        yield "data: [DONE]\n\n"
