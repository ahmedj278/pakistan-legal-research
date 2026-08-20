"""
LLM abstraction (Module 5, Session 5.1).

Wraps the actual LLM API call behind a small interface, same
reasoning as embeddings.py/reranker.py: RAG code should depend on
this module's generate() function, not on a specific provider's SDK
directly — so the LLM could be swapped later (different provider,
different model) via config alone, without touching any calling
code.

Default provider: Gemini, not Anthropic. Reasoning: Anthropic and
OpenAI only offer a small one-time trial credit (~$5, requires phone
verification), not an ongoing free tier. Google's Gemini API, via
Google AI Studio, offers a genuinely free, permanent, no-credit-card
tier (verified via web search, not assumed from memory, since
pricing/free-tier terms change often) — the right default for a
student project with no budget. Anthropic is kept available as a
second option (e.g. if the user later gets access to credits).
"""

from app.config import settings


def _generate_anthropic(prompt: str, system: str, max_tokens: int) -> str:
    if not settings.llm_api_key:
        raise RuntimeError(
            "LLM_API_KEY is not set in .env — required to call the Anthropic API. "
            "Get one at https://console.anthropic.com (note: only a small one-time "
            "trial credit, not an ongoing free tier — consider LLM_PROVIDER=gemini instead)."
        )

    # Imported lazily, and after the API-key check above, so a
    # missing key gives its own clear error rather than being masked
    # by an import error if the `anthropic` package isn't installed.
    import anthropic

    client = anthropic.Anthropic(api_key=settings.llm_api_key)
    response = client.messages.create(
        model=settings.llm_model_name,
        max_tokens=max_tokens,
        system=system or "",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _generate_gemini(prompt: str, system: str, max_tokens: int) -> str:
    if not settings.llm_api_key:
        raise RuntimeError(
            "LLM_API_KEY is not set in .env — required to call the Gemini API. "
            "Get a FREE key (no credit card needed) at https://aistudio.google.com/apikey"
        )

    # Imported lazily, same reasoning as the Anthropic branch above.
    from google import genai

    client = genai.Client(api_key=settings.llm_api_key)

    # NOTE: verified against Google's most recently published SDK
    # docs at build time (not from training data, since this SDK has
    # changed shape before), but Google's Python GenAI SDK is
    # actively evolving — if this errors on your machine, check
    # whatever `pip install google-genai` actually installed against
    # its own quickstart example and adjust this function to match.
    #
    # This SDK version doesn't cleanly expose a separate system-vs-
    # user-content split the way Anthropic's does, so system
    # instructions are simply prepended to the prompt — a reliable
    # fallback regardless of exact API shape.
    combined_input = f"{system}\n\n{prompt}" if system else prompt

    response = client.models.generate_content(
        model=settings.llm_model_name,
        contents=combined_input,
    )
    return response.text


PROVIDERS = {
    "anthropic": _generate_anthropic,
    "gemini": _generate_gemini,
}


def generate(prompt: str, system: str = None, max_tokens: int = 1024) -> str:
    provider_fn = PROVIDERS.get(settings.llm_provider)
    if provider_fn is None:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{settings.llm_provider}'. "
            f"Supported: {list(PROVIDERS.keys())}"
        )
    return provider_fn(prompt, system, max_tokens)
