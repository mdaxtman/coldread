"""Tests for config helpers — focused on the CORS allowlist security contract."""

import pytest

import config


def test_cors_origins_defaults_to_dev_server(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert config.get_cors_origins() == ["http://localhost:5173"]


def test_cors_origins_parses_comma_separated_and_strips(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", " https://a.example , https://b.example ")
    assert config.get_cors_origins() == ["https://a.example", "https://b.example"]


def test_cors_origins_drops_literal_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    # A misconfigured env must never silently reintroduce the "*" wildcard.
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example,*")
    origins = config.get_cors_origins()
    assert "*" not in origins
    assert origins == ["https://a.example"]


def test_cors_origins_wildcard_only_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    # Dropping "*" must not leave an empty allowlist (which some stacks treat
    # as allow-all); fall back to the safe dev default instead.
    monkeypatch.setenv("CORS_ORIGINS", "*")
    assert config.get_cors_origins() == ["http://localhost:5173"]
