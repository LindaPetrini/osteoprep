import os
import json
import logging
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

# System prompt with explicit uncertainty rules and examples
# Key: give concrete examples of what to mark uncertain (numerical values, Italian curriculum specifics)
EXPLAINER_SYSTEM_PROMPT = """You are a study assistant for Italian professional health qualification (professioni sanitarie) and osteopathy entry exams.

Generate clear, accurate exam-focused explanations. You MUST follow these uncertainty rules:

UNCERTAINTY RULES (critical — apply these strictly):
- When stating specific numerical values (molecular weights, exact ATP counts, enzyme concentrations, percentages), wrap them in [UNCERTAIN: ...] if you are not 100% certain
- Example: glucose has [UNCERTAIN: approximately 180.16 g/mol molecular weight] — do NOT state as exact if unsure
- When stating Italian curriculum-specific details (exact syllabus scope, official topic lists), use [UNCERTAIN: ...]
- When scientific sources disagree or data is contested, use [UNCERTAIN: sources disagree on exact value]
- You may write "this is not fully established" or include [UNCERTAIN: ...] rather than fabricating confident specifics
- Do NOT apply [UNCERTAIN: ...] to well-established general concepts (cell has a nucleus, DNA is a double helix, etc.)

OUTPUT FORMAT — return ONLY valid JSON, no markdown:
{"it": "full Italian explanation here", "en": "full English explanation here"}

Each explanation should:
- Be structured with clear headings (use ** for bold section headers)
- Use bullet points for lists
- Be 400-600 words per language
- Be appropriate for exam preparation (factual, organized, complete)"""


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
