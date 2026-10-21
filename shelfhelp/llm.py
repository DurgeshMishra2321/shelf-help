"""A thin adapter so the LLM provider can be swapped with one env variable.

    LLM_PROVIDER = anthropic (default) | openai | groq | gemini
    LLM_MODEL    = optional model override

The only function the rest of the code uses is complete(system, user).
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

PROVIDERS = {
    #  name:       (API key variable,   default model,              base URL for the OpenAI SDK)
    "anthropic": ("ANTHROPIC_API_KEY", "claude-opus-5-5",           None),
    "openai":    ("OPENAI_API_KEY",    "gpt-4o-mini",               None),
    "groq":      ("GROQ_API_KEY",      "llama-3.3-70b-versatile",   "https://api.groq.com/openai/v1"),
    "gemini":    ("GEMINI_API_KEY",    "gemini-2.5-flash",
                  "https://generativelanguage.googleapis.com/v1beta/openai/"),
}


class LLMError(Exception):
    """A temporary failure (timeout, rate limit, server error). Safe to retry."""


def provider() -> str:
    name = os.getenv("LLM_PROVIDER", "anthropic").strip().lower()
    if name not in PROVIDERS:
        sys.exit(f"error: LLM_PROVIDER={name!r} is not supported. Use one of: {', '.join(PROVIDERS)}")
    return name


def check_config() -> None:
    """Exit with a clear message if the API key for the chosen provider is missing."""
    key_var = PROVIDERS[provider()][0]
    if not os.getenv(key_var):
        sys.exit(f"error: {key_var} is not set. Copy .env.example to .env and add your key "
                 f"(or set LLM_PROVIDER to a provider you have a key for).")


def complete(system: str, user: str, timeout: float = 20) -> str:
    name = provider()
    check_config()
    key_var, default_model, base_url = PROVIDERS[name]
    model = os.getenv("LLM_MODEL") or default_model
    if name == "anthropic":
        return _anthropic(system, user, model, timeout)
    return _openai_compatible(system, user, model, timeout, os.getenv(key_var), base_url)


def _anthropic(system, user, model, timeout):
    import anthropic

    client = anthropic.Anthropic(timeout=timeout, max_retries=0)   # extract.py does the retrying
    try:
        response = client.beta.messages.create(
            model=model,
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": user}],
            # Current Claude models don't take temperature; low effort keeps extraction fast.
            output_config={"effort": "low"},
            # If the model refuses, the API retries on a fallback model for us.
            betas=["server-side-fallback-2026-07-01"],
            extra_body={"fallbacks": "default"},
        )
    except (anthropic.APITimeoutError, anthropic.APIConnectionError,
            anthropic.RateLimitError, anthropic.InternalServerError) as e:
        raise LLMError(f"{type(e).__name__}: {e}") from e
    if response.stop_reason == "refusal":
        raise LLMError("model refused the request")
    return "".join(block.text for block in response.content if block.type == "text")


def _openai_compatible(system, user, model, timeout, api_key, base_url):
    import openai

    client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=0)
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
    except (openai.APITimeoutError, openai.APIConnectionError,
            openai.RateLimitError, openai.InternalServerError) as e:
        raise LLMError(f"{type(e).__name__}: {e}") from e
    return response.choices[0].message.content or ""
