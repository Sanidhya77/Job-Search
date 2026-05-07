# Report 9 — Testing Strategy (Initial)

*Auto-generated from Step 1 submission. Purpose: plan how system correctness will be validated.*

## Unit Tests

Each tool module (CV reader, job search mock, output writer, string sanitization) will have dedicated unit tests. These tests will verify correct input processing, output formatting, and error handling for edge cases (e.g., empty files, invalid characters, malformed data). Mocked responses will be used for external API interactions.

## Tool Interaction Tests

Tests will be written to ensure seamless data flow between consecutive tools. For example, verifying that the output string from the CV reader is correctly processed by the LLM analysis module, or that the structured output from the job search tool is correctly passed to the scoring module.

## AI Behavior Validation

- Accuracy of CV profile extraction.
- Consistency and correctness of relevance scores against predefined scenarios.
- Adherence to instructions in generated content (e.g., not inventing skills).

Mocked LLM responses will be used for deterministic testing, with real API calls used sparingly for validation during development.

## Acceptance Criteria

- The system successfully processes a variety of CV formats (PDF, DOCX) and extracts key information accurately.
- It retrieves relevant job postings based on user briefs.
- The relevance scoring mechanism correctly filters jobs according to the 60–70% threshold for a diverse set of test cases.
- Generated tailored CVs and cover letters are coherent, relevant, and do not contain fabricated information.
- Output files (DOCX, TXT) are correctly generated and organized in valid directory structures.
- The system handles errors gracefully and provides informative messages without crashing.
