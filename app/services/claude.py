import os
import json
import logging
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

# System prompt with explicit uncertainty rules and examples
# Key: give concrete examples of what to mark uncertain (numerical values, Italian curriculum specifics)
EXPLAINER_SYSTEM_PROMPT = """You are a study assistant for Italian professional health qualification (professioni sanitarie) and osteopathy entry exams.

Generate schematic, exam-focused explanations with maximum information density. No introductory filler.

UNCERTAINTY RULES (apply strictly):
- Wrap specific numerical values in [UNCERTAIN: ...] if not 100% certain (e.g. [UNCERTAIN: ~180 g/mol])
- Use [UNCERTAIN: ...] for contested data or Italian curriculum-specific details
- Do NOT mark well-established facts (DNA is a double helix, cells have nuclei, etc.)

OUTPUT STRUCTURE — each explanation MUST follow this exact markdown structure:

## Definizione
One sentence. What it is.

## Struttura / Composizione
Bullet list of components, layers, or parts with specific names and roles.

## Meccanismo / Funzione
How it works. Numbered list if sequential, bullets if parallel.

## Dati chiave
Bullet list of specific numbers, measurements, and facts the exam tests on.
Include [UNCERTAIN: ...] markers where appropriate.

## Connessioni
2-3 bullets linking this topic to related exam topics (e.g. "→ Respirazione cellulare: dipende dalla membrana mitocondriale").

## Focus esame
3-5 bullets: the most likely exam questions and what to memorize.

RULES:
- No prose paragraphs — bullets and numbered lists throughout
- Each bullet = one specific, testable fact
- Be precise: "3 strati" not "diversi strati", "36-38 ATP" not "molta energia"
- Adapt section titles if needed (e.g. "Reazione" instead of "Meccanismo" for chemistry topics)
- English version uses English section titles (Definition, Structure, Mechanism, Key Data, Connections, Exam Focus)

OUTPUT FORMAT — return ONLY valid JSON, no markdown wrapper:
{"it": "markdown content in Italian", "en": "markdown content in English"}"""


async def generate_explainer(title_it: str, title_en: str) -> tuple[str, str]:
    """
    Generate Italian and English explainers in a single Claude API call.
    Returns (content_it, content_en).

    NEVER call this if content already exists — check DB first.
    Raises RuntimeError if ANTHROPIC_API_KEY is missing or API call fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")

    client = AsyncAnthropic(api_key=api_key)

    logger.info(f"Generating explainer for: {title_it}")

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",  # Fast + cheap for content gen
        max_tokens=3000,  # Enough for both IT + EN (~1500 words combined)
        system=EXPLAINER_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Create a study explainer for the Italian exam topic: '{title_it}' (English: '{title_en}').\n"
                f"Return JSON with 'it' and 'en' keys as specified."
            )
        }]
    )

    raw = response.content[0].text.strip()

    # Parse JSON — strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        data = json.loads(raw)
        content_it = data.get("it", "").strip()
        content_en = data.get("en", "").strip()
        if not content_it or not content_en:
            raise ValueError("Empty content in response")
        return content_it, content_en
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse Claude response for '{title_it}': {e}")
        logger.error(f"Raw response: {raw[:500]}")
        # Fallback: treat entire response as Italian content, use as English too
        return raw, raw
