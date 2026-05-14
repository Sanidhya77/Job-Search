"""One-shot script to capture a real OpenAI response as a test fixture.

Run this exactly once after Day 6 code is in place. The script reads
a CV from a path the user provides, calls the LLMClient with the
CV_ANALYSER_PROMPT, and saves the response at
tests/fixtures/sample_cv_analysis_response.json so tests can replay
it offline.

Usage:
    python tests/fixtures/capture_openai_fixture.py path/to/your_cv.pdf

The script lives outside test code so pytest never runs it.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from job_agent.llm.client import LLMClient
from job_agent.llm.prompts import CV_ANALYSER_PROMPT
from job_agent.tools.cv_reader import read_cv


FIXTURE_PATH = Path(__file__).parent / "sample_cv_analysis_response.json"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python tests/fixtures/capture_openai_fixture.py <cv_path>", file=sys.stderr)
        sys.exit(1)

    cv_path = Path(sys.argv[1])
    if not cv_path.exists():
        print(f"ERROR: CV file not found: {cv_path}", file=sys.stderr)
        sys.exit(1)

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    print(f"Reading CV from {cv_path} ...")
    cv_text = read_cv(cv_path)
    print(f"CV is {len(cv_text)} characters.")

    print("Calling OpenAI (gpt-4o-mini, response_format=json) ...")
    client = LLMClient(api_key=api_key)
    response = client.complete(
        system=CV_ANALYSER_PROMPT,
        user=cv_text,
        response_format_json=True,
    )

    # Validate it parses as JSON before saving.
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Response is not valid JSON: {exc}", file=sys.stderr)
        print(f"Raw response was:\n{response}", file=sys.stderr)
        sys.exit(1)

    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        json.dump({"raw_response": response, "parsed": parsed}, f, indent=2, ensure_ascii=False)

    # Also save a copy with the original CV's name
    named_fixture_path = FIXTURE_PATH.parent / f"{cv_path.stem}_analysis.json"
    with open(named_fixture_path, "w", encoding="utf-8") as f:
        json.dump({"raw_response": response, "parsed": parsed}, f, indent=2, ensure_ascii=False)

    print(f"Saved test fixture to {FIXTURE_PATH.name}")
    print(f"Saved named copy to {named_fixture_path.name}")
    print(f"Detected name: {parsed.get('full_name')}")
    print(f"Detected seniority: {parsed.get('seniority')}")
    print(f"Detected skills count: {len(parsed.get('skills', []))}")


if __name__ == "__main__":
    main()
