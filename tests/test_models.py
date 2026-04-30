"""Tests for the domain models in src/job_agent/models.py."""

from job_agent.models import Application, Job, ScoredJob, UserProfile


def test_user_profile_with_required_fields():
    """A UserProfile can be created with only the required fields."""
    profile = UserProfile(
        full_name="Jane Doe",
        skills=["Python", "SQL"],
        years_of_experience=3.0,
        seniority="mid",
        domains=["data analysis"],
    )
    assert profile.full_name == "Jane Doe"
    assert profile.languages == []
    assert profile.location_preference is None


def test_job_holds_listing_data():
    """A Job stores the fields the search tool extracts."""
    job = Job(
        title="Junior Data Analyst",
        company="Acme",
        location="Berlin, Germany",
        description="We are looking for...",
        apply_url="https://example.com/apply/123",
    )
    assert job.source == "serpapi"


def test_scored_job_wraps_job_with_score():
    """A ScoredJob attaches a score and reasoning to a Job."""
    job = Job("T", "C", "L", "D", "U")
    scored = ScoredJob(job=job, score=78, reasoning="Strong skill overlap.")
    assert scored.score == 78
    assert scored.job.title == "T"


def test_application_holds_all_outputs():
    """An Application bundles everything the writer needs."""
    job = Job("T", "C", "L", "D", "U")
    app = Application(
        job=job,
        score=78,
        tailored_cv="cv text",
        cover_letter="letter text",
        job_summary="summary text",
    )
    assert app.score == 78
    assert app.tailored_cv == "cv text"
