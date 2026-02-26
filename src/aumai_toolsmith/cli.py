"""CLI entry point for aumai-toolsmith."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from aumai_toolsmith.core import BUILT_IN_TEMPLATES, ToolGenerator, ToolSpecBuilder
from aumai_toolsmith.models import ToolSpec

_builder = ToolSpecBuilder()
_generator = ToolGenerator()


@click.group()
@click.version_option()
def main() -> None:
    """AumAI ToolSmith — AI-assisted tool creation framework CLI."""


@main.command("create")
@click.option("--description", required=True, help="Natural language description of the tool.")
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output Python file path.",
)
@click.option(
    "--template",
    type=click.Choice(list(BUILT_IN_TEMPLATES.keys())),
    default=None,
    help="Built-in template to use.",
)
def create(description: str, output: Path | None, template: str | None) -> None:
    """Create a tool from a natural language description."""
    spec = _builder.from_description(description)
    tpl = BUILT_IN_TEMPLATES.get(template) if template else None
    tool = _generator.generate(spec, template=tpl)

    click.echo(f"Generated tool: {spec.name}")
    click.echo("--- Source Code ---")
    click.echo(tool.source_code)

    if output is not None:
        output.write_text(tool.source_code, encoding="utf-8")
        click.echo(f"\nSource saved to {output}")
        test_path = output.with_name(f"test_{output.name}")
        test_path.write_text(tool.test_code, encoding="utf-8")
        click.echo(f"Tests saved to {test_path}")


@main.command("schema")
@click.option(
    "--spec",
    "spec_file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to ToolSpec JSON or YAML file.",
)
@click.option(
    "--format",
    "schema_format",
    default="openai",
    show_default=True,
    type=click.Choice(["openai", "mcp"]),
    help="Schema format to generate.",
)
def schema(spec_file: Path, schema_format: str) -> None:
    """Generate a function calling schema from a ToolSpec file."""
    try:
        import yaml  # type: ignore[import-untyped]
        raw = spec_file.read_text(encoding="utf-8")
        if spec_file.suffix in {".yaml", ".yml"}:
            data: dict[str, object] = yaml.safe_load(raw)
        else:
            data = json.loads(raw)
    except ImportError:
        data = json.loads(spec_file.read_text(encoding="utf-8"))

    spec = ToolSpec.model_validate(data)

    if schema_format == "openai":
        result = _generator.generate_openai_schema(spec)
    else:
        result = _generator.generate_mcp_schema(spec)

    click.echo(json.dumps(result, indent=2))


@main.command("templates")
def templates() -> None:
    """List available built-in tool templates."""
    for template_id, template in BUILT_IN_TEMPLATES.items():
        click.echo(f"[{template_id}] {template.name}: {template.description}")


if __name__ == "__main__":
    main()
