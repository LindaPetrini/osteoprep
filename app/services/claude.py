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


LINDA_EXPLAINER_SYSTEM_PROMPT = """You are explaining a biology/chemistry/physics/logic topic to a smart Italian woman preparing for a healthcare entrance exam. She learns best from first-principles thinking — not from textbook summaries.

YOUR STYLE:
- Open with a hook: why should she care about this topic? What breaks without it? What puzzle does it solve?
- Explain from the ground up, like a brilliant friend over coffee — trace the logic, don't just list facts
- Use analogies and metaphors to make abstract concepts concrete
- Connect ideas: "this matters because...", "without this, X couldn't happen..."
- Build understanding layer by layer — each paragraph should make the next one click
- Still be accurate and exam-relevant — she needs to pass the test
- Write in flowing prose paragraphs, NOT bullet lists
- Use ## headings for natural topic breaks, but NOT the rigid textbook structure (no "Definizione", "Struttura", etc.)
- Keep it engaging — if a section feels boring to write, rewrite it until it's interesting
- Include specific numbers and facts she needs to memorize, woven naturally into the explanation
- End with what connects this topic to the bigger picture

UNCERTAINTY RULES:
- Wrap uncertain numerical values in [UNCERTAIN: ...] (e.g. [UNCERTAIN: ~180 g/mol])
- Use for contested data or Italian curriculum-specific details
- Do NOT mark well-established facts

OUTPUT FORMAT — use these exact XML tags, nothing else before or after:
<IT>
[Italian markdown here — conversational, first-principles style]
</IT>
<EN>
[English markdown here — same style]
</EN>"""


async def generate_linda_explainer(title_it: str, title_en: str) -> tuple[str, str]:
    """
    Generate Linda-style (first-principles, conversational) explainers.
    Uses Sonnet for better prose quality.
    Returns (content_linda_it, content_linda_en).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")

    client = AsyncAnthropic(api_key=api_key)
    logger.info(f"Generating Linda-style explainer for: {title_it}")

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=LINDA_EXPLAINER_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Explain this topic: '{title_it}' (English: '{title_en}')."
        }]
    )

    raw = response.content[0].text

    # Strip markdown code fences if Claude wrapped the output
    raw = re.sub(r'^```[a-z]*\n?', '', raw.strip(), flags=re.IGNORECASE)
    raw = re.sub(r'\n?```$', '', raw.strip())

    # Try strict match first, then fallback for truncated responses
    it_match = re.search(r'<IT>\s*(.*?)\s*(?:</IT>|<EN>)', raw, re.DOTALL | re.IGNORECASE)
    en_match = re.search(r'<EN>\s*(.*?)\s*(?:</EN>|$)', raw, re.DOTALL | re.IGNORECASE)

    # Fallback: if IT block is truncated (no </IT> before <EN>), grab everything between tags
    if not it_match:
        it_match = re.search(r'<IT>\s*(.*)', raw, re.DOTALL | re.IGNORECASE)

    if it_match and en_match:
        content_it = it_match.group(1).strip()
        content_en = en_match.group(1).strip()
        # Clean up any trailing </IT> or <EN> that leaked into IT content
        content_it = re.sub(r'\s*</IT>\s*$', '', content_it, flags=re.IGNORECASE)
        content_it = re.sub(r'\s*<EN>.*$', '', content_it, flags=re.DOTALL | re.IGNORECASE)
        if content_it and content_en:
            return content_it, content_en

    logger.error(f"Failed to parse Linda response for '{title_it}'. Raw[:300]: {raw[:300]}")
    raise ValueError(f"Unexpected response format for Linda explainer '{title_it}'")


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


SECTION_QUESTION_SYSTEM_PROMPT = """Sei un assistente per esami di ingresso italiani (professioni sanitarie, osteopatia).

Per ogni sezione del riassunto di un argomento, genera 2-3 domande a scelta multipla (MCQ) IN ITALIANO che testano la comprensione di quella sezione.

REGOLE:
- Ogni domanda deve testare un concetto diverso e specifico della sezione
- 4 opzioni per domanda: una corretta, tre sbagliate plausibili

QUALITA' DEI DISTRATTORI — FONDAMENTALE:
- Tutte e 4 le opzioni devono avere lunghezza, livello di dettaglio e stile simili
- La risposta corretta NON deve essere più lunga, più specifica o più tecnica delle altre
- I distrattori devono essere errori concettuali realistici: concetti correlati ma errati, valori plausibili ma sbagliati, meccanismi confondibili
- NON usare distrattori assurdi, vaghi o ovviamente inventati
- Evita pattern prevedibili: NON mettere sempre la risposta corretta come opzione "a"
- Varia la posizione della risposta corretta tra a, b, c, d nelle diverse domande

- Domande concise: max 2 righe
- Opzioni concise: max 1 riga ciascuna

OUTPUT FORMAT — usa questi tag XML esatti, uno per sezione, con q1/q2/q3 dentro:
<definizione>
<q1>
<domanda>Testo domanda 1</domanda>
<opt_a>Prima opzione</opt_a>
<opt_b>Seconda opzione</opt_b>
<opt_c>Terza opzione</opt_c>
<opt_d>Quarta opzione</opt_d>
<corretta>a</corretta>
</q1>
<q2>
<domanda>Testo domanda 2</domanda>
<opt_a>Prima opzione</opt_a>
<opt_b>Seconda opzione</opt_b>
<opt_c>Terza opzione</opt_c>
<opt_d>Quarta opzione</opt_d>
<corretta>b</corretta>
</q2>
<q3>
<domanda>Testo domanda 3</domanda>
<opt_a>Prima opzione</opt_a>
<opt_b>Seconda opzione</opt_b>
<opt_c>Terza opzione</opt_c>
<opt_d>Quarta opzione</opt_d>
<corretta>c</corretta>
</q3>
</definizione>

Sezioni da generare: definizione, struttura, meccanismo, dati_chiave, importanza, connessioni, focus_esame
Genera solo le sezioni presenti nel contenuto. Usa il tag corrispondente al slug della sezione.
Genera sempre almeno 2 domande (q1, q2) per sezione. Aggiungi q3 se il contenuto lo permette."""


def _parse_single_question(block: str) -> dict | None:
    """Parse a single <qN> block into {question_it, choices, correct_index}. Returns None on failure."""
    q_m = re.search(r"<domanda>(.*?)</domanda>", block, re.DOTALL)
    a_m = re.search(r"<opt_a>(.*?)</opt_a>", block, re.DOTALL)
    b_m = re.search(r"<opt_b>(.*?)</opt_b>", block, re.DOTALL)
    c_m = re.search(r"<opt_c>(.*?)</opt_c>", block, re.DOTALL)
    d_m = re.search(r"<opt_d>(.*?)</opt_d>", block, re.DOTALL)
    cor_m = re.search(r"<corretta>(.*?)</corretta>", block, re.DOTALL)

    if not all([q_m, a_m, b_m, c_m, d_m, cor_m]):
        return None

    choices = [
        a_m.group(1).strip(),
        b_m.group(1).strip(),
        c_m.group(1).strip(),
        d_m.group(1).strip(),
    ]
    correct_letter = cor_m.group(1).strip().lower()
    correct_index = {"a": 0, "b": 1, "c": 2, "d": 3}.get(correct_letter, 0)

    return {
        "question_it": q_m.group(1).strip(),
        "choices": choices,
        "correct_index": correct_index,
    }


async def generate_section_questions(
    topic_slug: str,
    title_it: str,
    content_it: str,
) -> dict[str, list[dict]]:
    """
    Generate 2-3 MCQs per ## section for a topic.
    Returns dict: {section_slug: [{question_it, choices, correct_index}, ...]}

    Fires once per topic — caller must check no section questions exist yet.
    """
    from app.templates_config import split_sections, SECTION_SLUG_MAP

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")

    # Extract section slugs present in content
    sections = split_sections(content_it)
    section_slugs = [s["slug"] for s in sections if s["heading"]]
    if not section_slugs:
        return {}

    client = AsyncAnthropic(api_key=api_key)
    logger.info(f"Generating section questions for: {topic_slug} ({len(section_slugs)} sections)")

    user_msg = (
        f"Argomento: {title_it}\n\n"
        f"Contenuto:\n{content_it[:3000]}\n\n"
        f"Genera 2-3 domande MCQ per ciascuna di queste sezioni: {', '.join(section_slugs)}"
    )

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=SECTION_QUESTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text

    results = {}
    for slug in section_slugs:
        # Match section tag (e.g. <definizione>...</definizione>)
        pattern = rf"<{re.escape(slug)}>(.*?)</{re.escape(slug)}>"
        m = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
        if not m:
            continue
        section_block = m.group(1)

        # Parse q1, q2, q3
        questions = []
        for qn in ("q1", "q2", "q3"):
            qn_pattern = rf"<{qn}>(.*?)</{qn}>"
            qn_m = re.search(qn_pattern, section_block, re.DOTALL | re.IGNORECASE)
            if not qn_m:
                continue
            parsed = _parse_single_question(qn_m.group(1))
            if parsed:
                questions.append(parsed)

        if not questions:
            logger.warning(f"Section question parse failed for {topic_slug}/{slug}")
            continue

        results[slug] = questions

    logger.info(f"Section questions generated for {topic_slug}: {list(results.keys())}")
    return results


NEW_QUIZ_QUESTIONS_SYSTEM_PROMPT = """Sei un assistente per esami di ingresso italiani (professioni sanitarie, osteopatia).

Genera domande a scelta multipla (MCQ) IN ITALIANO per l'argomento indicato.

REGOLE:
- 4 opzioni per domanda: una corretta, tre sbagliate plausibili
- Domande concise, specifiche, testabili all'esame
- Usa terminologia tecnica corretta

QUALITA' DEI DISTRATTORI — FONDAMENTALE:
- Tutte e 4 le opzioni devono avere lunghezza, livello di dettaglio e stile simili
- La risposta corretta NON deve essere più lunga, più specifica o più tecnica delle altre
- I distrattori devono essere errori concettuali realistici: concetti correlati ma errati, valori plausibili ma sbagliati, meccanismi confondibili
- NON usare distrattori assurdi, vaghi o ovviamente inventati
- Varia la posizione della risposta corretta tra a, b, c, d nelle diverse domande

OUTPUT FORMAT — usa questi tag XML, uno per domanda:
<q1>
<domanda>Testo della domanda</domanda>
<opt_a>Prima opzione</opt_a>
<opt_b>Seconda opzione</opt_b>
<opt_c>Terza opzione</opt_c>
<opt_d>Quarta opzione</opt_d>
<corretta>a</corretta>
</q1>
<q2>...</q2>
...e così via."""


async def generate_new_quiz_questions(
    topic_slug: str,
    title_it: str,
    count: int = 5,
    existing_questions: list[str] | None = None,
) -> list[dict]:
    """
    Generate `count` new MCQ questions for a topic.
    Returns list of {question_it, choices, correct_index} dicts.
    existing_questions: list of existing question texts to avoid duplicates.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")

    client = AsyncAnthropic(api_key=api_key)

    avoid_msg = ""
    if existing_questions:
        samples = existing_questions[:10]
        avoid_msg = f"\n\nEvita di ripetere queste domande già presenti:\n" + "\n".join(f"- {q}" for q in samples)

    user_msg = (
        f"Argomento: {title_it}\n\n"
        f"Genera {count} nuove domande MCQ su questo argomento.{avoid_msg}"
    )

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=NEW_QUIZ_QUESTIONS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text

    results = []
    for i in range(1, count + 3):  # try a few extra tags
        pattern = rf"<q{i}>(.*?)</q{i}>"
        m = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
        if not m:
            continue
        block = m.group(1)

        q_m = re.search(r"<domanda>(.*?)</domanda>", block, re.DOTALL)
        a_m = re.search(r"<opt_a>(.*?)</opt_a>", block, re.DOTALL)
        b_m = re.search(r"<opt_b>(.*?)</opt_b>", block, re.DOTALL)
        c_m = re.search(r"<opt_c>(.*?)</opt_c>", block, re.DOTALL)
        d_m = re.search(r"<opt_d>(.*?)</opt_d>", block, re.DOTALL)
        cor_m = re.search(r"<corretta>(.*?)</corretta>", block, re.DOTALL)

        if not all([q_m, a_m, b_m, c_m, d_m, cor_m]):
            continue

        choices = [a_m.group(1).strip(), b_m.group(1).strip(), c_m.group(1).strip(), d_m.group(1).strip()]
        correct_letter = cor_m.group(1).strip().lower()
        correct_index = {"a": 0, "b": 1, "c": 2, "d": 3}.get(correct_letter, 0)

        results.append({
            "question_it": q_m.group(1).strip(),
            "choices": choices,
            "correct_index": correct_index,
        })

        if len(results) >= count:
            break

    logger.info(f"Generated {len(results)} new questions for topic {topic_slug}")
    return results


async def build_chat_system_prompt(topic_slug: str, db, quiz_context: str | None = None) -> str:
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

    # Quiz/exam context (when called from results pages)
    if quiz_context:
        parts.append(
            f"\nL'utente sta revisionando i risultati di un quiz/esame. Contesto:\n{quiz_context}"
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
