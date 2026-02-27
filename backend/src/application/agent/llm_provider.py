"""LLM Provider — abstract base and concrete Gemini implementation.

The provider is a simple adapter that calls an LLM API and returns the
raw text response. JSON parsing is the caller's responsibility.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    async def complete(self, messages: list[dict]) -> str:
        """Send messages to the LLM and return the raw text response.

        Args:
            messages: List of dicts with ``role`` ("user" | "model")
                      and ``content`` (str).

        Returns:
            Raw text string from the model.
        """


class GeminiProvider(LLMProvider):
    """Google Gemini provider via REST API (httpx).

    Uses the ``generativelanguage.googleapis.com`` endpoint directly,
    no SDK required.
    """

    _BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    _TIMEOUT = 30  # seconds

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self.api_key = api_key
        self.model = model

    def _build_contents(self, messages: list[dict]) -> list[dict]:
        """Convert our message format to Gemini's ``contents`` format.

        Maps:
            role "user"    -> Gemini role "user"
            role "model"   -> Gemini role "model"
            role "system"  -> extracted as system instruction
        """
        contents: list[dict] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                # System messages handled separately
                continue
            gemini_role = "model" if role in ("model", "assistant") else "user"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}],
            })
        return contents

    def _extract_system_instruction(self, messages: list[dict]) -> str | None:
        """Extract system instruction from messages if present."""
        for msg in messages:
            if msg.get("role") == "system":
                return msg.get("content")
        return None

    async def complete(self, messages: list[dict]) -> str:
        """Call Gemini generateContent and return the raw text."""
        url = (
            f"{self._BASE_URL}/models/{self.model}:generateContent"
        )

        body: dict = {
            "contents": self._build_contents(messages),
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
            },
        }

        system_instruction = self._extract_system_instruction(messages)
        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}],
            }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        async with httpx.AsyncClient(timeout=self._TIMEOUT) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # Extract text from the first candidate
        candidates = data.get("candidates", [])
        if not candidates:
            return ""

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return ""

        return parts[0].get("text", "")
