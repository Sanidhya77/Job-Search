# Report 6 — Tool Integration Specification

*Auto-generated from Step 1 submission. Purpose: define how external tools are used, including their inputs, outputs, trigger conditions, and error handling.*

## SerpApi (Google Jobs Engine)

**Purpose:** To retrieve job listings from Google Jobs.
**Input:** A string query (e.g., "Python Developer remote").
**Output:** JSON of job listings, parsed into a list of `Job` dataclasses (title, company, location, description, apply_url, source).
**Trigger:** Called after initial CV analysis and user brief processing, when job search is initiated.
**Error Handling:** Catches `RateLimitError`, `APIError`, or `JSONDecodeError`. If SerpApi fails or returns insufficient data, the agent attempts to use JSearch (RapidAPI) as a fallback. If both fail, a `JobSearchError` is raised, and the agent reports a clear error to the user.

## pdfplumber

**Purpose:** To extract text from PDF CV files.
**Input:** A `pathlib.Path` object pointing to a PDF file.
**Output:** A string containing the normalized text content of the PDF.
**Trigger:** Called when the user's CV is provided as a PDF file.
**Error Handling:** Wraps errors in a custom `CVReaderError` exception, distinguishing between missing files, unsupported extensions, and corrupted files. This ensures the agent can report specific issues to the user.

## python-docx

**Purpose:** To read DOCX CV files and write generated application materials (tailored CV, cover letter) into DOCX format.
**Input:** For reading: a `pathlib.Path` object pointing to a DOCX file. For writing: an `Application` dataclass containing the generated content.
**Output:** For reading: a string containing the normalized text content. For writing: a `.docx` file saved to disk.
**Trigger:** Reading is triggered when a DOCX CV is provided. Writing is triggered after LLM generation of tailored CV and cover letter.
**Error Handling:** Errors during reading or writing are caught and wrapped in a `CVReaderError` or a custom `FileWriterError` respectively, providing specific feedback on file issues or permission problems.

## OpenAI GPT-4o-mini (via OpenAI SDK)

**Purpose:** To perform AI reasoning tasks: CV analysis, job scoring, CV rewriting, cover letter drafting.
**Input:** Structured prompts containing user profile, job descriptions, and specific instructions.
**Output:** Text responses (extracted data, scores, rewritten text, drafted letters).
**Trigger:** Called at multiple stages of the pipeline: CV analysis, job scoring/filtering, and content generation.
**Error Handling:** Handles API errors (e.g., `APIConnectionError`, `RateLimitError`, `AuthenticationError`) by retrying or reporting a critical failure. Explicit prompts are used to mitigate hallucinations, and the system is designed to handle unexpected output formats by parsing carefully.
