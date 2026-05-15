"""One-shot script to capture a real OpenAI rewriter response as a fixture.

Loads the CV analyser fixture (Day 6) and picks a job from the SerpApi
fixture (Day 5), then calls the rewriter and saves the result. The
saved fixture is what tests replay.

Usage:
    python tests/fixtures/capture_rewriter_fixture.py
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from job_agent.llm.client import LLMClient
from job_agent.llm.prompts import REWRITER_PROMPT
from job_agent.llm.rewriter import (
    build_rewriter_message,
    parse_rewriter_response,
)
from job_agent.models import Job, UserProfile


FIXTURE_DIR = Path(__file__).parent
CV_FIXTURE = FIXTURE_DIR / "sample_cv_analysis_response.json"
JOB_FIXTURE = FIXTURE_DIR / "sample_serpapi_response.json"
OUTPUT_FIXTURE = FIXTURE_DIR / "sample_rewriter_response.json"


# We need the raw CV text on the UserProfile for the rewriter to work
# properly. The CV analyser fixture does not store the original CV text
# (we did not need it there), so we ask the user to provide the path
# again so we can re-read it.
CV_PATH_PROMPT = (
    "Enter the path to the CV you used for the Day 6 capture "
    "(needs to be readable again): "
)


def _build_profile() -> UserProfile:
    """Rebuild a UserProfile from the CV analyser fixture plus raw CV text."""
    from job_agent.tools.cv_reader import read_cv

    cv_path_str = input(CV_PATH_PROMPT).strip()
    cv_path = Path(cv_path_str)
    if not cv_path.exists():
        print(f"ERROR: CV file not found: {cv_path}", file=sys.stderr)
        sys.exit(1)
    raw_cv_text = read_cv(cv_path)

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
        raw_cv_text=raw_cv_text,
    )


def _pick_job() -> Job:
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

    if not CV_FIXTURE.exists() or not JOB_FIXTURE.exists():
        print("ERROR: Earlier fixtures missing. Run Day 5 and Day 6 captures first.",
              file=sys.stderr)
        sys.exit(1)

    profile = _build_profile()
    job = _pick_job()

    print(f"\nProfile: {profile.full_name}")
    print(f"Job: {job.title} @ {job.company}")
    print("\nCalling OpenAI rewriter (gpt-4o-mini, response_format=json) ...")
    print("This may take 10-20 seconds.\n")

    client = LLMClient(api_key=api_key)
    user_message = build_rewriter_message(profile, job)
    raw_response = client.complete(
        system=REWRITER_PROMPT,
        user=user_message,
        response_format_json=True,
    )

    # Validate it parses (using score=80 just as a placeholder).
    application = parse_rewriter_response(raw_response, job, score=80)

    with open(OUTPUT_FIXTURE, "w", encoding="utf-8") as f:
        json.dump({
            "raw_response": raw_response,
            "job_title_used": job.title,
            "job_company_used": job.company,
            "parsed_cv_length": len(application.tailored_cv),
            "parsed_letter_length": len(application.cover_letter),
            "parsed_summary_length": len(application.job_summary),
        }, f, indent=2, ensure_ascii=False)

    print(f"\nSaved fixture to {OUTPUT_FIXTURE}")
    print(f"Tailored CV: {len(application.tailored_cv)} chars")
    print(f"Cover letter: {len(application.cover_letter)} chars")
    print(f"Summary: {len(application.job_summary)} chars\n")
    print("=" * 60)
    print("PREVIEW: First 500 chars of cover letter")
    print("=" * 60)
    print(application.cover_letter[:500])
    print("=" * 60)
    print("\nReview the cover letter above. If it sounds reasonable and does")
    print("not invent skills you do not have, you are done. Otherwise re-run.")


if __name__ == "__main__":
    main()
