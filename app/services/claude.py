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
