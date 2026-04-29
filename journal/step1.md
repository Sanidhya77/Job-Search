# Step 1 (24.04)

We have determined the core system description, AI/agent approach, list of tools, and preliminary programming concepts for the AI-Assisted Job Application Agent.

## System Description

The system is a CLI tool designed to simplify job applications. Instead of a multi-agent approach, we chose a single agent with tool-calling. This reflects a sequential workflow, minimizing unnecessary coordination overhead. The pipeline handles everything from reading a user CV to searching for jobs and generating tailored applications.

## AI/Agent Approach

We rely on `gpt-4o-mini` strictly for reasoning steps. This includes:
- Information extraction from the provided CV.
- Scoring job alignment against the extracted profile.
- Rewriting CV bullet points and generating a drafted cover letter.

By separating the deterministic actions (API calls, file I/O, sanitization) from the LLM, we greatly limit the potential for hallucinations and ensure system reliability.

## Tools

1. **Job search**: SerpApi (Google Jobs engine).
2. **CV reading**: `pdfplumber` (for PDFs) and `python-docx` (for DOCX).
3. **Output writing**: `python-docx` and standard Python library I/O for text generation and directory setup.

## Preliminary Programming Concepts

- Modular architecture emphasizing separation of concerns (tools vs. reasoning).
- Dataclasses for strict structural definitions (`UserProfile`, `Job`, `ScoredJob`, `Application`).
- Defensive Python techniques such as API mocking via saved fixtures.
