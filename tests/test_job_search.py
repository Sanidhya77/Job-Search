"""Tests for the SerpApi job search tool.

All tests run offline. The real API was called exactly once to
capture tests/fixtures/sample_serpapi_response.json. From that point
on every test replays the saved response, which keeps the test suite
fast, free, and deterministic.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from job_agent.models import Job
from job_agent.tools.job_search import (
    JobSearchError,
    _listing_to_job,
    load_fixture_response,
    parse_response,
    search_jobs,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_serpapi_response.json"


# ---------- parse_response ----------


def test_parse_response_with_real_fixture_returns_jobs():
    """Parsing the captured real SerpApi response yields Job objects."""
    response = load_fixture_response(FIXTURE_PATH)
    jobs = parse_response(response)

    assert isinstance(jobs, list)
    assert len(jobs) > 0, "Fixture should contain at least one listing."
    for job in jobs:
        assert isinstance(job, Job)
        assert job.source == "serpapi"


def test_parse_response_extracts_expected_fields():
    """Each parsed Job has non-empty core fields where the source provided them."""
    response = load_fixture_response(FIXTURE_PATH)
    jobs = parse_response(response)

    # At least one job should have a usable title and company.
    usable = [j for j in jobs if j.title and j.company]
    assert len(usable) > 0, "Fixture should contain at least one fully populated job."


def test_parse_response_handles_empty_results():
    """A response with no jobs_results returns an empty list, not an error."""
    assert parse_response({}) == []
    assert parse_response({"jobs_results": []}) == []


def test_parse_response_raises_on_api_error():
    """A response carrying an error field is surfaced as JobSearchError."""
    response = {"error": "Invalid API key"}
    with pytest.raises(JobSearchError, match="Invalid API key"):
        parse_response(response)


def test_parse_response_raises_on_malformed_shape():
    """If jobs_results is not a list, parsing fails clearly."""
    response = {"jobs_results": "this should be a list"}
    with pytest.raises(JobSearchError, match="Unexpected response shape"):
        parse_response(response)


# ---------- _listing_to_job ----------


def test_listing_to_job_with_apply_options():
    """When apply_options is present, the first link is used as apply_url."""
    raw = {
        "title": "Data Analyst",
        "company_name": "Acme",
        "location": "Berlin",
        "description": "Looking for an analyst...",
        "apply_options": [{"link": "https://example.com/apply/1"}],
    }
    job = _listing_to_job(raw)
    assert job.apply_url == "https://example.com/apply/1"
    assert job.title == "Data Analyst"
    assert job.company == "Acme"


def test_listing_to_job_falls_back_to_share_link():
    """When apply_options is missing, share_link is used."""
    raw = {
        "title": "Data Analyst",
        "company_name": "Acme",
        "share_link": "https://example.com/share/2",
    }
    job = _listing_to_job(raw)
    assert job.apply_url == "https://example.com/share/2"


def test_listing_to_job_returns_empty_string_when_no_url():
    """A listing with no URL fields returns an empty apply_url (not None)."""
    raw = {"title": "Data Analyst", "company_name": "Acme"}
    job = _listing_to_job(raw)
    assert job.apply_url == ""


def test_listing_to_job_strips_whitespace():
    """Title, company, and location are stripped of leading and trailing spaces."""
    raw = {
        "title": "  Data Analyst  ",
        "company_name": "  Acme  ",
        "location": "  Berlin  ",
    }
    job = _listing_to_job(raw)
    assert job.title == "Data Analyst"
    assert job.company == "Acme"
    assert job.location == "Berlin"


# ---------- search_jobs (with mocked network) ----------


def test_search_jobs_rejects_empty_query():
    """An empty or whitespace-only query is rejected before any API call."""
    with pytest.raises(JobSearchError, match="empty"):
        search_jobs("", api_key="test-key")
    with pytest.raises(JobSearchError, match="empty"):
        search_jobs("   ", api_key="test-key")


def test_search_jobs_uses_fixture_when_network_mocked():
    """search_jobs returns Job objects when the SerpApi client is mocked."""
    fixture_response = load_fixture_response(FIXTURE_PATH)

    with patch("job_agent.tools.job_search.GoogleSearch") as mock_search:
        mock_search.return_value.get_dict.return_value = fixture_response

        jobs = search_jobs("Python Developer Berlin", api_key="test-key")

    assert isinstance(jobs, list)
    assert len(jobs) > 0
    assert all(isinstance(j, Job) for j in jobs)


def test_search_jobs_wraps_underlying_failure():
    """A failure inside the SerpApi client is wrapped in JobSearchError."""
    with patch("job_agent.tools.job_search.GoogleSearch") as mock_search:
        mock_search.return_value.get_dict.side_effect = RuntimeError("network down")

        with pytest.raises(JobSearchError, match="SerpApi request failed"):
            search_jobs("Python Developer Berlin", api_key="test-key")


def test_load_fixture_response_raises_on_missing_file(tmp_path: Path):
    """The fixture loader gives a clear error if the file does not exist."""
    missing = tmp_path / "no_such_fixture.json"
    with pytest.raises(JobSearchError, match="Fixture file not found"):
        load_fixture_response(missing)
