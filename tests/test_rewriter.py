"""Tests for the rewriter module.

One real OpenAI call was made to capture sample_rewriter_response.json.
All tests here run offline by replaying that fixture or constructing
synthetic JSON strings.
"""

import json
from pathlib import Path

import pytest

from job_agent.llm.client import LLMError
from job_agent.llm.rewriter import (
    MIN_COVER_LETTER_LENGTH,
    MIN_CV_LENGTH,
    MIN_SUMMARY_LENGTH,
    RewriterError,
    build_rewriter_message,
    parse_rewriter_response,
    rewrite_for_job,
)
from job_agent.models import Application, Job, UserProfile


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_rewriter_response.json"


def _sample_profile(with_cv_text: bool = True) -> UserProfile:
    return UserProfile(
        full_name="Jane Doe",
        skills=["Python", "SQL"],
        years_of_experience=3.0,
        seniority="mid",
        domains=["data analysis"],
        languages=["English"],
        location_preference="Berlin",
        remote_preference="hybrid",
        raw_cv_text="Jane Doe\n\nExperience\n\nAcme - Data Analyst (2022-2024)\nBuilt Python pipelines." if with_cv_text else "",
    )


def _sample_job() -> Job:
    return Job(
        title="Junior Data Analyst",
        company="Acme",
        location="Berlin",
        description="Looking for a data analyst with Python and SQL.",
        apply_url="https://example.com/apply/1",
    )


# ---------- build_rewriter_message ----------


def test_message_contains_full_cv_and_job():
    """The formatted message includes both CV text and job description."""
    message = build_rewriter_message(_sample_profile(), _sample_job())
    assert "CANDIDATE CV" in message
    assert "TARGET JOB" in message
    assert "Jane Doe" in message
    assert "Junior Data Analyst" in message
    assert "Python pipelines" in message  # from raw_cv_text


# ---------- parse_rewriter_response with real fixture ----------


def test_parse_real_fixture_yields_application():
    """The captured rewriter response parses into a valid Application."""
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        fixture = json.load(f)
    raw = fixture["raw_response"]

    application = parse_rewriter_response(raw, _sample_job(), score=80)

    assert isinstance(application, Application)
    assert application.score == 80
    assert len(application.tailored_cv) >= MIN_CV_LENGTH
    assert len(application.cover_letter) >= MIN_COVER_LETTER_LENGTH
    assert len(application.job_summary) >= MIN_SUMMARY_LENGTH


# ---------- parse_rewriter_response with synthetic JSON ----------


def _valid_response() -> str:
    return json.dumps({
        "tailored_cv": "A" * 200,
        "cover_letter": "B" * 300,
        "job_summary": "C" * 50,
    })


def test_parse_valid_response():
    """A response that meets all thresholds parses cleanly."""
    application = parse_rewriter_response(_valid_response(), _sample_job(), score=75)
    assert application.score == 75
    assert application.tailored_cv.startswith("A")


def test_parse_raises_on_invalid_json():
    """Garbage JSON is rejected."""
    with pytest.raises(RewriterError, match="not valid JSON"):
        parse_rewriter_response("not json", _sample_job(), score=75)


def test_parse_raises_on_non_object_json():
    """JSON arrays and scalars are rejected."""
    with pytest.raises(RewriterError, match="not a JSON object"):
        parse_rewriter_response("[1,2,3]", _sample_job(), score=75)


def test_parse_raises_on_missing_tailored_cv():
    """A response with no tailored_cv field is rejected."""
    raw = json.dumps({"cover_letter": "B" * 300, "job_summary": "C" * 50})
    with pytest.raises(RewriterError, match="tailored_cv"):
        parse_rewriter_response(raw, _sample_job(), score=75)


def test_parse_raises_on_missing_cover_letter():
    """A response with no cover_letter field is rejected."""
    raw = json.dumps({"tailored_cv": "A" * 200, "job_summary": "C" * 50})
    with pytest.raises(RewriterError, match="cover_letter"):
        parse_rewriter_response(raw, _sample_job(), score=75)


def test_parse_raises_on_missing_summary():
    """A response with no job_summary field is rejected."""
    raw = json.dumps({"tailored_cv": "A" * 200, "cover_letter": "B" * 300})
    with pytest.raises(RewriterError, match="job_summary"):
        parse_rewriter_response(raw, _sample_job(), score=75)


def test_parse_raises_on_short_cv():
    """A tailored_cv below the minimum length triggers a truncation error."""
    raw = json.dumps({
        "tailored_cv": "tiny",
        "cover_letter": "B" * 300,
        "job_summary": "C" * 50,
    })
    with pytest.raises(RewriterError, match="too short"):
        parse_rewriter_response(raw, _sample_job(), score=75)


def test_parse_raises_on_short_cover_letter():
    """A cover letter below the minimum length is rejected."""
    raw = json.dumps({
        "tailored_cv": "A" * 200,
        "cover_letter": "Hi.",
        "job_summary": "C" * 50,
    })
    with pytest.raises(RewriterError, match="too short"):
        parse_rewriter_response(raw, _sample_job(), score=75)


def test_parse_raises_on_non_string_field():
    """A field that comes back as a number or list is rejected."""
    raw = json.dumps({
        "tailored_cv": 12345,
        "cover_letter": "B" * 300,
        "job_summary": "C" * 50,
    })
    with pytest.raises(RewriterError, match="must be a string"):
        parse_rewriter_response(raw, _sample_job(), score=75)


# ---------- rewrite_for_job (with mocked LLM) ----------


def test_rewrite_for_job_rejects_empty_raw_cv():
    """A UserProfile without raw_cv_text is rejected before any LLM call."""
    mock_client = type("M", (), {"complete": lambda *a, **k: ""})()
    with pytest.raises(RewriterError, match="raw_cv_text is empty"):
        rewrite_for_job(_sample_profile(with_cv_text=False), _sample_job(), score=80, client=mock_client)


def test_rewrite_for_job_returns_application_on_success():
    """A mocked LLM response flows through to an Application."""
    class MockClient:
        def complete(self, system, user, response_format_json=False):
            return json.dumps({
                "tailored_cv": "A" * 200,
                "cover_letter": "B" * 300,
                "job_summary": "C" * 50,
            })

    application = rewrite_for_job(_sample_profile(), _sample_job(), score=80, client=MockClient())
    assert application.score == 80
    assert len(application.cover_letter) == 300


def test_rewrite_for_job_wraps_llm_error():
    """An LLMError from the client is surfaced as RewriterError."""
    class FailingClient:
        def complete(self, system, user, response_format_json=False):
            raise LLMError("rate limited")

    with pytest.raises(RewriterError, match="LLM call failed"):
        rewrite_for_job(_sample_profile(), _sample_job(), score=80, client=FailingClient())
