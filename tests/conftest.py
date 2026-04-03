"""Pytest configuration and shared fixtures."""

import pathlib

import pytest


@pytest.fixture(scope="session", autouse=True)
def _ensure_report_dirs():
    """Create build/reports before any test runs so coverage/junit sinks exist."""
    pathlib.Path("build/reports").mkdir(parents=True, exist_ok=True)
