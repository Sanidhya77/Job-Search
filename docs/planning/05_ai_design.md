# Report 5 — AI / Agent Design Report

*Auto-generated from Step 1 submission. Purpose: explain how intelligence is implemented.*

## Agent Workflow and Control Flow

1. Input (CV, brief).
2. File Reader tool (extracts CV text).
3. Follow-up questions (if needed, based on LLM analysis of missing or ambiguous info).
4. Search tool (finds candidate jobs).
5. LLM Reasoning (scores jobs against CV profile, filters by relevance threshold).
6. LLM Reasoning (rewrites CV bullet points, drafts cover letter).
7. File Writer tool (generates output files).
8. Output (application materials, links).

## Tool-Calling Logic

The agent's Python code explicitly calls external tools for specific, deterministic tasks. The LLM is invoked for reasoning-intensive steps. The division is: Python code handles API calls, file I/O, and orchestration; LLM handles CV analysis, job scoring, and text generation. This separation ensures reliability for critical operations.

## Decision-Making Process

- Determining if follow-up questions are necessary by identifying gaps in user input.
- Assigning a numeric alignment score (0–100) to each job based on explicit criteria (skill match, seniority, hard blockers).
- Filtering jobs based on a relevance threshold (60–70% score).
- Rewriting CV bullet points and drafting cover letters to match specific job requirements without inventing new information.

## AI Model and Capabilities

- Information Extraction (parsing CV into a structured profile).
- Classification with Numeric Scoring (job relevance assessment).
- Constrained Text Generation (tailoring application materials).

## Relevance Threshold Determination

After job search results are obtained, each job description and the user's CV profile are sent to GPT-4o-mini. The LLM is prompted to return a numeric alignment score (0–100) and a one-sentence justification. Jobs scoring 60 or above are retained for further processing.

## Adaptive Follow-up Questions

The agent analyzes the initial CV and brief. If information is missing or ambiguous (e.g., location preferences not stated when CV shows specific experience), the LLM is used to formulate targeted questions to the user, avoiding redundant queries.

## Limitations and Risk Mitigation

Hallucination is a primary risk, particularly in rewriting CV bullet points. This is mitigated by explicit system prompts instructing the LLM to only rephrase existing experience and never invent new skills, technologies, or numbers. Reliability risks are managed by confining LLM use to reasoning tasks and using deterministic Python code for critical operations like file handling and API calls. The agent's scope intentionally stops at generating application materials, preventing risks associated with automated submission.
