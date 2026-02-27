# API Reference — aumai-toolsmith

Complete documentation for all public classes, functions, constants, and Pydantic
models in `aumai_toolsmith`.

---

## Module: `aumai_toolsmith.core`

Public exports: `ToolSpecBuilder`, `ToolGenerator`, `BUILT_IN_TEMPLATES`

---

### `BUILT_IN_TEMPLATES`

```python
BUILT_IN_TEMPLATES: dict[str, ToolTemplate]
```

Module-level constant. A dictionary of pre-built `ToolTemplate` objects, keyed
by `template_id`. These templates provide complete, runnable Python function
skeletons for common tool categories.

| Key | `template_id` | Description |
|---|---|---|
| `"http_tool"` | `http_tool` | Makes HTTP requests using `urllib.request`. |
| `"file_tool"` | `file_tool` | Reads files using `pathlib.Path`. |
| `"database_tool"` | `database_tool` | Queries SQLite with parameterized SQL. |
| `"search_tool"` | `search_tool` | Filters a list by case-insensitive substring match. |

**Template skeletons use these `{placeholders}`:**

| Placeholder | Filled by `ToolGenerator` | Filled manually |
|---|---|---|
| `{name}` | Yes — `spec.name` | — |
| `{params}` | Yes — `"param: type, ..."` | — |
| `{return_type}` | Yes — `spec.returns["type"]` | — |
| `{description}` | Yes — `spec.description` | — |
| `{url_param}`, `{path_param}`, etc. | No | Developer fills in |

**Example:**

```python
from aumai_toolsmith.core import BUILT_IN_TEMPLATES

for tid, template in BUILT_IN_TEMPLATES.items():
    print(f"{tid}: {template.description}")

template = BUILT_IN_TEMPLATES["http_tool"]
print(template.skeleton)
```

---

### `class ToolSpecBuilder`

Build `ToolSpec` objects from natural language descriptions or input/output examples.
No external dependencies or ML models are used — this is pure pattern matching.

```python
from aumai_toolsmith.core import ToolSpecBuilder
```

---

#### `ToolSpecBuilder.from_description(description: str) -> ToolSpec`

Parse a natural language description into a structured `ToolSpec`.

Extracts a function name, parameters, and return type using regex patterns.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `description` | `str` | Natural language description of the tool's purpose. |

**Returns:** `ToolSpec` with:

- `name`: snake_case name extracted from first meaningful words.
- `description`: the original `description` string.
- `parameters`: list of inferred parameter dicts.
- `returns`: inferred return type dict.

**Name extraction:** Takes the first 5 words that are not stop words
(`a`, `an`, `the`, `that`, `this`, `for`, `to`, `and`, `or`, `with`),
lowercases them, joins with underscores, and truncates to 50 characters.
Falls back to `"unnamed_tool"` if the result is empty.

**Parameter extraction:** Scans for these regex patterns (case-insensitive):
- `(?:given|with|for|accepts?|takes?)\s+(?:a\s+)?(\w+)`
- `(\w+)\s+parameter`
- `input\s+(\w+)`

Each unique match becomes a parameter with `type="str"` and `required=True`.
If no matches are found, a single default `query: str` parameter is added.

**Return type heuristics:**

| Keywords in description | Inferred type |
|---|---|
| `list`, `array`, `multiple` | `list` |
| `dict`, `object`, `json` | `dict` |
| `bool`, `whether`, `check`, `verify` | `bool` |
| (none of the above) | `str` |

**Example:**

```python
builder = ToolSpecBuilder()
spec = builder.from_description(
    "search a list of documents for a query string and return matching items"
)
print(spec.name)        # "search_list_documents_query"
print(spec.parameters)  # [{"name": "query", "type": "str", ...}]
print(spec.returns)     # {"type": "list", "description": "List of results."}
```

---

#### `ToolSpecBuilder.from_example(input_output_pairs: list[dict[str, object]]) -> ToolSpec`

Infer a `ToolSpec` from a list of input/output example pairs.

Each pair must have an `"input"` key and an `"output"` key. The spec's name
defaults to `"inferred_tool"`. Parameter names and types are inferred from
the first example's input.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `input_output_pairs` | `list[dict[str, object]]` | List of `{"input": ..., "output": ...}` dicts. Must be non-empty. |

**Returns:** `ToolSpec` with:

- `name`: `"inferred_tool"`
- `description`: `"Tool inferred from input/output examples."`
- `parameters`: inferred from the first pair's `"input"` value.
  - If `input` is a `dict`: one parameter per key, with Python type names.
  - Otherwise: a single `input` parameter with the type of the first value.
- `returns`: `{"type": type(output).__name__, "description": "Result of the tool operation."}`.
- `examples`: the original `input_output_pairs` list.

**Raises:**

- `ValueError` — if `input_output_pairs` is empty.

**Example:**

```python
spec = builder.from_example([
    {"input": {"text": "Hello world", "lang": "en"}, "output": "Hola mundo"},
    {"input": {"text": "Good morning", "lang": "es"}, "output": "Buenos días"},
])
print(spec.name)        # "inferred_tool"
print(spec.parameters)
# [{"name": "text", "type": "str", "description": "Input parameter 'text'.", "required": True},
#  {"name": "lang", "type": "str", "description": "Input parameter 'lang'.", "required": True}]
print(spec.returns)     # {"type": "str", "description": "Result of the tool operation."}
```

---

### `class ToolGenerator`

Generate Python source code, pytest tests, Markdown documentation, and JSON schemas
from a `ToolSpec`.

```python
from aumai_toolsmith.core import ToolGenerator
```

---

#### `ToolGenerator.generate(spec: ToolSpec, template: ToolTemplate | None = None) -> GeneratedTool`

Generate a complete tool implementation from a spec.

Calls `_generate_source()`, `_generate_tests()`, and `_generate_docs()` internally
and bundles the results into a `GeneratedTool`.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `spec` | `ToolSpec` | — (required) | The tool specification to generate from. |
| `template` | `ToolTemplate \| None` | `None` | Optional built-in template to use as the code skeleton. |

**Returns:** `GeneratedTool` with `source_code`, `test_code`, and `documentation` fields.

**Without template:** Generates a function with proper type hints, docstring, Args
section, Returns section, and `raise NotImplementedError` body.

**With template:** Performs string substitution on the template's `skeleton`,
replacing `{name}`, `{params}`, `{return_type}`, and `{description}`. Other
placeholders remain for manual completion.

**Example:**

```python
from aumai_toolsmith.core import BUILT_IN_TEMPLATES, ToolGenerator, ToolSpecBuilder

builder = ToolSpecBuilder()
generator = ToolGenerator()

spec = builder.from_description("fetch JSON from a URL given a url string")
tool = generator.generate(spec, template=BUILT_IN_TEMPLATES["http_tool"])

print(tool.source_code)
print(tool.test_code)
print(tool.documentation)
```

---

#### `ToolGenerator.generate_openai_schema(spec: ToolSpec) -> dict[str, object]`

Generate an OpenAI function-calling schema from a `ToolSpec`.

Maps Python type names to JSON Schema types and builds the exact structure
expected by OpenAI's Chat Completions API with `tools`.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `spec` | `ToolSpec` | The tool specification. |

**Returns:** `dict[str, object]` — OpenAI-compatible function schema.

**Python → JSON Schema type mapping:**

| Python type | JSON Schema type |
|---|---|
| `str` | `string` |
| `int` | `integer` |
| `float` | `number` |
| `bool` | `boolean` |
| `list` | `array` |
| `dict` | `object` |
| (other) | `string` |

**Output structure:**

```python
{
    "type": "function",
    "function": {
        "name": spec.name,
        "description": spec.description,
        "parameters": {
            "type": "object",
            "properties": {
                "<param_name>": {
                    "type": "<json_type>",
                    "description": "<param description>",
                }
                # ... one entry per parameter
            },
            "required": ["<param_name>", ...]  # only required=True params
        },
    },
}
```

**Example:**

```python
import json

spec = builder.from_description("translate text given a text and language")
schema = generator.generate_openai_schema(spec)
print(json.dumps(schema, indent=2))
```

---

#### `ToolGenerator.generate_mcp_schema(spec: ToolSpec) -> dict[str, object]`

Generate a Model Context Protocol (MCP) tool schema from a `ToolSpec`.

MCP is the protocol used by Claude and other systems that support standardized
tool definitions. The output uses `inputSchema` (camelCase) rather than
OpenAI's `parameters`.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `spec` | `ToolSpec` | The tool specification. |

**Returns:** `dict[str, object]` — MCP-compatible tool definition.

Uses the same Python → JSON Schema type mapping as `generate_openai_schema()`.

**Output structure:**

```python
{
    "name": spec.name,
    "description": spec.description,
    "inputSchema": {
        "type": "object",
        "properties": {
            "<param_name>": {
                "type": "<json_type>",
                "description": "<param description>",
            }
        },
        "required": ["<param_name>", ...]  # only required=True params
    },
}
```

**Example:**

```python
import json

mcp_schema = generator.generate_mcp_schema(spec)
print(json.dumps(mcp_schema, indent=2))
```

---

## Module: `aumai_toolsmith.models`

Public exports: `ToolSpec`, `GeneratedTool`, `ToolTemplate`

All models use Pydantic v2 (`BaseModel`).

---

### `class ToolSpec`

Specification for an AI tool function. The central data structure in ToolSmith.

```python
from aumai_toolsmith.models import ToolSpec
```

**Fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | — (required) | Python-safe function name, e.g. `"search_web"`, `"send_email"`. |
| `description` | `str` | — (required) | Human-readable description of what the tool does. |
| `parameters` | `list[dict[str, object]]` | `[]` | List of parameter descriptor dicts. |
| `returns` | `dict[str, object]` | `{}` | Return value descriptor with `"type"` and `"description"` keys. |
| `examples` | `list[dict[str, object]]` | `[]` | List of `{"input": ..., "output": ...}` example pairs. |

**Parameter dict structure:**

| Key | Type | Description |
|---|---|---|
| `"name"` | `str` | Python parameter name (used in function signature). |
| `"type"` | `str` | Python type name: `"str"`, `"int"`, `"float"`, `"bool"`, `"list"`, `"dict"`. |
| `"description"` | `str` | Human-readable description of the parameter. |
| `"required"` | `bool` | Whether the parameter is required. Affects schema `required` list. |

**Full example:**

```python
spec = ToolSpec(
    name="search_documents",
    description="Search a corpus for a query and return matching items.",
    parameters=[
        {
            "name": "query",
            "type": "str",
            "description": "The search query string.",
            "required": True,
        },
        {
            "name": "limit",
            "type": "int",
            "description": "Maximum number of results.",
            "required": True,
        },
    ],
    returns={
        "type": "list",
        "description": "List of matching document strings.",
    },
    examples=[
        {"input": {"query": "machine learning", "limit": 5}, "output": ["doc1.txt"]},
    ],
)
```

---

### `class GeneratedTool`

A tool generated from a `ToolSpec`. Bundles source code, tests, and documentation.

```python
from aumai_toolsmith.models import GeneratedTool
```

**Fields:**

| Field | Type | Description |
|---|---|---|
| `spec` | `ToolSpec` | The original specification the tool was generated from. |
| `source_code` | `str` | Runnable Python source code (function definition with docstring). |
| `test_code` | `str` | `pytest` test stub code. |
| `documentation` | `str` | Markdown documentation string. |

**Example:**

```python
from pathlib import Path

tool = generator.generate(spec)
Path("my_tool.py").write_text(tool.source_code, encoding="utf-8")
Path("test_my_tool.py").write_text(tool.test_code, encoding="utf-8")
Path("my_tool.md").write_text(tool.documentation, encoding="utf-8")
```

---

### `class ToolTemplate`

A reusable Python code skeleton for tool generation. Used by `ToolGenerator.generate()`
when a `template` argument is provided.

```python
from aumai_toolsmith.models import ToolTemplate
```

**Fields:**

| Field | Type | Description |
|---|---|---|
| `template_id` | `str` | Unique identifier (e.g. `"http_tool"`). Used as key in `BUILT_IN_TEMPLATES`. |
| `name` | `str` | Human-readable template name (e.g. `"HTTP Tool"`). |
| `description` | `str` | Short description of what the template is for. |
| `skeleton` | `str` | Python code skeleton with `{name}`, `{params}`, `{return_type}`, `{description}` placeholders. |

**Custom template example:**

```python
from aumai_toolsmith.models import ToolTemplate
from aumai_toolsmith.core import ToolGenerator, ToolSpecBuilder

my_template = ToolTemplate(
    template_id="redis_tool",
    name="Redis Tool",
    description="Connects to Redis and performs key/value operations.",
    skeleton=(
        "import redis\n\n"
        "def {name}({params}) -> {return_type}:\n"
        '    """{description}"""\n'
        "    client = redis.Redis(host='localhost', port=6379, decode_responses=True)\n"
        "    # TODO: implement Redis logic\n"
        "    raise NotImplementedError\n"
    ),
)

builder = ToolSpecBuilder()
generator = ToolGenerator()

spec = builder.from_description("get a value from Redis given a key string")
tool = generator.generate(spec, template=my_template)
print(tool.source_code)
```

---

## Module: `aumai_toolsmith.cli`

The CLI is accessed via the `toolsmith` command installed by the package.
All commands are built with [Click](https://click.palletsprojects.com/).

| Command | Description |
|---|---|
| `toolsmith create --description TEXT` | Parse a description, generate source + tests. |
| `toolsmith schema --spec PATH --format [openai\|mcp]` | Emit a function-calling schema from a ToolSpec file. |
| `toolsmith templates` | List all built-in templates. |

See the [README](../README.md) for full CLI usage examples with sample output.

---

## Package metadata

```python
import aumai_toolsmith
print(aumai_toolsmith.__version__)  # "0.1.0"
```
