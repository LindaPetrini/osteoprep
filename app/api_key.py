"""Extract user-provided Anthropic API key from request header or cookie."""
from fastapi import Request


def get_user_api_key(request: Request) -> str | None:
    """Get API key from X-Anthropic-Key header (fetch calls) or cookie (page loads)."""
    return request.headers.get("X-Anthropic-Key") or request.cookies.get("anthropic_api_key") or None
