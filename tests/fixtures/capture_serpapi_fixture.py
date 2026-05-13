"""One-shot script to capture a real SerpApi response as a test fixture.

Run this exactly once after setting up your SerpApi key in .env. The
saved file at tests/fixtures/sample_serpapi_response.json is then used
by every test in this module, so no test ever makes a real API call.

Usage:
    python tests/fixtures/capture_serpapi_fixture.py

The script intentionally lives outside of test code so it is never run
as part of pytest. Test runs do not need a real API key.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from serpapi import GoogleSearch


FIXTURE_PATH = Path(__file__).parent / "sample_serpapi_response.json"
SAMPLE_QUERY = "Python Developer New York"


def main() -> None:
    load_dotenv()
    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key:
        print("ERROR: SERPAPI_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    params = {
        "engine": "google_jobs",
        "q": SAMPLE_QUERY,
        "api_key": api_key,
        "num": 10,
    }

    print(f"Querying SerpApi for: {SAMPLE_QUERY!r} ...")
    search = GoogleSearch(params)
    response = search.get_dict()

    # Strip the API key from the saved response if SerpApi echoed it
    # back in search_parameters, so it never lands in version control.
    if "search_parameters" in response and "api_key" in response["search_parameters"]:
        response["search_parameters"]["api_key"] = "REDACTED"

    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        json.dump(response, f, indent=2, ensure_ascii=False)

    job_count = len(response.get("jobs_results", []))
    print(f"Saved fixture to {FIXTURE_PATH}")
    print(f"Contains {job_count} job listings.")


if __name__ == "__main__":
    main()
