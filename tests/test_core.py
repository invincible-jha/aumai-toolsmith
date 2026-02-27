"""Comprehensive tests for aumai-toolsmith core module."""

from __future__ import annotations

import pytest

from aumai_toolsmith.core import BUILT_IN_TEMPLATES, ToolGenerator, ToolSpecBuilder
from aumai_toolsmith.models import GeneratedTool, ToolSpec, ToolTemplate


# ---------------------------------------------------------------------------
# ToolSpecBuilder tests
# ---------------------------------------------------------------------------


class TestToolSpecBuilder:
    """Tests for ToolSpecBuilder."""

    def test_from_description_returns_tool_spec(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_description() returns a ToolSpec instance."""
        spec = builder.from_description("Fetch weather data for a location")
        assert isinstance(spec, ToolSpec)

    def test_from_description_extracts_name(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_description() creates a snake_case function name."""
        spec = builder.from_description("Fetch weather data for location reports")
        assert "_" in spec.name or spec.name.islower()
        assert spec.name != ""

    def test_from_description_default_query_parameter(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_description() adds a 'query' parameter when none can be inferred."""
        spec = builder.from_description("Do something useful")
        param_names = [p.get("name") for p in spec.parameters]
        assert "query" in param_names

    def test_from_description_extracts_given_parameter(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_description() extracts parameter from 'given X' pattern."""
        spec = builder.from_description("Search documents given a keyword and filter")
        param_names = [p.get("name") for p in spec.parameters]
        assert "keyword" in param_names

    def test_from_description_extracts_with_parameter(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_description() extracts parameter from 'with X' pattern."""
        spec = builder.from_description("Connect to database with credentials")
        param_names = [p.get("name") for p in spec.parameters]
        assert "credentials" in param_names

    def test_from_description_list_return_type(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_description() infers list return type from keywords."""
        spec = builder.from_description("Return a list of matching results")
        assert spec.returns.get("type") == "list"

    def test_from_description_dict_return_type(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_description() infers dict return type from keywords."""
        spec = builder.from_description("Return a JSON object with data fields")
        assert spec.returns.get("type") == "dict"

    def test_from_description_bool_return_type(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_description() infers bool return type from check/verify keywords."""
        spec = builder.from_description("Verify whether the connection is active")
        assert spec.returns.get("type") == "bool"

    def test_from_description_str_default_return_type(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_description() defaults to str return type."""
        spec = builder.from_description("Format the output for display")
        assert spec.returns.get("type") == "str"

    def test_from_description_stores_original_text(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_description() stores the original description in ToolSpec."""
        description = "A custom tool that does something interesting"
        spec = builder.from_description(description)
        assert spec.description == description

    def test_from_example_returns_tool_spec(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_example() returns a ToolSpec from input/output pairs."""
        pairs = [{"input": {"text": "hello"}, "output": "Hello!"}]
        spec = builder.from_example(pairs)
        assert isinstance(spec, ToolSpec)

    def test_from_example_name_is_inferred_tool(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_example() names the spec 'inferred_tool'."""
        pairs = [{"input": {"x": 1}, "output": 2}]
        spec = builder.from_example(pairs)
        assert spec.name == "inferred_tool"

    def test_from_example_infers_dict_parameters(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_example() infers parameter names from dict input."""
        pairs = [{"input": {"query": "test", "limit": 10}, "output": []}]
        spec = builder.from_example(pairs)
        param_names = [p.get("name") for p in spec.parameters]
        assert "query" in param_names
        assert "limit" in param_names

    def test_from_example_infers_scalar_parameter(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_example() handles non-dict input as single 'input' parameter."""
        pairs = [{"input": "hello", "output": "HELLO"}]
        spec = builder.from_example(pairs)
        assert spec.parameters[0]["name"] == "input"

    def test_from_example_infers_return_type(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_example() infers return type from first output value."""
        pairs = [{"input": {"x": 1}, "output": [1, 2, 3]}]
        spec = builder.from_example(pairs)
        assert spec.returns["type"] == "list"

    def test_from_example_stores_examples(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_example() stores the pairs as spec.examples."""
        pairs = [{"input": {"a": 1}, "output": 2}]
        spec = builder.from_example(pairs)
        assert spec.examples == pairs

    def test_from_example_raises_on_empty_pairs(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_example() raises ValueError for empty pairs list."""
        with pytest.raises(ValueError, match="At least one"):
            builder.from_example([])

    def test_from_example_return_type_any_for_none_output(
        self, builder: ToolSpecBuilder
    ) -> None:
        """from_example() uses 'Any' return type when output is None."""
        pairs = [{"input": {"x": 1}, "output": None}]
        spec = builder.from_example(pairs)
        assert spec.returns["type"] == "Any"

    def test_extract_name_filters_stop_words(
        self, builder: ToolSpecBuilder
    ) -> None:
        """_extract_name() filters common stop words from the function name."""
        spec = builder.from_description("The tool that searches for information")
        # 'the', 'that', 'for' should be excluded
        assert "the" not in spec.name
        assert "that" not in spec.name


# ---------------------------------------------------------------------------
# ToolGenerator tests
# ---------------------------------------------------------------------------


class TestToolGenerator:
    """Tests for ToolGenerator."""

    def test_generate_returns_generated_tool(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate() returns a GeneratedTool instance."""
        tool = generator.generate(search_spec)
        assert isinstance(tool, GeneratedTool)

    def test_generate_source_contains_function_name(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate() source_code contains the function name."""
        tool = generator.generate(search_spec)
        assert "search_web" in tool.source_code

    def test_generate_source_contains_parameters(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate() source_code includes parameter names."""
        tool = generator.generate(search_spec)
        assert "query" in tool.source_code

    def test_generate_source_contains_return_type(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate() source_code includes the return type annotation."""
        tool = generator.generate(search_spec)
        assert "list" in tool.source_code

    def test_generate_with_template(
        self,
        generator: ToolGenerator,
        search_spec: ToolSpec,
        http_template: ToolTemplate,
    ) -> None:
        """generate() with template substitutes name and params."""
        tool = generator.generate(search_spec, template=http_template)
        assert "search_web" in tool.source_code

    def test_generate_test_code_contains_function(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate() test_code includes a test function for the spec name."""
        tool = generator.generate(search_spec)
        assert "test_search_web" in tool.test_code

    def test_generate_test_code_contains_import(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate() test_code contains an import statement."""
        tool = generator.generate(search_spec)
        assert "import" in tool.test_code

    def test_generate_documentation_contains_header(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate() documentation starts with a markdown header."""
        tool = generator.generate(search_spec)
        assert tool.documentation.startswith("#")

    def test_generate_documentation_contains_parameters_section(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate() documentation includes a Parameters section."""
        tool = generator.generate(search_spec)
        assert "## Parameters" in tool.documentation

    def test_generate_documentation_contains_returns_section(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate() documentation includes a Returns section."""
        tool = generator.generate(search_spec)
        assert "## Returns" in tool.documentation

    def test_generate_documentation_includes_examples(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate() documentation includes Examples section when examples exist."""
        tool = generator.generate(search_spec)
        assert "## Examples" in tool.documentation

    def test_generate_openai_schema_structure(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate_openai_schema() returns a properly structured OpenAI schema."""
        schema = generator.generate_openai_schema(search_spec)
        assert schema["type"] == "function"
        function_obj = schema["function"]
        assert isinstance(function_obj, dict)
        assert function_obj["name"] == "search_web"
        parameters = function_obj["parameters"]
        assert isinstance(parameters, dict)
        assert "properties" in parameters

    def test_generate_openai_schema_required_params(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate_openai_schema() marks required parameters correctly."""
        schema = generator.generate_openai_schema(search_spec)
        required = schema["function"]["parameters"]["required"]
        assert "query" in required

    def test_generate_openai_schema_type_mapping(
        self, generator: ToolGenerator
    ) -> None:
        """generate_openai_schema() maps Python types to JSON Schema types."""
        spec = ToolSpec(
            name="typed_tool",
            description="Tool with typed params",
            parameters=[
                {"name": "count", "type": "int", "description": "A count.", "required": True},
                {"name": "rate", "type": "float", "description": "A rate.", "required": True},
                {"name": "flag", "type": "bool", "description": "A flag.", "required": False},
            ],
            returns={"type": "str", "description": "Result."},
        )
        schema = generator.generate_openai_schema(spec)
        props = schema["function"]["parameters"]["properties"]
        assert props["count"]["type"] == "integer"
        assert props["rate"]["type"] == "number"
        assert props["flag"]["type"] == "boolean"

    def test_generate_mcp_schema_structure(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate_mcp_schema() returns a properly structured MCP schema."""
        schema = generator.generate_mcp_schema(search_spec)
        assert schema["name"] == "search_web"
        assert "inputSchema" in schema
        assert schema["inputSchema"]["type"] == "object"

    def test_generate_mcp_schema_required_params(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate_mcp_schema() marks required parameters correctly."""
        schema = generator.generate_mcp_schema(search_spec)
        required = schema["inputSchema"]["required"]
        assert "query" in required

    def test_generate_mcp_schema_description(
        self, generator: ToolGenerator, search_spec: ToolSpec
    ) -> None:
        """generate_mcp_schema() includes the tool description."""
        schema = generator.generate_mcp_schema(search_spec)
        assert schema["description"] == search_spec.description


# ---------------------------------------------------------------------------
# BUILT_IN_TEMPLATES tests
# ---------------------------------------------------------------------------


class TestBuiltInTemplates:
    """Tests for the BUILT_IN_TEMPLATES dict."""

    def test_templates_exist(self) -> None:
        """All four expected built-in templates exist."""
        expected = {"http_tool", "file_tool", "database_tool", "search_tool"}
        assert set(BUILT_IN_TEMPLATES.keys()) == expected

    def test_template_has_skeleton(self) -> None:
        """Each template has a non-empty skeleton string."""
        for template_id, template in BUILT_IN_TEMPLATES.items():
            assert template.skeleton != "", f"Template '{template_id}' has empty skeleton"

    def test_template_ids_match_keys(self) -> None:
        """Each template's template_id matches its dict key."""
        for key, template in BUILT_IN_TEMPLATES.items():
            assert template.template_id == key
