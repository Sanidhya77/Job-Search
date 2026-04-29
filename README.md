# AI-Assisted Job Application Agent

A CLI tool that helps users apply for jobs by intelligently analyzing their CV and matching it against job listings.

## Overview

This project provides an AI agent that takes a user's CV (PDF or DOCX), searches for relevant jobs via SerpApi, scores each job against the CV, and generates tailored CV bullet points and cover letters for matches with high alignment (60-70%+).

It relies on a modular architecture:
- **CLI**: Standard Python interface for taking inputs.
- **Tools**: Deterministic Python integrations (CV parsing, job searching, file saving).
- **LLM Engine**: Uses `gpt-4o-mini` for reasoning (scoring, information extraction, rewriting).

## Features

- Parse PDF and DOCX CVs.
- Search for job listings via Google Jobs (SerpApi).
- Score job alignment using AI reasoning.
- Generate tailored application materials without web hallucination risks.

## Setup

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and fill in your API keys (OpenAI and SerpApi).
4. Run the application via the CLI (instructions to be added).
