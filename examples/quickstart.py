"""Quickstart examples for aumai-toolsmith.

Demonstrates building tool specs from natural language descriptions and
example pairs, generating Python source code and tests, producing OpenAI
and MCP schemas, and using built-in code templates.

Run this file directly to verify your installation:

    python examples/quickstart.py

No external services or API keys are required.
"""

from aumai_toolsmith.core import BUILT_IN_TEMPLATES, ToolGenerator, ToolSpecBuilder
from aumai_toolsmith.models import GeneratedTool, ToolSpec, ToolTemplate


# ---------------------------------------------------------------------------
# Demo 1: Build a ToolSpec from a natural language description
# ---------------------------------------------------------------------------


def demo_spec_from_description() -> None:
    """Parse a description string into a structured ToolSpec."""
    print("\n--- Demo 1: ToolSpec from Description ---")

    builder = ToolSpecBuilder()

    description = (
        "Search the web given a query and return a list of relevant URLs "
        "with titles and snippets."
    )
    spec: ToolSpec = builder.from_description(description)

    print(f"Name        : {spec.name}")
    print(f"Description : {spec.description[:60]}...")
    print(f"Parameters  : {[p['name'] for p in spec.parameters]}")
    print(f"Return type : {spec.returns.get('type')}")


# ---------------------------------------------------------------------------
# Demo 2: Build a ToolSpec from input/output examples
# ---------------------------------------------------------------------------


def demo_spec_from_examples() -> None:
    """Infer a ToolSpec from concrete input/output demonstration pairs."""
    print("\n--- Demo 2: ToolSpec from Examples ---")

    builder = ToolSpecBuilder()

    example_pairs = [
        {"input": {"city": "Mumbai", "unit": "celsius"}, "output": {"temp": 31.5, "humidity": 78}},
        {"input": {"city": "Delhi", "unit": "celsius"}, "output": {"temp": 28.0, "humidity": 55}},
    ]

    spec = builder.from_example(example_pairs)

    print(f"Inferred name    : {spec.name}")
    print(f"Inferred params  : {[p['name'] for p in spec.parameters]}")
    print(f"Inferred return  : {spec.returns}")
    print(f"Example count    : {len(spec.examples)}")


# ---------------------------------------------------------------------------
# Demo 3: Generate Python source code, tests, and documentation
# ---------------------------------------------------------------------------


def demo_generate_tool() -> None:
    """Generate a complete tool implementation from a ToolSpec."""
    print("\n--- Demo 3: Generate Tool Source, Tests, and Docs ---")

    builder = ToolSpecBuilder()
    generator = ToolGenerator()

    spec = ToolSpec(
        name="fetch_weather",
        description="Fetch current weather data for a city and return temperature and humidity.",
        parameters=[
            {"name": "city", "type": "str", "description": "Name of the city.", "required": True},
            {"name": "unit", "type": "str", "description": "Temperature unit: celsius or fahrenheit.", "required": False},
        ],
        returns={"type": "dict", "description": "Dictionary with temp and humidity keys."},
        examples=[
            {"input": {"city": "Mumbai"}, "output": {"temp": 31.5, "humidity": 78}},
        ],
    )

    generated: GeneratedTool = generator.generate(spec)

    print("Generated source_code:")
    print("  " + "\n  ".join(generated.source_code.splitlines()))

    print("\nGenerated test_code (first 5 lines):")
    test_lines = generated.test_code.splitlines()[:5]
    for line in test_lines:
        print(f"  {line}")

    print("\nGenerated documentation (first 8 lines):")
    doc_lines = generated.documentation.splitlines()[:8]
    for line in doc_lines:
        print(f"  {line}")


# ---------------------------------------------------------------------------
# Demo 4: Export OpenAI function-calling schema and MCP tool schema
# ---------------------------------------------------------------------------


def demo_schema_export() -> None:
    """Convert a ToolSpec to OpenAI function schema and MCP tool definition."""
    print("\n--- Demo 4: Schema Export (OpenAI and MCP) ---")

    generator = ToolGenerator()

    spec = ToolSpec(
        name="send_email",
        description="Send an email to one or more recipients.",
        parameters=[
            {"name": "to", "type": "str", "description": "Recipient email address.", "required": True},
            {"name": "subject", "type": "str", "description": "Email subject line.", "required": True},
            {"name": "body", "type": "str", "description": "Email body text.", "required": True},
            {"name": "cc", "type": "str", "description": "CC address (optional).", "required": False},
        ],
        returns={"type": "bool", "description": "True if the email was sent successfully."},
    )

    openai_schema: dict[str, object] = generator.generate_openai_schema(spec)
    mcp_schema: dict[str, object] = generator.generate_mcp_schema(spec)

    # OpenAI schema
    function_def = openai_schema.get("function", {})
    assert isinstance(function_def, dict)
    parameters_def = function_def.get("parameters", {})
    assert isinstance(parameters_def, dict)
    print("OpenAI schema:")
    print(f"  type            : {openai_schema['type']}")
    print(f"  function.name   : {function_def['name']}")
    print(f"  required fields : {parameters_def.get('required')}")

    # MCP schema
    input_schema = mcp_schema.get("inputSchema", {})
    assert isinstance(input_schema, dict)
    print("\nMCP schema:")
    print(f"  name     : {mcp_schema['name']}")
    print(f"  required : {input_schema.get('required')}")
    print(f"  properties: {list(input_schema.get('properties', {}).keys())}")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Demo 5: Use a built-in template skeleton during generation
# ---------------------------------------------------------------------------


def demo_builtin_templates() -> None:
    """List available built-in templates and generate code using one."""
    print("\n--- Demo 5: Built-in Templates ---")

    print(f"Available template IDs: {list(BUILT_IN_TEMPLATES.keys())}")

    # Use the 'search_tool' template
    template: ToolTemplate = BUILT_IN_TEMPLATES["search_tool"]
    print(f"\nTemplate: '{template.name}'")
    print(f"Description: {template.description}")

    spec = ToolSpec(
        name="search_documents",
        description="Search a corpus of documents for a query string.",
        parameters=[
            {"name": "query", "type": "str", "description": "The search query.", "required": True},
            {"name": "corpus", "type": "list", "description": "List of document strings.", "required": True},
            {"name": "limit", "type": "int", "description": "Maximum results to return.", "required": False},
        ],
        returns={"type": "list", "description": "Matching document strings."},
    )

    generator = ToolGenerator()
    generated = generator.generate(spec, template=template)

    print("\nTemplate-based source_code:")
    for line in generated.source_code.splitlines():
        print(f"  {line}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run all aumai-toolsmith quickstart demos."""
    print("=== aumai-toolsmith Quickstart ===")

    demo_spec_from_description()
    demo_spec_from_examples()
    demo_generate_tool()
    demo_schema_export()
    demo_builtin_templates()

    print("\nAll demos completed successfully.")


if __name__ == "__main__":
    main()
