"""LLM backend selection. GEMINI_API_KEY present -> real Gemini client;
otherwise fall back to the deterministic mock so the service still runs.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from notetaker.llm.base import LLMClient
from notetaker.llm.mock import MockClient

load_dotenv()


def get_llm_client() -> LLMClient:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        from notetaker.llm.gemini import GeminiClient

        return GeminiClient(api_key=api_key)
    return MockClient()
