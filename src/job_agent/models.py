"""Domain models for the job application agent.

These dataclasses define the contracts between modules. The flow is:

    raw CV text  ->  UserProfile        (cv_analyzer)
    raw job JSON ->  Job                 (job_search)
    profile + job -> ScoredJob           (scorer)
    profile + job -> Application         (rewriter)

Keeping these as dataclasses (not dicts) means the contract is explicit
and type-checkable, which makes the data conversion story for Step 3
much easier to document.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UserProfile:
    """Structured representation of the user's CV.

    Built by the cv_analyzer LLM step from raw CV text. Every field
    here must be derivable from the source CV; nothing is invented.
    """

    full_name: str
    skills: list[str]
    years_of_experience: float
    seniority: str  # one of: "junior", "mid", "senior"
    domains: list[str]  # e.g. ["data analysis", "backend web"]
    languages: list[str] = field(default_factory=list)
    location_preference: Optional[str] = None
    remote_preference: Optional[str] = None  # "remote", "hybrid", "onsite", or None
    raw_cv_text: str = ""  # kept so the rewriter can rewrite from the original


@dataclass
class Job:
    """A job listing as returned by the search tool, normalised."""

    title: str
    company: str
    location: str
    description: str
    apply_url: str
    source: str = "serpapi"  # which tool produced this listing


@dataclass
class ScoredJob:
    """A job after the scorer has rated its alignment with the user."""

    job: Job
    score: int  # 0 to 100
    reasoning: str  # one-sentence justification from the LLM


@dataclass
class Application:
    """The full set of materials produced for one matched job."""

    job: Job
    score: int
    tailored_cv: str  # plain text, the writer converts to docx
    cover_letter: str  # plain text, the writer converts to docx
    job_summary: str  # short summary written to a .txt file
