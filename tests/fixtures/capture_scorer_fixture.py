"""One-shot script to capture a real OpenAI scorer response as a fixture.

Reads the CV analysis fixture from Day 6 (so the candidate profile is
consistent across the test suite), takes a job from the SerpApi
fixture, sends both to the scorer, and saves the result.

Usage:
    python tests/fixtures/capture_scorer_fixture.py
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from job_agent.llm.client import LLMClient
from job_agent.llm.scorer import build_scorer_message, parse_scorer_response, SCORER_PROMPT
from job_agent.models import Job, UserProfile


FIXTURE_DIR = Path(__file__).parent
CV_FIXTURE = FIXTURE_DIR / "sample_cv_analysis_response.json"
JOB_FIXTURE = FIXTURE_DIR / "sample_serpapi_response.json"
OUTPUT_FIXTURE = FIXTURE_DIR / "sample_scorer_response.json"


def _build_profile_from_cv_fixture() -> UserProfile:
    """Recover a UserProfile from the saved CV analyser fixture."""
    with open(CV_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    parsed = data["parsed"]
    return UserProfile(
        full_name=parsed["full_name"],
        skills=parsed.get("skills", []),
        years_of_experience=float(parsed.get("years_of_experience", 0)),
        seniority=parsed.get("seniority", "junior"),
        domains=parsed.get("domains", []),
        languages=parsed.get("languages", []),
        location_preference=parsed.get("location_preference"),
        remote_preference=parsed.get("remote_preference"),
        raw_cv_text="(omitted in fixture; not needed by scorer)",
    )


def _pick_job_from_serpapi_fixture() -> Job:
    """Pick the first non-empty job from the SerpApi fixture."""
    with open(JOB_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for raw in data.get("jobs_results", []):
        if raw.get("title") and raw.get("description"):
            return Job(
                title=raw["title"],
                company=raw.get("company_name", "Unknown"),
                location=raw.get("location", ""),
                description=raw["description"],
                apply_url="https://example.com",
                source="serpapi",
            )
    raise RuntimeError("No usable job in SerpApi fixture.")


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    if not CV_FIXTURE.exists():
        print(f"ERROR: CV fixture missing: {CV_FIXTURE}", file=sys.stderr)
        print("Run capture_openai_fixture.py first (Day 6).", file=sys.stderr)
        sys.exit(1)
    if not JOB_FIXTURE.exists():
        print(f"ERROR: SerpApi fixture missing: {JOB_FIXTURE}", file=sys.stderr)
        print("Run capture_serpapi_fixture.py first (Day 5).", file=sys.stderr)
        sys.exit(1)

    profile = _build_profile_from_cv_fixture()
    job = _pick_job_from_serpapi_fixture()

    print(f"Profile: {profile.full_name}, seniority={profile.seniority}")
    print(f"Job: {job.title} @ {job.company}")
    print("Calling OpenAI scorer (gpt-4o-mini, response_format=json) ...")

    client = LLMClient(api_key=api_key)
    user_message = build_scorer_message(profile, job)
    raw_response = client.complete(
        system=SCORER_PROMPT,
        user=user_message,
        response_format_json=True,
    )

    # Validate it parses.
    scored = parse_scorer_response(raw_response, job)

    with open(OUTPUT_FIXTURE, "w", encoding="utf-8") as f:
        json.dump({
            "raw_response": raw_response,
            "parsed_score": scored.score,
            "parsed_reasoning": scored.reasoning,
            "job_title_used": job.title,
            "job_company_used": job.company,
        }, f, indent=2, ensure_ascii=False)

    print(f"Saved fixture to {OUTPUT_FIXTURE}")
    print(f"Score: {scored.score}")
    print(f"Reasoning: {scored.reasoning}")


if __name__ == "__main__":
    main()
