"""Tests for the output writer tool.

The sanitisation function gets the most thorough coverage because it
is the highest-risk pure-Python function in the project. Bad
sanitisation either crashes on the file system or silently overwrites
a previous user's output.
"""

from pathlib import Path

import pytest
from docx import Document

from job_agent.models import Application, Job
from job_agent.tools.output_writer import (
    APPLY_LINK_FILENAME,
    COVER_LETTER_FILENAME,
    CV_FILENAME,
    JOB_SUMMARY_FILENAME,
    OutputWriterError,
    create_job_folder,
    sanitize_job_title,
    write_application,
)


# ---------- sanitize_job_title ----------


@pytest.mark.parametrize(
    "raw_title, raw_company, expected",
    [
        # Plain ASCII case.
        ("Data Analyst", "Acme", "Data_Analyst_Acme"),
        # Slashes and at-signs.
        ("Data Analyst @ Google", "", "Data_Analyst_Google"),
        # Gender marker (m/f/d).
        ("Data Analyst (m/f/d)", "Acme", "Data_Analyst_Acme"),
        # Gender marker without parens.
        ("Data Analyst m/w/d", "Acme", "Data_Analyst_Acme"),
        # Accented characters get folded to ASCII.
        ("Müller Engineer", "Köln GmbH", "Muller_Engineer_Koln_GmbH"),
        # Emoji is stripped.
        ("Senior Engineer 🚀", "Acme", "Senior_Engineer_Acme"),
        # Multiple consecutive separators collapse.
        ("Data    Analyst!!!", "Acme", "Data_Analyst_Acme"),
        # Leading and trailing punctuation is trimmed.
        ("---Data Analyst---", "", "Data_Analyst"),
    ],
)
def test_sanitize_job_title_handles_common_cases(raw_title, raw_company, expected):
    """Common real-world job titles produce predictable folder names."""
    assert sanitize_job_title(raw_title, raw_company) == expected


def test_sanitize_job_title_truncates_long_input():
    """A title longer than the limit is truncated cleanly."""
    long_title = "A" * 200
    result = sanitize_job_title(long_title)
    assert len(result) <= 80
    assert "A" in result


def test_sanitize_job_title_falls_back_for_empty_input():
    """Pure-garbage input that sanitises to nothing returns a fallback."""
    assert sanitize_job_title("***///") == "Untitled_Job"
    assert sanitize_job_title("") == "Untitled_Job"


# ---------- create_job_folder ----------


def test_create_job_folder_creates_new_folder(tmp_path: Path):
    """Creating a folder that does not exist returns the new path."""
    folder = create_job_folder(tmp_path, "Data_Analyst_Acme")
    assert folder.exists()
    assert folder.is_dir()
    assert folder.name == "Data_Analyst_Acme"


def test_create_job_folder_suffixes_on_collision(tmp_path: Path):
    """If the folder exists, a numeric suffix is appended."""
    first = create_job_folder(tmp_path, "Data_Analyst_Acme")
    second = create_job_folder(tmp_path, "Data_Analyst_Acme")
    third = create_job_folder(tmp_path, "Data_Analyst_Acme")

    assert first.name == "Data_Analyst_Acme"
    assert second.name == "Data_Analyst_Acme_2"
    assert third.name == "Data_Analyst_Acme_3"


# ---------- write_application ----------


def _make_application() -> Application:
    """Helper to build a complete Application for tests."""
    job = Job(
        title="Junior Data Analyst (m/f/d)",
        company="Acme",
        location="Berlin",
        description="We are looking for...",
        apply_url="https://example.com/apply/123",
    )
    return Application(
        job=job,
        score=78,
        tailored_cv="Jane Doe\n\nExperience\n\nAcme intern, 2023",
        cover_letter="Dear Hiring Manager,\n\nI am writing to apply...",
        job_summary="Junior Data Analyst at Acme, Berlin. Python and SQL.",
    )


def test_write_application_creates_all_four_files(tmp_path: Path):
    """A successful write produces the expected file layout."""
    app = _make_application()
    folder = write_application(app, tmp_path)

    assert (folder / CV_FILENAME).exists()
    assert (folder / COVER_LETTER_FILENAME).exists()
    assert (folder / JOB_SUMMARY_FILENAME).exists()
    assert (folder / APPLY_LINK_FILENAME).exists()


def test_write_application_apply_link_contents_match(tmp_path: Path):
    """The apply_here.txt contains the URL the user can click."""
    app = _make_application()
    folder = write_application(app, tmp_path)

    link_text = (folder / APPLY_LINK_FILENAME).read_text(encoding="utf-8").strip()
    assert link_text == "https://example.com/apply/123"


def test_write_application_cv_docx_is_readable(tmp_path: Path):
    """The CV docx round-trips: writing then reading recovers the text."""
    app = _make_application()
    folder = write_application(app, tmp_path)

    doc = Document(str(folder / CV_FILENAME))
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    assert "Jane Doe" in full_text
    assert "Acme intern" in full_text


def test_write_application_job_summary_is_utf8(tmp_path: Path):
    """The summary file is UTF-8 and contains the summary text."""
    app = _make_application()
    folder = write_application(app, tmp_path)

    summary = (folder / JOB_SUMMARY_FILENAME).read_text(encoding="utf-8")
    assert "Junior Data Analyst at Acme" in summary


def test_write_application_does_not_overwrite_existing_folder(tmp_path: Path):
    """Two writes for the same job produce two separate folders."""
    app = _make_application()
    first = write_application(app, tmp_path)
    second = write_application(app, tmp_path)

    assert first != second
    assert first.exists()
    assert second.exists()
