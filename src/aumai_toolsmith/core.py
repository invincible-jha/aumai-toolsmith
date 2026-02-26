"""Core logic for aumai-toolsmith."""

from __future__ import annotations

import re
import textwrap

from aumai_toolsmith.models import GeneratedTool, ToolSpec, ToolTemplate

__all__ = ["ToolSpecBuilder", "ToolGenerator", "BUILT_IN_TEMPLATES"]

# ---------------------------------------------------------------------------
# Built-in templates
# ---------------------------------------------------------------------------

BUILT_IN_TEMPLATES: dict[str, ToolTemplate] = {
    "http_tool": ToolTemplate(
        template_id="http_tool",
        name="HTTP Tool",
        description="Tool that makes HTTP requests.",
        skeleton=textwrap.dedent("""\
            import urllib.request
            import json as _json
            from typing import Any


            def {name}({params}) -> {return_type}:
                \"\"\"{description}\"\"\"
                url = {url_param}
                req = urllib.request.Request(url, headers={{"User-Agent": "aumai-toolsmith/0.1"}})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    body = resp.read().decode("utf-8")
                return _json.loads(body)
        """),
    ),
    "file_tool": ToolTemplate(
        template_id="file_tool",
        name="File Tool",
        description="Tool that reads or writes files.",
        skeleton=textwrap.dedent("""\
            from pathlib import Path


            def {name}({params}) -> {return_type}:
                \"\"\"{description}\"\"\"
                path = Path({path_param})
                return path.read_text(encoding="utf-8")
        """),
    ),
    "database_tool": ToolTemplate(
        template_id="database_tool",
        name="Database Tool",
        description="Tool that queries a database using parameterized SQL.",
        skeleton=textwrap.dedent("""\
            import sqlite3
            from typing import Any


            def {name}({params}) -> {return_type}:
                \"\"\"{description}\"\"\"
                conn = sqlite3.connect({db_param})
                cursor = conn.execute({query_param}, {args_param})
                rows = cursor.fetchall()
                conn.close()
                return rows
        """),
    ),
    "search_tool": ToolTemplate(
        template_id="search_tool",
        name="Search Tool",
        description="Tool that searches a collection of documents.",
        skeleton=textwrap.dedent("""\
            from typing import Any


            def {name}({params}) -> {return_type}:
                \"\"\"{description}\"\"\"
                query_lower = {query_param}.lower()
                results = [
                    item for item in {corpus_param}
                    if query_lower in str(item).lower()
                ]
                return results[:{limit_param}]
        """),
    ),
}


class ToolSpecBuilder:
    """Build ToolSpec objects from natural language descriptions or examples."""

    def from_description(self, description: str) -> ToolSpec:
        """Parse a natural language description into a structured ToolSpec.

        Extracts a function name from the first verb phrase and infers
        parameters from common patterns like 'given X', 'with Y', 'for Z'.

        Args:
            description: Natural language description of the tool.

        Returns:
            A ToolSpec with inferred name, parameters, and return info.
        """
        name = self._extract_name(description)
        parameters = self._extract_parameters(description)
        returns = self._extract_returns(description)

        return ToolSpec(
            name=name,
            description=description,
            parameters=parameters,
            returns=returns,
        )

    def from_example(
        self, input_output_pairs: list[dict[str, object]]
    ) -> ToolSpec:
        """Infer a ToolSpec from input/output example pairs.

        Each pair must have 'input' and 'output' keys. The tool name
        defaults to 'inferred_tool'. Parameter types are inferred from
        the Python types of input values.

        Args:
            input_output_pairs: List of {'input': ..., 'output': ...} dicts.

        Returns:
            A ToolSpec with inferred parameters and return type.

        Raises:
            ValueError: If no pairs are provided.
        """
        if not input_output_pairs:
            raise ValueError("At least one input/output pair is required.")

        first_input = input_output_pairs[0].get("input")
        first_output = input_output_pairs[0].get("output")

        parameters: list[dict[str, object]] = []
        if isinstance(first_input, dict):
            for key, value in first_input.items():
                parameters.append({
                    "name": key,
                    "type": type(value).__name__,
                    "description": f"Input parameter '{key}'.",
                    "required": True,
                })
        else:
            parameters.append({
                "name": "input",
                "type": type(first_input).__name__,
                "description": "Primary input.",
                "required": True,
            })

        return_type = type(first_output).__name__ if first_output is not None else "Any"
        returns: dict[str, object] = {
            "type": return_type,
            "description": "Result of the tool operation.",
        }

        return ToolSpec(
            name="inferred_tool",
            description="Tool inferred from input/output examples.",
            parameters=parameters,
            returns=returns,
            examples=input_output_pairs,
        )

    def _extract_name(self, description: str) -> str:
        """Extract a snake_case function name from the description."""
        # Take first 5 words, clean to snake_case
        words = re.findall(r"\b[a-zA-Z]+\b", description)[:5]
        name = "_".join(w.lower() for w in words if w.lower() not in {
            "a", "an", "the", "that", "this", "for", "to", "and", "or", "with"
        })
        return name[:50] or "unnamed_tool"

    def _extract_parameters(self, description: str) -> list[dict[str, object]]:
        """Extract parameter hints from description text."""
        params: list[dict[str, object]] = []
        # Look for patterns: "given X", "with X", "for X", "accepts X"
        patterns = [
            r"(?:given|with|for|accepts?|takes?)\s+(?:a\s+)?(\w+)",
            r"(\w+)\s+parameter",
            r"input\s+(\w+)",
        ]
        seen: set[str] = set()
        for pattern in patterns:
            for match in re.finditer(pattern, description, re.IGNORECASE):
                param_name = match.group(1).lower()
                if param_name not in seen and param_name not in {
                    "the", "a", "an", "this", "that"
                }:
                    seen.add(param_name)
                    params.append({
                        "name": param_name,
                        "type": "str",
                        "description": f"The {param_name} input.",
                        "required": True,
                    })

        if not params:
            params.append({
                "name": "query",
                "type": "str",
                "description": "Primary input query.",
                "required": True,
            })
        return params

    def _extract_returns(self, description: str) -> dict[str, object]:
        """Extract return type hints from description text."""
        if re.search(r"\blist\b|\barray\b|\bmultiple\b", description, re.IGNORECASE):
            return {"type": "list", "description": "List of results."}
        if re.search(r"\bdict\b|\bobject\b|\bjson\b", description, re.IGNORECASE):
            return {"type": "dict", "description": "Result object."}
        if re.search(r"\bbool\b|\bwhether\b|\bcheck\b|\bverify\b", description, re.IGNORECASE):
            return {"type": "bool", "description": "True if successful, False otherwise."}
        return {"type": "str", "description": "Result as a string."}


class ToolGenerator:
    """Generate Python source code, tests, and schemas from a ToolSpec."""

    def generate(
        self,
        spec: ToolSpec,
        template: ToolTemplate | None = None,
    ) -> GeneratedTool:
        """Generate a complete tool implementation from a spec.

        Args:
            spec: The tool specification.
            template: Optional template to use as the code skeleton.

        Returns:
            A GeneratedTool with source code, tests, and documentation.
        """
        source_code = self._generate_source(spec, template)
        test_code = self._generate_tests(spec)
        documentation = self._generate_docs(spec)

        return GeneratedTool(
            spec=spec,
            source_code=source_code,
            test_code=test_code,
            documentation=documentation,
        )

    def _generate_source(self, spec: ToolSpec, template: ToolTemplate | None) -> str:
        """Generate Python function source code."""
        param_parts: list[str] = []
        for param in spec.parameters:
            ptype = param.get("type", "str")
            pname = param.get("name", "arg")
            param_parts.append(f"{pname}: {ptype}")

        params_str = ", ".join(param_parts)
        return_type = spec.returns.get("type", "str") if spec.returns else "str"
        return_desc = spec.returns.get("description", "") if spec.returns else ""

        param_docs = "\n".join(
            f"        {p.get('name', 'arg')}: {p.get('description', '')}"
            for p in spec.parameters
        )

        if template:
            # Use template skeleton with basic substitution
            source = template.skeleton
            source = source.replace("{name}", spec.name)
            source = source.replace("{params}", params_str)
            source = source.replace("{return_type}", str(return_type))
            source = source.replace("{description}", spec.description)
            return source

        lines = [
            "from __future__ import annotations",
            "",
            f'def {spec.name}({params_str}) -> {return_type}:',
            f'    """{spec.description}',
            "",
            "    Args:",
            f"{param_docs}",
            "",
            "    Returns:",
            f"        {return_desc}",
            '    """',
            "    # TODO: implement tool logic",
            "    raise NotImplementedError",
        ]
        return "\n".join(lines)

    def _generate_tests(self, spec: ToolSpec) -> str:
        """Generate pytest test stubs for the tool."""
        import_line = f"from {spec.name}_module import {spec.name}"
        test_lines = [
            "import pytest",
            import_line,
            "",
            "",
            f"def test_{spec.name}_basic() -> None:",
            f'    """Test basic invocation of {spec.name}."""',
            "    # TODO: provide real test inputs",
        ]
        for param in spec.parameters:
            pname = param.get("name", "arg")
            ptype = param.get("type", "str")
            default_val = '"test"' if ptype == "str" else "0" if ptype == "int" else "False"
            test_lines.append(f"    {pname} = {default_val}")

        param_names = [str(p.get("name", "arg")) for p in spec.parameters]
        call_args = ", ".join(f"{n}={n}" for n in param_names)
        test_lines += [
            f"    result = {spec.name}({call_args})",
            "    assert result is not None",
        ]
        return "\n".join(test_lines)

    def _generate_docs(self, spec: ToolSpec) -> str:
        """Generate markdown documentation for the tool."""
        lines = [
            f"# `{spec.name}`",
            "",
            spec.description,
            "",
            "## Parameters",
            "",
        ]
        for param in spec.parameters:
            required = "required" if param.get("required") else "optional"
            lines.append(
                f"- **`{param.get('name', 'arg')}`** (`{param.get('type', 'Any')}`, {required}): "
                f"{param.get('description', '')}"
            )

        lines += [
            "",
            "## Returns",
            "",
            f"- `{spec.returns.get('type', 'Any')}`: {spec.returns.get('description', '')}",
        ]

        if spec.examples:
            lines += ["", "## Examples", ""]
            for i, example in enumerate(spec.examples, 1):
                lines.append(f"### Example {i}")
                lines.append(f"```python")
                lines.append(f"# Input: {example.get('input')}")
                lines.append(f"# Output: {example.get('output')}")
                lines.append("```")

        return "\n".join(lines)

    def generate_openai_schema(self, spec: ToolSpec) -> dict[str, object]:
        """Generate an OpenAI function-calling schema from a ToolSpec.

        Args:
            spec: The tool specification.

        Returns:
            OpenAI-compatible function schema dict.
        """
        properties: dict[str, object] = {}
        required: list[str] = []

        for param in spec.parameters:
            pname = str(param.get("name", "arg"))
            ptype = str(param.get("type", "string"))
            # Map Python types to JSON Schema types
            json_type = {
                "str": "string",
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object",
            }.get(ptype, "string")

            properties[pname] = {
                "type": json_type,
                "description": str(param.get("description", "")),
            }
            if param.get("required"):
                required.append(pname)

        return {
            "type": "function",
            "function": {
                "name": spec.name,
                "description": spec.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def generate_mcp_schema(self, spec: ToolSpec) -> dict[str, object]:
        """Generate a Model Context Protocol (MCP) tool schema from a ToolSpec.

        Args:
            spec: The tool specification.

        Returns:
            MCP-compatible tool definition dict.
        """
        properties: dict[str, object] = {}
        required: list[str] = []

        for param in spec.parameters:
            pname = str(param.get("name", "arg"))
            ptype = str(param.get("type", "string"))
            json_type = {
                "str": "string", "int": "integer", "float": "number",
                "bool": "boolean", "list": "array", "dict": "object",
            }.get(ptype, "string")

            properties[pname] = {
                "type": json_type,
                "description": str(param.get("description", "")),
            }
            if param.get("required"):
                required.append(pname)

        return {
            "name": spec.name,
            "description": spec.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }
