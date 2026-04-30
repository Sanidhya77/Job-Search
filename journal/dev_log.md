## Day 2 — Domain models and configuration

Added the core dataclasses (`UserProfile`, `Job`, `ScoredJob`, `Application`) in `src/job_agent/models.py` and the config loader in `src/job_agent/config.py`.

The dataclasses make the contracts between modules explicit. Later tools and LLM steps will have clear input and output types instead of passing dicts around, which also makes the data conversion explanation for Step 3 straightforward to write.

The `Config` dataclass is frozen so no module can accidentally mutate runtime settings that another module is also reading. The loader validates required keys and rejects out-of-range or non-integer values for the threshold, so misconfiguration fails at startup with a clear message rather than later inside an API call.

Tests cover the happy path and three failure cases for config (missing key, non-integer threshold, out-of-range threshold), plus shape checks for each dataclass. Pytest passes with 8 tests.

**Notes for Step 2 journal:**
- Why `raw_cv_text` lives on `UserProfile`: the rewriter needs the original wording to rewrite from, so bundling it with the profile means it does not have to be threaded separately through every function call.
- Why `Config` is frozen: mutable global config is a classic source of cross-module bugs. Freezing makes the contract obvious: read at startup, never modified after.
