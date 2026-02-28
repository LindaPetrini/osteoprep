from fastapi.templating import Jinja2Templates
import re
from markdown_it import MarkdownIt

templates = Jinja2Templates(directory="app/templates")

_md = MarkdownIt()

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

templates.env.filters["render_content"] = render_content
templates.env.filters["uncertainty"] = render_uncertainty_markers
