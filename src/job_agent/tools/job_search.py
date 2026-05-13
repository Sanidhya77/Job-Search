"""Job search tool, SerpApi (Google Jobs engine).

Takes a query string built from the user's brief, calls SerpApi, and
returns a list of Job dataclasses for the agent to score and filter.

This is a deterministic tool, not an LLM step. The LLM never sees the
raw SerpApi response; it only sees the Job objects this tool produces.
Keeping the network call here means the rest of the system can be
tested without any internet access by replacing this tool with mocked
fixture data.
"""

import json
from pathlib import Path
from typing import Optional

from serpapi import GoogleSearch

from job_agent.models import Job


# Default number of jobs to fetch per query. SerpApi's Google Jobs
# engine typically returns about 10 results per page; we keep the
# default modest to stay well inside the free tier of 100 searches
# per month during development.
DEFAULT_RESULT_COUNT = 10


class JobSearchError(Exception):
    """Raised when the job search cannot complete for any reason.

    A single exception type means the agent's main loop handles one
    thing per tool, rather than branching on every underlying
    SerpApi or HTTP error.
    """


def search_jobs(
    query: str,
    api_key: str,
    result_count: int = DEFAULT_RESULT_COUNT,
) -> list[Job]:
    """Search for jobs matching the query and return parsed Job objects.

    Args:
        query: Natural-language search string, e.g. "Python Developer Berlin".
        api_key: SerpApi key, normally loaded from .env via Config.
        result_count: How many results to request. Default 10.

    Returns:
        A list of Job dataclasses. May be empty if SerpApi finds nothing.

    Raises:
        JobSearchError: If the query is empty, the request fails, or
            the response is malformed.
    """
    if not query or not query.strip():
        raise JobSearchError("Search query is empty.")

    params = {
        "engine": "google_jobs",
        "q": query.strip(),
        "api_key": api_key,
        "num": result_count,
    }

    try:
        search = GoogleSearch(params)
        response = search.get_dict()
    except Exception as exc:
        raise JobSearchError(f"SerpApi request failed: {exc}") from exc

    return parse_response(response)


def parse_response(response: dict) -> list[Job]:
    """Convert a SerpApi response dict into a list of Job objects.

    The conversion is its own function (rather than inline in
    search_jobs) so it can be tested against saved fixture files
    without making any network calls.

    The SerpApi Google Jobs response uses the key "jobs_results" for
    the list of listings, with each listing carrying its own nested
    structure. Some fields may be missing on individual listings, so
    each is read with a default to keep the parser tolerant.
    """
    if response.get("error"):
        raise JobSearchError(f"SerpApi returned an error: {response['error']}")

    listings = response.get("jobs_results", [])
    if not isinstance(listings, list):
        raise JobSearchError(
            f"Unexpected response shape: jobs_results is "
            f"{type(listings).__name__}, not list."
        )

    jobs: list[Job] = []
    for raw in listings:
        jobs.append(_listing_to_job(raw))

    return jobs


def _listing_to_job(raw: dict) -> Job:
    """Map one SerpApi listing dict to a Job dataclass.

    SerpApi sometimes returns the apply link nested under
    apply_options, sometimes as share_link, and sometimes as a
    direct URL on related_links. We prefer apply_options[0]["link"]
    when present and fall back through the alternatives. If nothing
    is available we return an empty string rather than None so the
    output writer downstream does not have to handle a missing URL
    as a special case.
    """
    apply_url = ""
    apply_options = raw.get("apply_options") or []
    if apply_options and isinstance(apply_options, list):
        apply_url = apply_options[0].get("link", "") or ""
    if not apply_url:
        apply_url = raw.get("share_link", "") or ""
    if not apply_url:
        related = raw.get("related_links") or []
        if related and isinstance(related, list):
            apply_url = related[0].get("link", "") or ""

    return Job(
        title=raw.get("title", "").strip(),
        company=raw.get("company_name", "").strip(),
        location=raw.get("location", "").strip(),
        description=raw.get("description", "").strip(),
        apply_url=apply_url,
        source="serpapi",
    )


def load_fixture_response(path: Path) -> dict:
    """Load a saved SerpApi JSON response from disk.

    Used by tests to replay a captured real response without making
    a network call. Kept in the production module (not test code) so
    the loader is the same code path the tests exercise.
    """
    path = Path(path)
    if not path.exists():
        raise JobSearchError(f"Fixture file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
