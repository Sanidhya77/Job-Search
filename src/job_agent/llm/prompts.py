"""System prompts for the three LLM reasoning steps.

All prompts live in this single file so they are version-controlled,
reviewable in pull requests, and easy to point at when writing the
Step 3 report. Keeping prompts as Python string constants (rather than
scattering them across the LLM modules) means changes to a prompt
show up as a single-file diff.

Each prompt is paired with a comment block above it that explains
what input the prompt expects and what output format it must return.
"""


# ============================================================
# CV ANALYSER
# Input:  full CV text (string)
# Output: JSON object matching the UserProfile dataclass fields
# ============================================================
CV_ANALYSER_PROMPT = """You are a CV analyser. Read the CV text and extract \
ONLY information that is explicitly present. Never invent, infer, or guess \
skills, experience, certifications, or details that are not in the source.

Return a JSON object with these exact fields:
- full_name: string (the candidate's name as it appears in the CV)
- skills: array of strings (technical and professional skills explicitly listed)
- years_of_experience: number (estimate based on dated work history; 0 if no dated experience)
- seniority: one of "junior" (0-2 years), "mid" (2-5 years), "senior" (5+ years)
- domains: array of strings (e.g. ["data analysis", "backend web", "devops"])
- languages: array of strings (spoken/written languages, NOT programming languages)
- location_preference: string or null (city or country if stated, otherwise null)
- remote_preference: one of "remote", "hybrid", "onsite", or null

If a field cannot be determined from the CV, use the null/default value \
rather than guessing. Return only the JSON object, no markdown fences, no \
explanation."""


# Scorer and rewriter prompts are scheduled for tomorrow.
SCORER_PROMPT = ""
REWRITER_PROMPT = ""
