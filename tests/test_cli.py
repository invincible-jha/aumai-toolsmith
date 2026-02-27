"""Comprehensive CLI tests for aumai-toolsmith."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from aumai_toolsmith.cli import main


@pytest.fixture()
def runner() -> CliRunner:
    """Return a Click test runner."""
    return CliRunner()


@pytest.fixture()
def spec_json(tmp_path: Path) -> Path:
    """Write a valid ToolSpec JSON file and return its path."""
    spec_data = {
        "name": "my_tool",
        "description": "A test tool that searches for information given a query",
        "parameters": [
            {"name": "query", "type": "str", "description": "The search query.", "required": True},
        ],
        "returns": {"type": "list", "description": "List of results."},
        "examples": [],
    }
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec_data), encoding="utf-8")
    return spec_file


class TestCliVersion:
    """Tests for --version flag."""

    def test_version_flag(self, runner: CliRunner) -> None:
        """--version must exit 0 and report version."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help_flag(self, runner: CliRunner) -> None:
        """--help must exit 0 and describe the CLI."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "ToolSmith" in result.output


class TestTemplatesCommand:
    """Tests for the `templates` command."""

    def test_templates_exits_zero(self, runner: CliRunner) -> None:
        """templates command exits 0."""
        result = runner.invoke(main, ["templates"])
        assert result.exit_code == 0

    def test_templates_lists_http_tool(self, runner: CliRunner) -> None:
        """templates command lists 'http_tool'."""
        result = runner.invoke(main, ["templates"])
        assert "http_tool" in result.output

    def test_templates_lists_file_tool(self, runner: CliRunner) -> None:
        """templates command lists 'file_tool'."""
        result = runner.invoke(main, ["templates"])
        assert "file_tool" in result.output

    def test_templates_lists_database_tool(self, runner: CliRunner) -> None:
        """templates command lists 'database_tool'."""
        result = runner.invoke(main, ["templates"])
        assert "database_tool" in result.output

    def test_templates_lists_search_tool(self, runner: CliRunner) -> None:
        """templates command lists 'search_tool'."""
        result = runner.invoke(main, ["templates"])
        assert "search_tool" in result.output


class TestCreateCommand:
    """Tests for the `create` command."""

    def test_create_basic(self, runner: CliRunner) -> None:
        """create exits 0 for a valid description."""
        result = runner.invoke(
            main, ["create", "--description", "Search documents given a query string"]
        )
        assert result.exit_code == 0

    def test_create_prints_generated_tool(self, runner: CliRunner) -> None:
        """create prints 'Generated tool:' header."""
        result = runner.invoke(
            main, ["create", "--description", "Fetch weather for a city"]
        )
        assert "Generated tool" in result.output

    def test_create_prints_source_code(self, runner: CliRunner) -> None:
        """create prints source code after the header."""
        result = runner.invoke(
            main, ["create", "--description", "Fetch data from an API endpoint"]
        )
        assert "Source Code" in result.output

    def test_create_with_template(self, runner: CliRunner) -> None:
        """create with --template uses the specified template."""
        result = runner.invoke(
            main,
            [
                "create",
                "--description", "Fetch JSON from a URL given the endpoint",
                "--template", "http_tool",
            ],
        )
        assert result.exit_code == 0

    def test_create_saves_output_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """create --output writes source code to file."""
        output_file = tmp_path / "my_tool.py"
        result = runner.invoke(
            main,
            [
                "create",
                "--description", "Search web for information given a query",
                "--output", str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        assert "saved" in result.output.lower()

    def test_create_saves_test_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """create --output also writes a test file alongside."""
        output_file = tmp_path / "my_tool.py"
        runner.invoke(
            main,
            [
                "create",
                "--description", "Do something useful given input data",
                "--output", str(output_file),
            ],
        )
        test_file = tmp_path / "test_my_tool.py"
        assert test_file.exists()

    def test_create_missing_description(self, runner: CliRunner) -> None:
        """create exits non-zero when --description is missing."""
        result = runner.invoke(main, ["create"])
        assert result.exit_code != 0


class TestSchemaCommand:
    """Tests for the `schema` command."""

    def test_schema_openai_format(
        self, runner: CliRunner, spec_json: Path
    ) -> None:
        """schema --format openai outputs valid JSON with 'type': 'function'."""
        result = runner.invoke(
            main, ["schema", "--spec", str(spec_json), "--format", "openai"]
        )
        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert output_json["type"] == "function"

    def test_schema_mcp_format(
        self, runner: CliRunner, spec_json: Path
    ) -> None:
        """schema --format mcp outputs valid JSON with 'inputSchema' key."""
        result = runner.invoke(
            main, ["schema", "--spec", str(spec_json), "--format", "mcp"]
        )
        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert "inputSchema" in output_json

    def test_schema_default_format_is_openai(
        self, runner: CliRunner, spec_json: Path
    ) -> None:
        """schema defaults to openai format."""
        result = runner.invoke(main, ["schema", "--spec", str(spec_json)])
        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert "function" in output_json

    def test_schema_missing_spec(self, runner: CliRunner, tmp_path: Path) -> None:
        """schema exits non-zero when --spec file does not exist."""
        result = runner.invoke(
            main, ["schema", "--spec", str(tmp_path / "missing.json")]
        )
        assert result.exit_code != 0

    def test_schema_invalid_format_choice(
        self, runner: CliRunner, spec_json: Path
    ) -> None:
        """schema exits non-zero for an invalid --format value."""
        result = runner.invoke(
            main, ["schema", "--spec", str(spec_json), "--format", "invalid"]
        )
        assert result.exit_code != 0
