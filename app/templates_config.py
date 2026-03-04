import json
import random
import re

from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt

templates = Jinja2Templates(directory="app/templates")

_md = MarkdownIt()

# Maps Claude-generated heading variants to canonical section slugs
SECTION_SLUG_MAP = {
    "definizione": "definizione",
    "definition": "definizione",
    "struttura": "struttura",
    "struttura / composizione": "struttura",
    "composizione": "struttura",
    "structure": "struttura",
    "structure / composition": "struttura",
    "meccanismo": "meccanismo",
    "meccanismo / funzione": "meccanismo",
    "funzione": "meccanismo",
    "mechanism": "meccanismo",
    "mechanism / function": "meccanismo",
    "reazione": "meccanismo",
    "reaction": "meccanismo",
    "dati chiave": "dati_chiave",
    "key data": "dati_chiave",
    "perché è importante": "importanza",
    "why it matters": "importanza",
    "connessioni agli altri argomenti": "connessioni",
    "connections": "connessioni",
    "focus esame": "focus_esame",
    "exam focus": "focus_esame",
}


def render_markdown(text: str) -> str:
    """Convert markdown to HTML (headers, bullets, bold, etc.)."""
    return _md.render(text)


def render_uncertainty_markers(text: str) -> str:
    """Convert [UNCERTAIN: text] markers to inline amber callout HTML."""
    return re.sub(
        r'\[UNCERTAIN:\s*([^\]]+)\]',
        r'<span class="inline-block bg-amber-100 border border-amber-300 text-amber-800 '
        r'text-sm px-2 py-0.5 rounded mx-0.5 my-0.5">'
        r'<strong>⚠</strong> \1</span>',
        text
    )


def render_content(text: str) -> str:
    """Full pipeline: markdown → HTML, then uncertainty markers."""
    return render_uncertainty_markers(render_markdown(text))


def split_sections(text: str) -> list[dict]:
    """Split markdown into sections by ## headings.
    Returns list of {heading, body, slug} dicts.
    First section has empty heading if content precedes first ##."""
    parts = re.split(r'\n(?=## )', '\n' + text)
    sections = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part.startswith('## '):
            lines = part.split('\n', 1)
            heading = lines[0][3:].strip()
            body = lines[1].strip() if len(lines) > 1 else ''
            slug = SECTION_SLUG_MAP.get(
                heading.lower(),
                heading.lower().replace(' ', '_').replace('/', '_')
            )
            sections.append({"heading": heading, "body": body, "slug": slug})
        else:
            sections.append({"heading": "", "body": part, "slug": "intro"})
    return sections


def shuffle_choices(choices: list[str]) -> list[tuple[int, str]]:
    """Return list of (original_index, choice_text) in shuffled order.

    Radio-button values stay tied to the original index so the router can
    compare against the stored correct_index without any mapping.
    """
    indexed = list(enumerate(choices))
    random.shuffle(indexed)
    return indexed


def distribute_questions(sq_map: dict, num_sections: int) -> dict[int, list]:
    """Flatten all section questions and distribute across N sections (by index).
    Returns {section_index: [(sq_id, q_index, q_data), ...]}.
    Spreads questions evenly so each prose section gets ~equal mini-tests."""
    all_qs = []
    for sq in sq_map.values():
        questions = json.loads(sq["questions_json"]) if sq.get("questions_json") else [
            {"question_it": sq["question_it"], "choices": json.loads(sq["choices_json"]) if isinstance(sq["choices_json"], str) else sq["choices_json"], "correct_index": sq["correct_index"]}
        ]
        for qi, q_data in enumerate(questions):
            all_qs.append((sq["id"], qi, q_data))

    if not all_qs or num_sections <= 0:
        return {}

    # Distribute round-robin across sections (skip index 0 if it's just intro text)
    start = 1 if num_sections > 1 else 0
    slots = max(num_sections - start, 1)
    result: dict[int, list] = {}
    for i, q_tuple in enumerate(all_qs):
        idx = start + (i % slots)
        result.setdefault(idx, []).append(q_tuple)
    return result


templates.env.filters["render_content"] = render_content
templates.env.filters["uncertainty"] = render_uncertainty_markers
templates.env.filters["split_sections"] = split_sections
templates.env.filters["fromjson"] = json.loads
templates.env.globals["shuffle_choices"] = shuffle_choices
templates.env.globals["distribute_questions"] = distribute_questions
