"""
AI Provider Abstraction: Supports OpenAI-compatible APIs (e.g. local endpoint http://127.0.0.1:20128/v1),
OpenAI, Ollama, and seamless deterministic fallback when AI is disabled.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AIProvider:
    def __init__(
        self,
        enabled: Optional[bool] = None,
        provider_type: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.enabled = (
            enabled
            if enabled is not None
            else os.getenv("ENABLE_AI_SCORING", "false").lower() in ("true", "1", "yes")
        )
        self.provider_type = provider_type or os.getenv("AI_PROVIDER", "openai_compatible")
        self.base_url = (base_url or os.getenv("AI_BASE_URL", "http://127.0.0.1:20128/v1")).rstrip("/")
        self.model = model or os.getenv("AI_MODEL", "auto")
        self.api_key = api_key or os.getenv("AI_API_KEY", "")

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """
        Sends a chat completion request to the OpenAI-compatible endpoint.
        Returns text response or None if disabled/unreachable.
        """
        if not self.enabled:
            logger.debug("AI scoring is disabled. Skipping LLM request.")
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"].get("content", "")
                else:
                    logger.warning(f"AI endpoint returned HTTP {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"AI endpoint request failed: {e}. Falling back to deterministic scoring.")

        return None
