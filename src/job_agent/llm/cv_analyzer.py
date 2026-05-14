"""CV analyser: extract a structured UserProfile from raw CV text.

Sends the CV text to GPT-4o-mini through the LLMClient wrapper, parses
the JSON response, and returns a UserProfile dataclass. The LLM never
sees raw file bytes; the cv_reader tool has already converted PDF or
DOCX to plain text.
"""

import json

from job_agent.llm.client import LLMClient, LLMError
from job_agent.llm.prompts import CV_ANALYSER_PROMPT
from job_agent.models import UserProfile


class CVAnalyzerError(Exception):
    """Raised when CV analysis fails for any reason."""


# Valid values for seniority. We validate against this set rather than
# trusting whatever the LLM returns, because the rest of the system
# (scorer prompts especially) will reason about these three categories.
VALID_SENIORITY = {"junior", "mid", "senior"}
VALID_REMOTE = {"remote", "hybrid", "onsite", None}


def analyse_cv(cv_text: str, client: LLMClient) -> UserProfile:
    """Convert raw CV text into a structured UserProfile.

    Args:
        cv_text: The normalised CV text from the cv_reader tool.
        client: An LLMClient instance for making the API call.

    Returns:
        A UserProfile dataclass populated from the LLM's structured output.
        The original cv_text is preserved on the UserProfile so the
        rewriter step later can work from the source rather than a
        lossy reconstruction.

    Raises:
        CVAnalyzerError: If the CV is empty, the LLM call fails, or the
            response cannot be parsed into a valid UserProfile.
    """
    if not cv_text or not cv_text.strip():
        raise CVAnalyzerError("CV text is empty.")

    try:
        raw_response = client.complete(
            system=CV_ANALYSER_PROMPT,
            user=cv_text,
            response_format_json=True,
        )
    except LLMError as exc:
        raise CVAnalyzerError(f"LLM call failed during CV analysis: {exc}") from exc

    return parse_analyser_response(raw_response, cv_text)


def parse_analyser_response(raw_response: str, cv_text: str) -> UserProfile:
    """Parse the LLM's JSON response into a UserProfile.

    Split out from analyse_cv so it can be tested against saved fixture
    responses without making any LLM calls.

    Args:
        raw_response: The JSON string returned by the LLM.
        cv_text: The original CV text to embed on the UserProfile.

    Returns:
        A populated UserProfile dataclass.

    Raises:
        CVAnalyzerError: If the response is not valid JSON or is missing
            required fields or contains invalid enum values.
    """
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise CVAnalyzerError(
            f"LLM response is not valid JSON: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise CVAnalyzerError(
            f"LLM response is not a JSON object, got {type(data).__name__}."
        )

    # full_name is the one field we genuinely require because identifying
    # the candidate is necessary for the cover letter step downstream.
    full_name = data.get("full_name", "").strip() if isinstance(data.get("full_name"), str) else ""
    if not full_name:
        raise CVAnalyzerError("LLM response missing full_name.")

    seniority = data.get("seniority", "junior")
    if seniority not in VALID_SENIORITY:
        raise CVAnalyzerError(
            f"Invalid seniority {seniority!r}. Must be one of {sorted(VALID_SENIORITY)}."
        )

    remote_preference = data.get("remote_preference")
    if remote_preference not in VALID_REMOTE:
        raise CVAnalyzerError(
            f"Invalid remote_preference {remote_preference!r}. "
            f"Must be one of remote/hybrid/onsite/null."
        )

    try:
        years = float(data.get("years_of_experience", 0))
    except (TypeError, ValueError) as exc:
        raise CVAnalyzerError(
            f"years_of_experience is not a number: {data.get('years_of_experience')!r}"
        ) from exc

    return UserProfile(
        full_name=full_name,
        skills=_as_string_list(data.get("skills")),
        years_of_experience=years,
        seniority=seniority,
        domains=_as_string_list(data.get("domains")),
        languages=_as_string_list(data.get("languages")),
        location_preference=_as_optional_string(data.get("location_preference")),
        remote_preference=remote_preference,
        raw_cv_text=cv_text,
    )


def _as_string_list(value) -> list[str]:
    """Defensive conversion: return [] for None or non-list inputs."""
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _as_optional_string(value) -> str | None:
    """Return a stripped non-empty string, or None."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped if stripped else None
