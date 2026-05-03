"""Generate the sample CV fixtures.

Run this script once after cloning to (re)create the fixture files
used by tests/test_cv_reader.py. The fixtures themselves are checked
into the repo so tests work without running this script first; it
exists so the fixtures are reproducible if they ever need to change.

Usage:
    python tests/fixtures/generate_fixtures.py
"""

from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


FIXTURES_DIR = Path(__file__).parent


CV_LINES = [
    "Jane Doe",
    "Junior Data Analyst",
    "Berlin, Germany",
    "",
    "Skills",
    "Python, SQL, pandas, basic statistics",
    "",
    "Experience",
    "Acme Corp - Data Analyst Intern (2023-2024)",
    "Built reporting dashboards in Python and SQL.",
    "",
    "Education",
    "BSc Computer Science, Riga Technical University, 2024",
]


def build_pdf(path: Path) -> None:
    """Write the sample CV as a single-page PDF."""
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica", 11)
    y = 800
    for line in CV_LINES:
        c.drawString(72, y, line)
        y -= 18
    c.save()


def build_docx(path: Path) -> None:
    """Write the sample CV as a DOCX file."""
    doc = Document()
    for line in CV_LINES:
        doc.add_paragraph(line)
    doc.save(str(path))


def main() -> None:
    build_pdf(FIXTURES_DIR / "sample_cv.pdf")
    build_docx(FIXTURES_DIR / "sample_cv.docx")
    print(f"Fixtures written to {FIXTURES_DIR}")


if __name__ == "__main__":
    main()
