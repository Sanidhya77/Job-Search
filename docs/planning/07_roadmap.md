# Report 7 — Development Plan / Roadmap

*Auto-generated from Step 1 submission and adjusted to match the actual project deadline of 22 May. Purpose: organize implementation work into milestones, tasks, and a timeline.*

## Milestone 1: Core Agent Framework and I/O

Establish the basic agent structure, implement file reading (PDF/DOCX) and writing capabilities, and set up configuration management.

**Tasks:**
- Setup project structure and version control.
- Implement `python-dotenv` for configuration.
- Develop `CVReader` tool using `pdfplumber` and `python-docx`.
- Develop `OutputWriter` tool using `python-docx` and `pathlib`.
- Create initial agent control loop structure.
- Implement basic error handling for I/O operations.

**Timeline Estimate:** 4 days (Days 1–4).

## Milestone 2: Job Search Integration and LLM Setup

Integrate the job search tool and set up the LLM client for initial reasoning tasks.

**Tasks:**
- Implement `JobSearch` tool using SerpApi (and JSearch fallback).
- Integrate OpenAI SDK for GPT-4o-mini.
- Develop initial LLM prompts for CV profile extraction.
- Implement basic LLM interaction for CV analysis.
- Setup testing framework with mocks for I/O and search tools.

**Timeline Estimate:** 3 days (Days 5–7).

## Milestone 3: LLM Reasoning and Filtering Logic

Develop and refine the LLM-driven scoring, filtering, and content generation logic.

**Tasks:**
- Implement LLM prompt for job-to-CV scoring and justification.
- Develop relevance threshold filtering logic.
- Implement LLM prompts for CV bullet point rewriting and cover letter drafting.
- Integrate LLM reasoning steps into the agent pipeline.
- Refine string sanitization for output file paths.

**Timeline Estimate:** 5 days (Days 8–12).

## Milestone 4: Adaptive Questioning and Refinement

Implement adaptive questioning and conduct comprehensive testing and refinement.

**Tasks:**
- Develop logic for adaptive follow-up questions based on CV analysis.
- Implement comprehensive error handling and logging across all modules.
- Write unit and integration tests for all components.
- Conduct end-to-end testing with diverse CVs and job briefs.
- Optimize LLM prompts for accuracy and cost.
- Prepare documentation (README).

**Timeline Estimate:** 5 days (Days 13–17).
