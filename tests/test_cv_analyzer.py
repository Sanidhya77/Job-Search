"""Tests for the CV analyser.

Real OpenAI was called exactly once to capture
tests/fixtures/sample_cv_analysis_response.json. From then on every
test replays the saved response or constructs synthetic JSON strings.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from job_agent.llm.client import LLMError
from job_agent.llm.cv_analyzer import (
    CVAnalyzerError,
    analyse_cv,
    parse_analyser_response,
)
from job_agent.models import UserProfile


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_cv_analysis_response.json"


# ---------- parse_analyser_response with real fixture ----------


def test_parse_real_fixture_returns_user_profile():
    """The captured real OpenAI response parses into a valid UserProfile."""
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        fixture = json.load(f)
    raw_response = fixture["raw_response"]

    profile = parse_analyser_response(raw_response, cv_text="Sample CV text")

    assert isinstance(profile, UserProfile)
    assert profile.full_name
    assert profile.seniority in {"junior", "mid", "senior"}
    assert isinstance(profile.skills, list)
    assert profile.raw_cv_text == "Sample CV text"


# ---------- parse_analyser_response with synthetic JSON ----------


def test_parse_minimal_valid_json():
    """The minimum fields required are full_name and seniority."""
    raw = json.dumps({
        "full_name": "Jane Doe",
        "skills": [],
        "years_of_experience": 0,
        "seniority": "junior",
        "domains": [],
        "languages": [],
        "location_preference": None,
        "remote_preference": None,
    })
    profile = parse_analyser_response(raw, cv_text="x")
    assert profile.full_name == "Jane Doe"
    assert profile.years_of_experience == 0


def test_parse_raises_on_missing_full_name():
    """A response with no name is a fatal error, not a fallback."""
    raw = json.dumps({"seniority": "mid"})
    with pytest.raises(CVAnalyzerError, match="full_name"):
        parse_analyser_response(raw, cv_text="x")


def test_parse_raises_on_invalid_seniority():
    """Seniority must be one of the three known categories."""
    raw = json.dumps({"full_name": "X", "seniority": "principal"})
    with pytest.raises(CVAnalyzerError, match="Invalid seniority"):
        parse_analyser_response(raw, cv_text="x")


def test_parse_raises_on_invalid_remote_preference():
    """Remote preference is restricted to the documented enum."""
    raw = json.dumps({
        "full_name": "X",
        "seniority": "mid",
        "remote_preference": "occasional",
    })
    with pytest.raises(CVAnalyzerError, match="remote_preference"):
        parse_analyser_response(raw, cv_text="x")


def test_parse_raises_on_non_numeric_years():
    """years_of_experience must be coercible to a float."""
    raw = json.dumps({
        "full_name": "X",
        "seniority": "mid",
        "years_of_experience": "a few",
    })
    with pytest.raises(CVAnalyzerError, match="years_of_experience"):
        parse_analyser_response(raw, cv_text="x")


def test_parse_raises_on_invalid_json():
    """A non-JSON string is rejected with a clear error."""
    with pytest.raises(CVAnalyzerError, match="not valid JSON"):
        parse_analyser_response("this is not json", cv_text="x")


def test_parse_raises_on_non_object_json():
    """A JSON array or scalar is not acceptable; we need an object."""
    with pytest.raises(CVAnalyzerError, match="not a JSON object"):
        parse_analyser_response("[1, 2, 3]", cv_text="x")


def test_parse_defends_against_non_list_skills():
    """If the LLM returns a string for skills, we treat it as empty."""
    raw = json.dumps({
        "full_name": "X",
        "seniority": "mid",
        "skills": "Python, SQL",  # wrong shape on purpose
    })
    profile = parse_analyser_response(raw, cv_text="x")
    assert profile.skills == []


# ---------- analyse_cv (with mocked LLM) ----------


def test_analyse_cv_rejects_empty_text():
    """An empty or whitespace-only CV is rejected before any LLM call."""
    mock_client = type("M", (), {"complete": lambda *a, **k: ""})()
    with pytest.raises(CVAnalyzerError, match="empty"):
        analyse_cv("", client=mock_client)
    with pytest.raises(CVAnalyzerError, match="empty"):
        analyse_cv("   ", client=mock_client)


def test_analyse_cv_returns_profile_on_success():
    """A mocked LLM response is parsed and returned as a UserProfile."""
    mock_response = json.dumps({
        "full_name": "Jane Doe",
        "skills": ["Python"],
        "years_of_experience": 3,
        "seniority": "mid",
        "domains": ["data"],
        "languages": ["English"],
        "location_preference": "Berlin",
        "remote_preference": "hybrid",
    })

    class MockClient:
        def complete(self, system, user, response_format_json=False):
            return mock_response

    profile = analyse_cv("Some CV text", client=MockClient())
    assert profile.full_name == "Jane Doe"
    assert profile.skills == ["Python"]
    assert profile.seniority == "mid"


def test_analyse_cv_wraps_llm_error():
    """An LLMError from the client is surfaced as CVAnalyzerError."""
    class FailingClient:
        def complete(self, system, user, response_format_json=False):
            raise LLMError("network down")

    with pytest.raises(CVAnalyzerError, match="LLM call failed"):
        analyse_cv("Some CV text", client=FailingClient())
