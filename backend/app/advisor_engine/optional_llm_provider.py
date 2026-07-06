"""OPTIONAL LLM advisor providers — DISABLED BY DEFAULT, NOT IMPLEMENTED.

This file exists so the provider interface has a clearly-marked slot for
future AI-backed advisors, without adding any AI dependency today:

  * The default provider is always the free, offline rule_based one.
  * Nothing in this module runs unless a developer explicitly sets
    ADVISOR_PROVIDER to one of the LLM provider names.
  * Even then, this stub makes NO network calls — it raises with an
    explanation, so a misconfigured deployment can never silently start
    paying for API calls.

If you implement a real provider someday, keep these rules:
  1. It must remain opt-in via ADVISOR_PROVIDER; rule_based stays the default.
  2. Resume text must never be stored or logged by the provider.
  3. A provider failure must never break the scan (report_generator already
     guards this) and must never change the score.
  4. Free/local options (e.g. Ollama) should be preferred over paid APIs.

Possible future providers: local_ollama_provider, anthropic_provider,
openai_provider.
"""

from ..models import AdvisorNote
from .base import AdvisorInput, AdvisorProvider


class OptionalLLMProvider(AdvisorProvider):
    """Placeholder for opt-in LLM advisors. Never used by default."""

    def __init__(self, kind: str):
        self.kind = kind
        self.name = f"llm_{kind}"

    def advise(self, data: AdvisorInput) -> list[AdvisorNote]:
        raise RuntimeError(
            f"The '{self.kind}' advisor provider is an optional placeholder and is "
            "not implemented. The base product intentionally requires no AI: unset "
            "ADVISOR_PROVIDER (or set it to 'rule_based') to use the free, offline "
            "default. No paid API calls are ever made by default."
        )
