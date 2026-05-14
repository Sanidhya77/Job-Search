"""Tests for the LLM client wrapper.

All tests run offline by mocking the underlying OpenAI client. No real
API call is ever made from pytest.
"""

from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError, RateLimitError

from job_agent.llm.client import LLMClient, LLMError


def _make_mock_response(content: str):
    """Build a mock that mimics the OpenAI SDK's response object shape."""
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


def test_client_rejects_empty_api_key():
    """An empty key is rejected at construction, not at call time."""
    with pytest.raises(LLMError, match="empty"):
        LLMClient(api_key="")
    with pytest.raises(LLMError, match="empty"):
        LLMClient(api_key="   ")


def test_client_complete_returns_assistant_message():
    """A successful call returns the assistant's reply as a string."""
    client = LLMClient(api_key="test-key")

    with patch.object(client.__class__, "client", new_callable=MagicMock) as mock_openai:
        mock_openai.chat.completions.create.return_value = _make_mock_response("Hello, world.")
        result = client.complete(system="You are helpful.", user="Say hi.")

    assert result == "Hello, world."


def test_client_complete_strips_whitespace():
    """Leading and trailing whitespace in the reply is stripped."""
    client = LLMClient(api_key="test-key")

    with patch.object(client.__class__, "client", new_callable=MagicMock) as mock_openai:
        mock_openai.chat.completions.create.return_value = _make_mock_response("  reply  \n")
        result = client.complete(system="x", user="y")

    assert result == "reply"


def test_client_complete_raises_on_empty_response():
    """An empty assistant message is treated as a failure, not silent."""
    client = LLMClient(api_key="test-key")

    with patch.object(client.__class__, "client", new_callable=MagicMock) as mock_openai:
        mock_openai.chat.completions.create.return_value = _make_mock_response("")
        with pytest.raises(LLMError, match="empty"):
            client.complete(system="x", user="y")


def test_client_passes_response_format_json_flag():
    """When response_format_json=True, the API is called with the JSON mode flag."""
    client = LLMClient(api_key="test-key")

    with patch.object(client.__class__, "client", new_callable=MagicMock) as mock_openai:
        mock_openai.chat.completions.create.return_value = _make_mock_response("{}")
        client.complete(system="x", user="y", response_format_json=True)

    call_kwargs = mock_openai.chat.completions.create.call_args.kwargs
    assert call_kwargs.get("response_format") == {"type": "json_object"}


def test_client_does_not_set_response_format_by_default():
    """When response_format_json=False, no response_format is sent."""
    client = LLMClient(api_key="test-key")

    with patch.object(client.__class__, "client", new_callable=MagicMock) as mock_openai:
        mock_openai.chat.completions.create.return_value = _make_mock_response("text")
        client.complete(system="x", user="y")

    call_kwargs = mock_openai.chat.completions.create.call_args.kwargs
    assert "response_format" not in call_kwargs


def test_client_wraps_non_retryable_error():
    """A non-retryable error (e.g. bad request) is wrapped in LLMError."""
    from openai import APIError

    client = LLMClient(api_key="test-key")

    with patch.object(client.__class__, "client", new_callable=MagicMock) as mock_openai:
        mock_openai.chat.completions.create.side_effect = APIError(
            message="Bad request", request=MagicMock(), body=None
        )
        with pytest.raises(LLMError, match="LLM call failed"):
            client.complete(system="x", user="y")


def test_client_wraps_unexpected_exception():
    """An unexpected exception is also wrapped in LLMError, not leaked."""
    client = LLMClient(api_key="test-key")

    with patch.object(client.__class__, "client", new_callable=MagicMock) as mock_openai:
        mock_openai.chat.completions.create.side_effect = RuntimeError("unknown")
        with pytest.raises(LLMError, match="Unexpected"):
            client.complete(system="x", user="y")
