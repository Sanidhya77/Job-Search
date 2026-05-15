"""Tailored CV and cover letter rewriter using GPT-4o-mini.

Takes a UserProfile and a matched Job and produces an Application
containing tailored CV text, a cover letter, and a short job summary.
The system prompt explicitly forbids inventing skills, technologies,
or numbers not present in the source CV.

The LLM call is delegated to LLMClient. This module is responsible
for formatting the input message, parsing the JSON response, and
validating that all three output fields are present and non-empty.
"""

import json

from job_agent.llm.client import LLMClient, LLMError
from job_agent.llm.prompts import REWRITER_PROMPT
from job_agent.models import Application, Job, UserProfile


class RewriterError(Exception):
    """Raised when rewriting fails for any reason."""


# Minimum acceptable lengths. The LLM occasionally returns truncated or
# one-line outputs when the input is sparse, and that produces a worse
# user experience than failing loudly.
MIN_CV_LENGTH = 100
MIN_COVER_LETTER_LENGTH = 200
MIN_SUMMARY_LENGTH = 30


def rewrite_for_job(
    profile: UserProfile,
    job: Job,
    score: int,
    client: LLMClient,
) -> Application:
    """Produce a tailored Application package for one matched job.

    Args:
        profile: The candidate's UserProfile, including raw_cv_text.
        job: The matched Job that passed the relevance threshold.
        score: The relevance score from the scorer step, recorded on
            the Application so the output writer can include it in
            the per-job folder name or summary file if desired.
        client: An LLMClient instance for the API call.

    Returns:
        An Application dataclass with tailored_cv, cover_letter, and
        job_summary, ready for the output writer to serialise to disk.

    Raises:
        RewriterError: If the LLM call fails or the response is malformed.
    """
    if not profile.raw_cv_text or not profile.raw_cv_text.strip():
        raise RewriterError(
            "UserProfile.raw_cv_text is empty; cannot rewrite without source."
        )

    user_message = build_rewriter_message(profile, job)

    try:
        raw_response = client.complete(
            system=REWRITER_PROMPT,
            user=user_message,
            response_format_json=True,
        )
    except LLMError as exc:
        raise RewriterError(f"LLM call failed during rewriting: {exc}") from exc

    return parse_rewriter_response(raw_response, job, score)


def build_rewriter_message(profile: UserProfile, job: Job) -> str:
    """Format the profile and job into the LLM's user message.

    The rewriter needs the full CV text (not just the extracted profile)
    because rephrasing bullet points requires access to the original
    wording. The job description is included verbatim so the model can
    reference specific requirements.
    """
    return (
        f"CANDIDATE CV (full text):\n"
        f"{profile.raw_cv_text}\n\n"
        f"---\n\n"
        f"TARGET JOB:\n"
        f"Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Location: {job.location}\n"
        f"Description:\n{job.description}"
    )


def parse_rewriter_response(raw_response: str, job: Job, score: int) -> Application:
    """Parse the LLM's JSON response into an Application.

    Split out so tests can hit it directly with synthetic JSON strings.
    Validates that all three fields are present, non-empty, and meet
    the minimum length thresholds so we do not write a one-line cover
    letter to disk and call it done.
    """
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise RewriterError(f"LLM response is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise RewriterError(
            f"LLM response is not a JSON object, got {type(data).__name__}."
        )

    tailored_cv = _validate_field(data, "tailored_cv", MIN_CV_LENGTH)
    cover_letter = _validate_field(data, "cover_letter", MIN_COVER_LETTER_LENGTH)
    job_summary = _validate_field(data, "job_summary", MIN_SUMMARY_LENGTH)

    return Application(
        job=job,
        score=score,
        tailored_cv=tailored_cv,
        cover_letter=cover_letter,
        job_summary=job_summary,
    )


def _validate_field(data: dict, field: str, min_length: int) -> str:
    """Confirm a field is a non-empty string above the minimum length."""
    if field not in data:
        raise RewriterError(f"LLM response missing '{field}' field.")

    value = data[field]
    if not isinstance(value, str):
        raise RewriterError(
            f"'{field}' must be a string, got {type(value).__name__}."
        )

    stripped = value.strip()
    if not stripped:
        raise RewriterError(f"'{field}' is empty.")

    if len(stripped) < min_length:
        raise RewriterError(
            f"'{field}' is too short ({len(stripped)} chars, "
            f"minimum {min_length}). The LLM likely truncated."
        )

    return stripped
