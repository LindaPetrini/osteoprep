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


templates.env.filters["render_content"] = render_content
templates.env.filters["uncertainty"] = render_uncertainty_markers
templates.env.filters["split_sections"] = split_sections
