"""Tests for the CV reader tool."""

from pathlib import Path

import pytest

from job_agent.tools.cv_reader import CVReaderError, read_cv


def test_read_pdf_returns_non_empty_text(sample_pdf_path: Path):
    """Reading the sample PDF returns text that includes known content."""
    text = read_cv(sample_pdf_path)
    assert isinstance(text, str)
    assert len(text) > 0
    # The fixture PDF contains the candidate's name; if extraction
    # works at all this should be present.
    assert "Jane Doe" in text


def test_read_docx_returns_non_empty_text(sample_docx_path: Path):
    """Reading the sample DOCX returns text that includes known content."""
    text = read_cv(sample_docx_path)
    assert isinstance(text, str)
    assert len(text) > 0
    assert "Jane Doe" in text


def test_read_cv_raises_on_missing_file(tmp_path: Path):
    """A non-existent path produces a clear CVReaderError."""
    missing = tmp_path / "does_not_exist.pdf"
    with pytest.raises(CVReaderError, match="not found"):
        read_cv(missing)


def test_read_cv_raises_on_directory(tmp_path: Path):
    """A directory passed instead of a file is rejected."""
    with pytest.raises(CVReaderError, match="not a file"):
        read_cv(tmp_path)


def test_read_cv_raises_on_unsupported_extension(tmp_path: Path):
    """An unsupported extension is rejected before any parsing happens."""
    unsupported = tmp_path / "cv.txt"
    unsupported.write_text("Plain text CV", encoding="utf-8")
    with pytest.raises(CVReaderError, match="Unsupported CV format"):
        read_cv(unsupported)


def test_read_cv_raises_on_corrupted_pdf(tmp_path: Path):
    """A file with .pdf extension that is not actually a PDF is rejected."""
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"this is not a pdf")
    with pytest.raises(CVReaderError, match="Failed to parse"):
        read_cv(fake_pdf)


def test_read_cv_accepts_string_path(sample_pdf_path: Path):
    """The reader accepts both Path and str inputs."""
    text = read_cv(str(sample_pdf_path))
    assert "Jane Doe" in text
