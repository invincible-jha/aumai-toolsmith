"""Pydantic models for aumai-toolsmith."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = [
    "ToolSpec",
    "GeneratedTool",
    "ToolTemplate",
]


class ToolSpec(BaseModel):
    """Specification for an AI tool function."""

    name: str = Field(description="Python-safe function name, e.g. 'search_web'.")
    description: str
    parameters: list[dict[str, object]] = Field(
        default_factory=list,
        description="List of parameter dicts with 'name', 'type', 'description', 'required'.",
    )
    returns: dict[str, object] = Field(
        default_factory=dict,
        description="Return value description with 'type' and 'description'.",
    )
    examples: list[dict[str, object]] = Field(default_factory=list)


class GeneratedTool(BaseModel):
    """A tool generated from a ToolSpec."""

    spec: ToolSpec
    source_code: str = Field(description="Runnable Python source code.")
    test_code: str = Field(description="pytest test code for the tool.")
    documentation: str = Field(description="Markdown documentation string.")


class ToolTemplate(BaseModel):
    """A reusable skeleton template for tool generation."""

    template_id: str
    name: str
    description: str
    skeleton: str = Field(description="Python code skeleton with {placeholders}.")
