"""Tests for the configuration loader."""

import pytest

from job_agent.config import load_config


def test_load_config_succeeds_with_required_env(monkeypatch, tmp_path):
    """Config loads cleanly when both required keys are set."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("SERPAPI_KEY", "serp-test")
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))

    cfg = load_config()

    assert cfg.openai_api_key == "sk-test"
    assert cfg.serpapi_key == "serp-test"
    assert cfg.openai_model == "gpt-4o-mini"
    assert cfg.relevance_threshold == 60
    assert cfg.output_dir == tmp_path.resolve()


def test_load_config_raises_when_openai_key_missing(monkeypatch):
    """Missing OPENAI_API_KEY produces a clear error, not a silent later failure."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("SERPAPI_KEY", "serp-test")

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        load_config()


def test_load_config_rejects_non_integer_threshold(monkeypatch):
    """Garbage in RELEVANCE_THRESHOLD is rejected at load time."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("SERPAPI_KEY", "serp-test")
    monkeypatch.setenv("RELEVANCE_THRESHOLD", "not-a-number")

    with pytest.raises(ValueError, match="RELEVANCE_THRESHOLD"):
        load_config()


def test_load_config_rejects_out_of_range_threshold(monkeypatch):
    """Threshold outside 0-100 is rejected."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("SERPAPI_KEY", "serp-test")
    monkeypatch.setenv("RELEVANCE_THRESHOLD", "150")

    with pytest.raises(ValueError, match="between 0 and 100"):
        load_config()
