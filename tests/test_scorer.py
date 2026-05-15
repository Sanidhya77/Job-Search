"""Tests for the scorer module.

One real OpenAI call was made to capture sample_scorer_response.json.
All tests here run offline by replaying that fixture or constructing
synthetic JSON strings.
"""

import json
from pathlib import Path

import pytest

from job_agent.llm.client import LLMError
from job_agent.llm.scorer import (
    ScorerError,
    build_scorer_message,
    parse_scorer_response,
    score_job,
)
from job_agent.models import Job, ScoredJob, UserProfile


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_scorer_response.json"


def _sample_profile() -> UserProfile:
    return UserProfile(
        full_name="Jane Doe",
        skills=["Python", "SQL", "pandas"],
        years_of_experience=3.0,
        seniority="mid",
        domains=["data analysis"],
        languages=["English"],
        location_preference="Berlin",
        remote_preference="hybrid",
        raw_cv_text="Sample CV text.",
    )


def _sample_job() -> Job:
    return Job(
        title="Junior Data Analyst",
        company="Acme",
        location="Berlin",
        description="Looking for a data analyst with Python and SQL.",
        apply_url="https://example.com/apply/1",
    )


# ---------- build_scorer_message ----------


def test_message_contains_profile_and_job_sections():
    """The formatted message has the section headers the prompt expects."""
    message = build_scorer_message(_sample_profile(), _sample_job())
    assert "CANDIDATE PROFILE:" in message
    assert "JOB LISTING:" in message
    assert "Jane Doe" in message
    assert "Junior Data Analyst" in message


def test_message_handles_empty_skill_list():
    """An empty skills list does not crash the formatter."""
    profile = _sample_profile()
    profile = UserProfile(
        full_name=profile.full_name,
        skills=[],
        years_of_experience=profile.years_of_experience,
        seniority=profile.seniority,
        domains=profile.domains,
        languages=profile.languages,
        location_preference=profile.location_preference,
        remote_preference=profile.remote_preference,
        raw_cv_text=profile.raw_cv_text,
    )
    message = build_scorer_message(profile, _sample_job())
    assert "Skills: none listed" in message


# ---------- parse_scorer_response with real fixture ----------


def test_parse_real_fixture_yields_scored_job():
    """The captured OpenAI response parses into a valid ScoredJob."""
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        fixture = json.load(f)
    raw = fixture["raw_response"]

    scored = parse_scorer_response(raw, _sample_job())

    assert isinstance(scored, ScoredJob)
    assert 0 <= scored.score <= 100
    assert scored.reasoning


# ---------- parse_scorer_response with synthetic JSON ----------


def test_parse_valid_minimal_json():
    """A minimal valid response parses cleanly."""
    raw = json.dumps({"score": 75, "reasoning": "Strong skill overlap."})
    scored = parse_scorer_response(raw, _sample_job())
    assert scored.score == 75


def test_parse_raises_on_invalid_json():
    """Garbage JSON is rejected with a clear error."""
    with pytest.raises(ScorerError, match="not valid JSON"):
        parse_scorer_response("not json", _sample_job())


def test_parse_raises_on_missing_score():
    """A response with no score field is rejected."""
    raw = json.dumps({"reasoning": "no score"})
    with pytest.raises(ScorerError, match="missing 'score'"):
        parse_scorer_response(raw, _sample_job())


def test_parse_raises_on_missing_reasoning():
    """A response with no reasoning field is rejected."""
    raw = json.dumps({"score": 50})
    with pytest.raises(ScorerError, match="missing 'reasoning'"):
        parse_scorer_response(raw, _sample_job())


def test_parse_raises_on_non_integer_score():
    """A score that is not an integer is rejected."""
    raw = json.dumps({"score": "high", "reasoning": "ok"})
    with pytest.raises(ScorerError, match="not an integer"):
        parse_scorer_response(raw, _sample_job())


def test_parse_raises_on_out_of_range_score():
    """A score outside 0-100 is rejected."""
    raw = json.dumps({"score": 150, "reasoning": "ok"})
    with pytest.raises(ScorerError, match="out of range"):
        parse_scorer_response(raw, _sample_job())


def test_parse_raises_on_empty_reasoning():
    """A blank reasoning string is rejected."""
    raw = json.dumps({"score": 50, "reasoning": "   "})
    with pytest.raises(ScorerError, match="non-empty"):
        parse_scorer_response(raw, _sample_job())


# ---------- score_job (with mocked LLM) ----------


def test_score_job_returns_scored_job_on_success():
    """A mocked LLM response flows through to a ScoredJob."""
    class MockClient:
        def complete(self, system, user, response_format_json=False):
            return json.dumps({"score": 82, "reasoning": "Good match."})

    scored = score_job(_sample_profile(), _sample_job(), client=MockClient())
    assert scored.score == 82
    assert "Good match" in scored.reasoning


def test_score_job_wraps_llm_error():
    """An LLMError from the client is surfaced as ScorerError."""
    class FailingClient:
        def complete(self, system, user, response_format_json=False):
            raise LLMError("network down")

    with pytest.raises(ScorerError, match="LLM call failed"):
        score_job(_sample_profile(), _sample_job(), client=FailingClient())
