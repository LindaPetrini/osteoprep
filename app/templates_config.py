from fastapi.templating import Jinja2Templates
import re

templates = Jinja2Templates(directory="app/templates")

def render_uncertainty_markers(text: str) -> str:
    """Convert [UNCERTAIN: text] markers to amber callout HTML blocks."""
    return re.sub(
        r'\[UNCERTAIN:\s*([^\]]+)\]',
        r'<span class="inline-block bg-amber-100 border border-amber-300 text-amber-800 '
        r'text-sm px-2 py-1 rounded mx-0.5 my-0.5">'
        r'<strong>?</strong> \1</span>',
        text
    )

templates.env.filters["uncertainty"] = render_uncertainty_markers
