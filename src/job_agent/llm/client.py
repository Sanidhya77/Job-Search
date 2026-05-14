"""Thin wrapper around the OpenAI Python SDK.

One module owns the HTTP call so retry logic, error wrapping, and the
model name live in exactly one place. The three LLM reasoning modules
(cv_analyzer, scorer, rewriter) call this wrapper rather than the SDK
directly, which means changing the underlying provider later requires
touching only this file.
"""

import time
from typing import Optional

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    OpenAI,
    RateLimitError,
)


# Default model. Configurable per-instance, but this is the model the
# whole project is budgeted around and that the prompts are tuned for.
DEFAULT_MODEL = "gpt-4o-mini"

# Retry policy. We retry only on errors that have a reasonable chance
# of succeeding on a second attempt: rate limits, transient network
# errors, and 5xx responses from the API. Bad requests, auth failures,
# and missing-model errors are not retried because they will fail the
# same way every time.
RETRYABLE_EXCEPTIONS = (RateLimitError, APIConnectionError)
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 1.0


class LLMError(Exception):
    """Raised when the LLM call cannot be completed.

    Wraps the underlying SDK exceptions so callers only handle one
    exception type per LLM-based module instead of branching on each
    possible OpenAI error class.
    """


class LLMClient:
    """Wrapper around the OpenAI chat completions endpoint.

    Holds the API key and model name. Exposes a single complete()
    method that takes a system prompt and a user message and returns
    the assistant's reply as a string.
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        if not api_key or not api_key.strip():
            raise LLMError("OpenAI API key is empty.")
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """Lazy OpenAI client init so unit tests can mock without a key."""
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        response_format_json: bool = False,
    ) -> str:
        """Send a chat completion request and return the assistant's reply.

        Args:
            system: System prompt that constrains the model's behaviour.
            user: User message containing the actual input data.
            temperature: Sampling temperature. Default 0.2 for analytical
                tasks where consistency matters more than creativity.
            response_format_json: When True, instructs the API to return
                a JSON object via the response_format parameter. Used by
                cv_analyzer and scorer where the prompt expects strict JSON.

        Returns:
            The assistant's reply as a single string.

        Raises:
            LLMError: If the call fails after all retries or returns an
                empty response.
        """
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format_json:
            kwargs["response_format"] = {"type": "json_object"}

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
            except RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                # Exponential backoff: 1s, 2s, 4s, ...
                if attempt < self.max_retries - 1:
                    time.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
                    continue
                raise LLMError(
                    f"LLM call failed after {self.max_retries} retries: {exc}"
                ) from exc
            except (APIStatusError, APIError) as exc:
                # Non-retryable: bad request, auth failure, model not found.
                raise LLMError(f"LLM call failed: {exc}") from exc
            except Exception as exc:
                # Anything else (network library bugs, etc.) is wrapped too.
                raise LLMError(f"Unexpected LLM error: {exc}") from exc

            content = response.choices[0].message.content
            if not content or not content.strip():
                raise LLMError("LLM returned an empty response.")
            return content.strip()

        # Should be unreachable, but keeps the type checker happy.
        raise LLMError(f"LLM call failed: {last_exc}")
