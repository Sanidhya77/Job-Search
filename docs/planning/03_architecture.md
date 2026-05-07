# Report 3 — System Architecture Overview

*Auto-generated from Step 1 submission. Purpose: define how the system will work structurally.*

## Architecture Style

Deterministic Pipeline Orchestration. The system uses a sequential control flow managed entirely by Python code, invoking the LLM only for specific reasoning tasks (extraction, scoring, rewriting) rather than acting as a free-form autonomous agent. This limits hallucination risks to text generation and keeps system operations reliable.

## Major Components

- **Input/Config Manager:** Loads the base CV and user brief.
- **Search Module:** Integrates with SerpApi to fetch job listings.
- **Reasoning Engine:** Uses OpenAI GPT-4o-mini for profile extraction, job scoring, and document tailoring.
- **Output Generator:** Creates sanitized directories and writes DOCX/TXT files.

## Data Flow

Unstructured CV → File Reader → Normalized String → LLM → UserProfile dataclass.
Search Query → SerpApi → Job dataclasses.
UserProfile + Job → LLM Scorer → ScoredJob.
ScoredJob (>60%) → LLM Rewriter → Application dataclass → File Writer → Local Filesystem.

## Design Patterns

Modular Tooling and Dataclasses. Tools are isolated in a `tools/` directory with single public functions and custom exception types (e.g., `CVReaderError`). Data is passed between modules using strongly typed Python dataclasses (`UserProfile`, `Job`, `Application`) to ensure strict contracts between the deterministic Python code and the LLM outputs.
