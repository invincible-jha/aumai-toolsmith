"""Shared test fixtures for aumai-toolsmith."""

from __future__ import annotations

import pytest

from aumai_toolsmith.core import BUILT_IN_TEMPLATES, ToolGenerator, ToolSpecBuilder
from aumai_toolsmith.models import ToolSpec, ToolTemplate


@pytest.fixture()
def builder() -> ToolSpecBuilder:
    """Return a ToolSpecBuilder instance."""
    return ToolSpecBuilder()


@pytest.fixture()
def generator() -> ToolGenerator:
    """Return a ToolGenerator instance."""
    return ToolGenerator()


@pytest.fixture()
def search_spec() -> ToolSpec:
    """Return a ToolSpec for a web search tool."""
    return ToolSpec(
        name="search_web",
        description="Search the web for information given a query string",
        parameters=[
            {"name": "query", "type": "str", "description": "The search query.", "required": True},
            {"name": "max_results", "type": "int", "description": "Max results to return.", "required": False},
        ],
        returns={"type": "list", "description": "List of search result URLs."},
        examples=[
            {"input": {"query": "python testing"}, "output": ["https://pytest.org"]},
        ],
    )


@pytest.fixture()
def http_template() -> ToolTemplate:
    """Return the built-in HTTP tool template."""
    return BUILT_IN_TEMPLATES["http_tool"]
