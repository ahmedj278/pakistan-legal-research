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

A third provider, "ollama", is available purely for LOCAL TESTING
when Gemini's daily free-tier quota is exhausted — it costs nothing
and has no rate limit, since it runs entirely on the developer's own
machine. It is NOT a production default (settings.llm_provider still
defaults to "gemini") and answer quality will generally be lower
than Gemini/Anthropic for a small local model — that tradeoff is
expected and fine for testing the pipeline's plumbing (does
retrieval -> LLM -> citations wire together correctly?), not for
judging real answer quality.
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
    from google.genai import types

    client = genai.Client(api_key=settings.llm_api_key)

    # NOTE: verified directly against the installed google-genai SDK
    # (not assumed from memory or from an older comment in this file —
    # this SDK has changed shape before). types.GenerateContentConfig
    # exposes both system_instruction and max_output_tokens, so both
    # are set properly here rather than working around their absence.
    response = client.models.generate_content(
        model=settings.llm_model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system or None,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text


def _generate_ollama(prompt: str, system: str, max_tokens: int) -> str:
    """
    Local model via Ollama's REST API (default http://localhost:11434).

    Requires Ollama to actually be running (`ollama serve`, or the
    desktop app open) AND at least one model already pulled — run
    `ollama list` to check what's available, `ollama pull <name>` if
    nothing suitable is there. settings.llm_model_name must match a
    pulled model's exact tag (e.g. "llama3.2:3b"), not a Gemini/
    Anthropic model name — this is a real, easy-to-hit misconfig when
    switching LLM_PROVIDER without also updating LLM_MODEL_NAME.

    No API key needed — that's the point of using this for testing.
    """
    import requests

    base_url = settings.ollama_base_url
    messages = (
        ([{"role": "system", "content": system}] if system else [])
        + [{"role": "user", "content": prompt}]
    )

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": settings.llm_model_name,
                "messages": messages,
                "stream": False,
                "options": {"num_predict": max_tokens},
            },
            timeout=120,
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Could not reach Ollama at {base_url}. Is it running? "
            f"Start it with `ollama serve` (or open the Ollama desktop "
            f"app), then confirm a model is pulled with `ollama list`."
        )

    if response.status_code == 404:
        raise RuntimeError(
            f"Ollama returned 404 for model '{settings.llm_model_name}'. "
            f"This usually means that model isn't pulled — run `ollama list` "
            f"to see what IS available, and set LLM_MODEL_NAME in .env to "
            f"match one of those tags exactly (e.g. 'llama3.2:3b')."
        )

    response.raise_for_status()
    return response.json()["message"]["content"]


PROVIDERS = {
    "anthropic": _generate_anthropic,
    "gemini": _generate_gemini,
    "ollama": _generate_ollama,
}


def generate(prompt: str, system: str = None, max_tokens: int = 1024) -> str:
    provider_fn = PROVIDERS.get(settings.llm_provider)
    if provider_fn is None:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{settings.llm_provider}'. "
            f"Supported: {list(PROVIDERS.keys())}"
        )
    return provider_fn(prompt, system, max_tokens)
