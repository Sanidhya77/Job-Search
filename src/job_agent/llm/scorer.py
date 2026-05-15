"""Job-to-profile scorer using GPT-4o-mini.

Takes a UserProfile and a single Job and returns a ScoredJob with a
numeric score (0-100) and a one-sentence justification. The scorer's
system prompt names three explicit criteria so the LLM's output is
reproducible across runs: skill overlap, seniority match, and hard
blockers.

The LLM call is delegated to LLMClient. This module is responsible
for formatting the input message, parsing the JSON response, and
validating that the score is in range.
"""

import json

from job_agent.llm.client import LLMClient, LLMError
from job_agent.llm.prompts import SCORER_PROMPT
from job_agent.models import Job, ScoredJob, UserProfile


class ScorerError(Exception):
    """Raised when scoring fails for any reason."""


def score_job(
    profile: UserProfile,
    job: Job,
    client: LLMClient,
) -> ScoredJob:
    """Score one job against the user's profile.

    Args:
        profile: The candidate's UserProfile from the cv_analyzer step.
        job: A single Job from the search results.
        client: An LLMClient instance for the API call.

    Returns:
        A ScoredJob with score 0-100 and a one-sentence reasoning.

    Raises:
        ScorerError: If the LLM call fails or the response is malformed.
    """
    user_message = build_scorer_message(profile, job)

    try:
        raw_response = client.complete(
            system=SCORER_PROMPT,
            user=user_message,
            response_format_json=True,
        )
    except LLMError as exc:
        raise ScorerError(f"LLM call failed during scoring: {exc}") from exc

    return parse_scorer_response(raw_response, job)


def build_scorer_message(profile: UserProfile, job: Job) -> str:
    """Format the profile and job into the LLM's user message.

    Pulled out as a public function so tests can verify the formatting
    contract independently of any LLM call. The format is plain text
    with labelled sections, which is more robust to model drift than
    pasting raw JSON of the profile.
    """
    return (
        f"CANDIDATE PROFILE:\n"
        f"Name: {profile.full_name}\n"
        f"Skills: {', '.join(profile.skills) if profile.skills else 'none listed'}\n"
        f"Years of experience: {profile.years_of_experience}\n"
        f"Seniority: {profile.seniority}\n"
        f"Domains: {', '.join(profile.domains) if profile.domains else 'none listed'}\n"
        f"Languages: {', '.join(profile.languages) if profile.languages else 'none listed'}\n"
        f"Location preference: {profile.location_preference or 'any'}\n"
        f"Remote preference: {profile.remote_preference or 'any'}\n\n"
        f"JOB LISTING:\n"
        f"Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Location: {job.location}\n"
        f"Description:\n{job.description}"
    )


def parse_scorer_response(raw_response: str, job: Job) -> ScoredJob:
    """Parse the LLM's JSON response into a ScoredJob.

    Split out so tests can hit it directly with synthetic JSON strings.
    Validates that score is an int in [0, 100] and reasoning is a
    non-empty string.
    """
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ScorerError(f"LLM response is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ScorerError(
            f"LLM response is not a JSON object, got {type(data).__name__}."
        )

    if "score" not in data:
        raise ScorerError("LLM response missing 'score' field.")
    if "reasoning" not in data:
        raise ScorerError("LLM response missing 'reasoning' field.")

    try:
        score = int(data["score"])
    except (TypeError, ValueError) as exc:
        raise ScorerError(
            f"score is not an integer: {data['score']!r}"
        ) from exc

    if not 0 <= score <= 100:
        raise ScorerError(f"score out of range 0-100: {score}")

    reasoning = data["reasoning"]
    if not isinstance(reasoning, str) or not reasoning.strip():
        raise ScorerError("reasoning must be a non-empty string.")

    return ScoredJob(job=job, score=score, reasoning=reasoning.strip())
