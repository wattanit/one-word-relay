import requests
import os
from typing import List, Dict, Any
from onewordrelay.config import get_llm_env_config

class LLMClient:
    """
    A client for OpenAI-compatible chat-completions endpoints.
    (HC-2, FR-19)
    """
    def __init__(self):
        config = get_llm_env_config()
        self.base_url = config["base_url"].rstrip("/")
        self.model = config["model"]
        self.api_key = config["api_key"]

    def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """
        Sends a request to the LLM endpoint and returns the response text.
        Implements a single retry on failure (Error Handling Policy).
        """
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.9, # High temperature to encourage candidate variety (FR-10/12)
            "max_tokens": 20,    # Small window to keep costs low and responses focused
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            return self._make_request(endpoint, payload, headers)
        except Exception as e:
            # Retry once (Error Handling Policy)
            try:
                return self._make_request(endpoint, payload, headers)
            except Exception as final_e:
                # Halt the session (handled by the caller, but we raise a clear error)
                raise RuntimeError(f"LLM call failed after retry: {final_e}")

    def _make_request(self, endpoint: str, payload: Dict[str, Any], headers: Dict[str, str]) -> str:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
