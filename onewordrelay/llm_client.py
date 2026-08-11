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

    def polish_transcript(self, raw_text: str) -> str:
        """
        Takes a raw string of words and returns a punctuated, 
        grammatically correct version without changing word order.
        """
        system_prompt = "You are a strict linguistic editor. Your only job is to add punctuation and capitalization."
        user_prompt = (
            f"Below is a raw transcript of a one-word-at-a-time game:\n\n\"{raw_text}\"\n\n"
            "TASK: Rewrite this into a grammatically correct paragraph.\n"
            "STRICT CONSTRAINT: You MUST NOT change, add, or remove any words. "
            "The word sequence must remain exactly as provided. "
            "Do not 'correct' the vocabulary or word order. "
            "ONLY add punctuation and capitalization.\n\n"
            "Return ONLY the polished text."
        )
        
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 1000,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            return self._make_request(endpoint, payload, headers).strip()
        except Exception as e:
            return f"[Polishing failed: {e}]"
