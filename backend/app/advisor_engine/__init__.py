"""Advisor engine: optional post-scan explanation layer.

Provider selection is via the ADVISOR_PROVIDER environment variable:

  rule_based (default)  free, offline, deterministic templates and rules
  off / none            disable advisor notes entirely
  ollama / anthropic / openai
                        optional LLM slots — currently explicit stubs that
                        raise instead of calling anything (see
                        optional_llm_provider.py). Never selected by default.

The advisor never changes the score — it only adds notes.
"""

import os
from typing import Optional

from .base import AdvisorInput, AdvisorProvider
from .rule_based_provider import RuleBasedProvider

__all__ = ["AdvisorInput", "AdvisorProvider", "RuleBasedProvider", "get_advisor"]

_LLM_PROVIDER_NAMES = ("ollama", "anthropic", "openai", "llm")


def get_advisor() -> Optional[AdvisorProvider]:
    choice = os.environ.get("ADVISOR_PROVIDER", "rule_based").strip().lower()
    if choice in ("off", "none", "0", "false", ""):
        return None
    if choice in _LLM_PROVIDER_NAMES:
        from .optional_llm_provider import OptionalLLMProvider

        return OptionalLLMProvider(choice)
    # Unknown values fall back to the safe default rather than breaking scans.
    return RuleBasedProvider()
