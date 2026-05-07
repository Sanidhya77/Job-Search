# Report 1 — Project Concept / Vision Report

*Auto-generated from Step 1 submission. Purpose: align stakeholders on what is being built and why.*

## Problem Statement

The current job application process is time-consuming and inefficient, requiring manual editing of CVs and cover letters for each role. This leads to a significant time investment per application and a tendency to send generic applications, reducing effectiveness.

## System Goal

To empower job seekers by automating the creation of tailored application materials. The system aims to reduce the time spent per application from 20–30 minutes to a single command, while maintaining user control over the final submission. It will deliver a customized CV, cover letter, job summary, and application link for relevant job opportunities.

## Innovation / AI / Agent Approach

The system employs a Python agent that leverages GPT-4o-mini for intelligent analysis and content generation. Its innovation lies in its ability to understand unstructured text (CVs, job descriptions), make nuanced decisions about job relevance through a scoring mechanism, and adaptively generate personalized application content. The agent operates as a controlled pipeline, distinguishing between deterministic Python logic and LLM-driven reasoning to ensure reliability and manage potential AI limitations.

## Key Features and Scope

The agent will analyze user CVs and search briefs, ask clarifying questions if needed, search for jobs, score job relevance (60–70% threshold), and generate tailored CVs, cover letters, job summaries, and apply links. Auto-submission is explicitly out of scope to ensure human oversight and prevent platform penalties. The system focuses on producing high-quality, personalized application materials.

## Target User

Job seekers looking to optimize their application process, save time, and increase their chances of success by submitting more targeted and personalized applications.
