# Report 4 — Requirements Specification (Draft)

*Auto-generated from Step 1 submission. Purpose: translate the idea into clear system requirements.*

## Functional Requirements

- The system SHALL accept a user's base CV (PDF or DOCX) and a brief description of their job search criteria.
- The system SHALL analyze the provided CV to extract key information such as skills, experience, and domain expertise.
- The system SHALL, if necessary, ask the user follow-up questions to clarify ambiguities or missing information in the CV or brief.
- The system SHALL search for job postings based on the user's brief.
- The system SHALL score each job posting against the user's CV profile to determine relevance, using a threshold of approximately 60–70% alignment.
- For jobs that meet the relevance threshold, the system SHALL generate a tailored version of the user's CV, a customized cover letter, a summary of the job description, and the direct application link.
- The system SHALL output these generated materials in a structured format (e.g., DOCX for CV/cover letter, TXT for summary).

## Non-Functional Requirements

- The system SHALL be cost-effective, with LLM usage kept to a minimum (e.g., GPT-4o-mini at ~$0.002 per run).
- The system SHALL be user-friendly, minimizing the need for user interaction beyond initial input and review.
- The system SHALL be reliable, with robust error handling for API failures, file issues, and unexpected data.
- The system SHALL ensure user privacy by not storing CVs or application data beyond the immediate processing session, and by keeping API keys secure.
- The system SHALL produce output files that are compatible with common document viewers (e.g., Microsoft Word, Google Docs).

## Constraints

- The system SHALL NOT automatically submit job applications.
- The system SHALL NOT invent skills, technologies, or experience not present in the original CV when tailoring materials.
- The system SHALL operate within the free tier limits of SerpApi (100 searches/month) during development and grading, with a fallback to JSearch if necessary.
- API keys for OpenAI and SerpApi MUST be managed securely and not committed to version control.

## Dependencies

The system depends on:
- OpenAI API access and GPT-4o-mini model.
- SerpApi service and API key.
- Python 3.x environment.
- Libraries: `openai`, `google-search-results`, `pdfplumber`, `python-docx`, `python-dotenv`, `pathlib`, `re`, `unicodedata`, `pytest`.

## Success Criteria

- Successful execution of the agent for a given CV and brief, resulting in a set of relevant job applications with tailored materials.
- Reduction in time spent per job application by the user.
- Positive user feedback on the quality and relevance of generated application materials.
- All generated materials (tailored CV, cover letter, summary, link) are accurate and correctly formatted.
- System handles common errors gracefully without crashing.
