"""Shared pytest fixtures.

Centralising fixtures here means every test module can use the same
sample data, and there is one place to update if the fixture format
changes. The actual fixture files live in tests/fixtures/.
"""

from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the directory holding sample input files."""
    return FIXTURES_DIR


@pytest.fixture
def sample_pdf_path(fixtures_dir: Path) -> Path:
    """Path to a small valid PDF CV used in tests."""
    return fixtures_dir / "sample_cv.pdf"


@pytest.fixture
def sample_docx_path(fixtures_dir: Path) -> Path:
    """Path to a small valid DOCX CV used in tests."""
    return fixtures_dir / "sample_cv.docx"
