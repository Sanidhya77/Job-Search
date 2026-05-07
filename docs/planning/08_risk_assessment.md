# Report 8 — Risk Assessment Report

*Auto-generated from Step 1 submission. Purpose: identify potential issues and challenges early in the project lifecycle to inform mitigation strategies and ensure successful implementation.*

## AI Output Risks

The primary risk is LLM hallucination, where GPT-4o-mini might invent skills or experience not present in the user's CV when tailoring application materials. This could lead to inaccurate or misleading CVs and cover letters. Another risk is the subjective nature of LLM-based scoring; while a threshold is set, the interpretation of "alignment" might vary, potentially leading to jobs being incorrectly included or excluded. The prompt engineering for these LLM tasks needs to be precise to mitigate these risks.

## Dependency Risks

The system relies on external APIs: SerpApi for job searching and OpenAI for LLM capabilities. Disruptions, rate limits, or changes in these services could impact the agent's functionality. For instance, SerpApi's free tier limitations or changes in Google's job search structure could affect job retrieval. Similarly, OpenAI API costs or availability are critical dependencies. The use of libraries like `pdfplumber` and `python-docx` also introduces dependency risks if they have bugs or are not maintained.

## Complexity Risks

Parsing diverse CV formats (PDF, DOCX) presents significant complexity. Variations in layout, fonts, tables, and embedded objects can lead to data extraction errors, corrupting the input for subsequent analysis. The sanitisation of job titles for file paths also involves handling a wide array of special characters and unicode, which can be complex to implement robustly across different operating systems. The orchestration of multiple tools and LLM calls in a controlled sequence adds to the overall system complexity.

## Project Risks

A key project risk is managing user expectations. While the agent aims to reduce manual effort, the output quality is dependent on the LLM's capabilities and the accuracy of the input data. If the tailored materials are not perceived as sufficiently high-quality or relevant by the user, it could lead to dissatisfaction. Scope creep is also a risk; the intention is to stop at material generation, but there might be pressure to add features like auto-submission or more advanced user interaction. Ensuring the .env file is correctly managed and not committed to version control is a critical security risk.

## Practical Mitigation Strategies

To mitigate AI output risks, strict system prompts will be used, explicitly instructing the LLM to only rephrase existing information and not invent new skills. User review before submission is a core part of the design to catch any AI errors. For dependency risks, fallback mechanisms (e.g., JSearch if SerpApi fails) and careful monitoring of API usage and costs will be implemented. Robust error handling and clear reporting for tool failures are essential. To address complexity, thorough unit and integration testing with diverse inputs will be conducted, focusing on edge cases in file parsing and path sanitisation. For project risks, clear communication with stakeholders about the system's capabilities and limitations, and a strict adherence to the defined scope will be maintained. Security best practices, such as using `.gitignore` for sensitive files, will be enforced.
