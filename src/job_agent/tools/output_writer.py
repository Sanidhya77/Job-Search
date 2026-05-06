"""Output writer tool.

Takes a finished Application and writes it to disk as a per-job folder
containing the tailored CV, cover letter, job summary, and apply link.

The writer is deterministic. The LLM produces plain text; this module
handles the conversion to DOCX, the folder naming, and the file layout.
Keeping the file system logic out of the LLM step means we can change
the output format later without touching any prompts.
"""

import re
import unicodedata
from pathlib import Path

from docx import Document

from job_agent.models import Application


# Maximum length for the sanitised folder name. 80 leaves headroom on
# all common file systems (Windows path limit is 260 chars including
# the parent directory, the file name inside, and the extension).
MAX_FOLDER_NAME_LENGTH = 80

# Filenames written inside each job folder. Constants so tests and
# downstream code can reference the exact names without string drift.
CV_FILENAME = "custom_resume.docx"
COVER_LETTER_FILENAME = "cover_letter.docx"
JOB_SUMMARY_FILENAME = "job_summary.txt"
APPLY_LINK_FILENAME = "apply_here.txt"


class OutputWriterError(Exception):
    """Raised when the output cannot be written for any reason."""


def sanitize_job_title(title: str, company: str = "") -> str:
    """Convert a job title and optional company name to a safe folder name.

    Steps applied in order:
        1. Normalise unicode to NFKD and strip combining marks, so accented
           characters become their base letters (e.g. "Müller" -> "Muller").
           This avoids surprises on file systems that handle unicode poorly.
        2. Remove the common "m/f/d", "(m/w/d)", and similar gender markers
           because they add noise without information.
        3. Replace any character that is not a letter, digit, dash, or
           underscore with a single underscore.
        4. Collapse runs of underscores and trim leading/trailing ones.
        5. Truncate to MAX_FOLDER_NAME_LENGTH.
        6. Fall back to "Untitled_Job" if the result is empty.

    Args:
        title: The raw job title from the search tool.
        company: Optional company name, appended after the title.

    Returns:
        A folder-name-safe string.
    """
    combined = f"{title}_{company}" if company else title

    # Step 1: unicode normalisation.
    normalised = unicodedata.normalize("NFKD", combined)
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")

    # Step 2: strip common gender markers like (m/f/d), m/w/d, (f/m/x).
    ascii_only = re.sub(
        r"\(?[a-zA-Z]{1,2}(?:/[a-zA-Z]{1,2}){1,3}\)?",
        "",
        ascii_only,
    )

    # Step 3: replace non-alphanumeric (except dash and underscore) with _.
    replaced = re.sub(r"[^A-Za-z0-9_\-]+", "_", ascii_only)

    # Step 4: collapse runs of underscores and trim.
    collapsed = re.sub(r"_+", "_", replaced).strip("_-")

    # Step 5: truncate.
    truncated = collapsed[:MAX_FOLDER_NAME_LENGTH].rstrip("_-")

    # Step 6: fallback for empty result.
    return truncated or "Untitled_Job"


def create_job_folder(base_dir: Path, folder_name: str) -> Path:
    """Create a unique folder under base_dir, suffixing if it already exists.

    If "Data_Analyst_Acme" already exists, the next call returns
    "Data_Analyst_Acme_2", then "_3", and so on. This avoids overwriting
    a previous run's output and lets the user keep multiple applications
    for similar jobs side by side.
    """
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    candidate = base_dir / folder_name
    if not candidate.exists():
        candidate.mkdir()
        return candidate

    suffix = 2
    while True:
        candidate = base_dir / f"{folder_name}_{suffix}"
        if not candidate.exists():
            candidate.mkdir()
            return candidate
        suffix += 1


def write_application(application: Application, base_dir: Path) -> Path:
    """Write a complete Application to a new folder under base_dir.

    Args:
        application: The Application produced by the rewriter step.
        base_dir: The output directory configured in Config.

    Returns:
        The absolute path to the folder that was created.

    Raises:
        OutputWriterError: If the folder cannot be created or any file
            cannot be written.
    """
    try:
        folder_name = sanitize_job_title(
            application.job.title, application.job.company
        )
        folder = create_job_folder(base_dir, folder_name)

        _write_docx(folder / CV_FILENAME, application.tailored_cv)
        _write_docx(folder / COVER_LETTER_FILENAME, application.cover_letter)
        _write_text(folder / JOB_SUMMARY_FILENAME, application.job_summary)
        _write_text(folder / APPLY_LINK_FILENAME, application.job.apply_url)

        return folder.resolve()
    except OutputWriterError:
        raise
    except Exception as exc:
        raise OutputWriterError(f"Failed to write application: {exc}") from exc


def _write_docx(path: Path, content: str) -> None:
    """Write plain text to a DOCX, splitting on blank lines into paragraphs.

    The LLM produces plain text with blank lines as paragraph separators.
    We map that to DOCX paragraphs directly, which gives a readable
    document without trying to interpret formatting hints from the model.
    """
    doc = Document()
    for paragraph_text in content.split("\n\n"):
        doc.add_paragraph(paragraph_text.strip())
    doc.save(str(path))


def _write_text(path: Path, content: str) -> None:
    """Write plain text with UTF-8 encoding and a trailing newline."""
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
