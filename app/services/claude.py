import os
import json
import logging
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

# System prompt with explicit uncertainty rules and examples
# Key: give concrete examples of what to mark uncertain (numerical values, Italian curriculum specifics)
EXPLAINER_SYSTEM_PROMPT = """You are a study assistant for Italian professional health qualification (professioni sanitarie) and osteopathy entry exams.

Generate detailed, schematic study notes. Dense with information. No filler.

UNCERTAINTY RULES:
- Wrap uncertain numerical values in [UNCERTAIN: ...] (e.g. [UNCERTAIN: ~180 g/mol])
- Use for contested data or Italian curriculum-specific details
- Do NOT mark well-established facts

OUTPUT STRUCTURE — follow this markdown template exactly:

## Definizione
One precise sentence. What it is, where it exists, what its core purpose is.

## Struttura / Composizione
Bullet list — each bullet covers one component/layer/part with:
- Its name
- What it is made of or how it is arranged
- Its specific role or property
Example: "- Membrana plasmatica: doppio strato fosfolipidico (~7 nm), delimita la cellula, permeabilità selettiva — lipidi passano liberamente, ioni richiedono proteine canale"

## Meccanismo / Funzione
How it works. Number steps if sequential, bullets if parallel processes.
Each step: what happens + why it matters. Be specific about molecules, directions, results.

## Dati chiave
Testable numbers and facts — each bullet one concrete datum:
- Sizes, temperatures, pH values, concentrations, counts, timings
- Use [UNCERTAIN: ...] where not 100% certain

## Perché è importante / Contesto
2-3 sentences of biological or chemical context: why this structure/process matters in the bigger picture, what would fail without it, how it connects to physiology or pathology.

## Connessioni agli altri argomenti
3-4 bullets explicitly linking this topic to others on the exam:
- "→ [Topic name]: [how they connect — one specific sentence]"
Example: "→ Respirazione cellulare: la membrana mitocondriale interna è il sito della catena respiratoria, il cui gradiente protonico dipende dalla sua impermeabilità"

## Focus esame
5-6 bullets: most likely exam questions + key facts to memorize.
Format: "❓ [Likely question or fact]"

RULES:
- Every bullet must contain at least one specific, verifiable detail — no vague statements
- Adapt section titles to the topic (e.g. "Reazione" instead of "Meccanismo" for chemistry)
- English version uses English titles (Definition, Structure/Composition, Mechanism/Function, Key Data, Why It Matters, Connections, Exam Focus)

OUTPUT FORMAT — ONLY valid JSON, no markdown wrapper:
{"it": "markdown in Italian", "en": "markdown in English"}"""


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
        max_tokens=4096,  # Richer format — more detail per section
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
