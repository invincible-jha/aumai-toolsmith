# Getting Started with aumai-toolsmith

This guide walks you from a fresh install to generating working Python tool code,
tests, and schemas in under five minutes.

---

## Prerequisites

| Requirement | Minimum version | Notes |
|---|---|---|
| Python | 3.11 | Type hint features used throughout |
| pip | 23.0+ | |
| PyYAML | 6.0+ | Optional — needed for `toolsmith schema` with YAML spec files |

No LLM API keys or network access are required. ToolSmith's `ToolSpecBuilder` is
a pattern-matching engine that runs entirely locally.

---

## Installation

```bash
pip install aumai-toolsmith
```

With YAML support (for `toolsmith schema --spec file.yaml`):

```bash
pip install aumai-toolsmith pyyaml
```

Development install:

```bash
git clone https://github.com/aumai/aumai-toolsmith
cd aumai-toolsmith
pip install -e ".[dev]"
```

Verify the install:

```bash
toolsmith --version
# aumai-toolsmith, version 0.1.0

toolsmith --help
# Usage: toolsmith [OPTIONS] COMMAND [ARGS]...
#   AumAI ToolSmith — AI-assisted tool creation framework CLI.
# Commands:
#   create     Create a tool from a natural language description.
#   schema     Generate a function calling schema from a ToolSpec file.
#   templates  List available built-in tool templates.
```

---

## Step-by-Step Tutorial

### Step 1: List available templates

```bash
toolsmith templates
```

Output:

```
[http_tool]      HTTP Tool:      Tool that makes HTTP requests.
[file_tool]      File Tool:      Tool that reads or writes files.
[database_tool]  Database Tool:  Tool that queries a database using parameterized SQL.
[search_tool]    Search Tool:    Tool that searches a collection of documents.
```

Templates are pre-written Python skeletons. Using a template produces runnable
code immediately, rather than a `raise NotImplementedError` stub.

---

### Step 2: Generate a tool from a description

Generate a tool without a template (produces a stub with `NotImplementedError`):

```bash
toolsmith create \
  --description "search a list of documents for a query string and return matching items"
```

Expected output:

```
Generated tool: search_list_documents_query
--- Source Code ---
from __future__ import annotations

def search_list_documents_query(query: str) -> list:
    """search a list of documents for a query string and return matching items

    Args:
        query: The query input.

    Returns:
        List of results.
    """
    # TODO: implement tool logic
    raise NotImplementedError
```

Note how the return type was inferred as `list` because the description contains
the word "list".

---

### Step 3: Generate with a template and save to files

```bash
toolsmith create \
  --description "fetch JSON data from a URL given a url string" \
  --template http_tool \
  --output fetch_json.py
```

Output:

```
Generated tool: fetch_json_data_from
--- Source Code ---
import urllib.request
import json as _json
from typing import Any

def fetch_json_data_from(url: str) -> str:
    ...
Source saved to fetch_json.py
Tests saved to test_fetch_json.py
```

Inspect the generated test file:

```bash
cat test_fetch_json.py
```

```python
import pytest
from fetch_json_data_from_module import fetch_json_data_from


def test_fetch_json_data_from_basic() -> None:
    """Test basic invocation of fetch_json_data_from."""
    # TODO: provide real test inputs
    url = "test"
    result = fetch_json_data_from(url=url)
    assert result is not None
```

---

### Step 4: Generate a schema from a ToolSpec file

Create `search-tool.json`:

```json
{
  "name": "search_documents",
  "description": "Search a corpus of documents for a query and return matching items.",
  "parameters": [
    {
      "name": "query",
      "type": "str",
      "description": "The search query string.",
      "required": true
    },
    {
      "name": "limit",
      "type": "int",
      "description": "Maximum number of results to return.",
      "required": true
    }
  ],
  "returns": {
    "type": "list",
    "description": "List of matching documents."
  },
  "examples": []
}
```

Generate an OpenAI function-calling schema:

```bash
toolsmith schema --spec search-tool.json --format openai
```

```json
{
  "type": "function",
  "function": {
    "name": "search_documents",
    "description": "Search a corpus of documents for a query and return matching items.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The search query string."
        },
        "limit": {
          "type": "integer",
          "description": "Maximum number of results to return."
        }
      },
      "required": ["query", "limit"]
    }
  }
}
```

Generate an MCP schema:

```bash
toolsmith schema --spec search-tool.json --format mcp
```

---

### Step 5: Use the Python API

```python
from aumai_toolsmith.core import ToolGenerator, ToolSpecBuilder

builder = ToolSpecBuilder()
generator = ToolGenerator()

spec = builder.from_description(
    "verify whether a given email address is valid"
)
print(spec.name)        # verify_whether_given_email
print(spec.parameters)  # [{"name": "email", "type": "str", ...}]
print(spec.returns)     # {"type": "bool", "description": "True if successful..."}

tool = generator.generate(spec)
print(tool.source_code)
print("---")
print(tool.test_code)
print("---")
print(tool.documentation)
```

---

## Common Patterns and Recipes

### Pattern 1: Build a tool from input/output examples

When you have examples but no description, use `from_example()`:

```python
from aumai_toolsmith.core import ToolGenerator, ToolSpecBuilder

builder = ToolSpecBuilder()
generator = ToolGenerator()

spec = builder.from_example([
    {"input": {"text": "Hello world", "lang": "en"}, "output": "Hola mundo"},
    {"input": {"text": "Good morning", "lang": "es"}, "output": "Buenos días"},
])
print(spec.name)        # inferred_tool
print(spec.parameters)  # [{"name": "text", "type": "str"}, {"name": "lang", "type": "str"}]

tool = generator.generate(spec)
print(tool.source_code)
```

### Pattern 2: Create a tool with explicit ToolSpec (full control)

Bypass the builder entirely when you know exactly what you want:

```python
from aumai_toolsmith.core import ToolGenerator
from aumai_toolsmith.models import ToolSpec

spec = ToolSpec(
    name="send_notification",
    description="Send a push notification to a user device.",
    parameters=[
        {"name": "device_token", "type": "str", "description": "Device push token.", "required": True},
        {"name": "message", "type": "str", "description": "Notification body.", "required": True},
        {"name": "title", "type": "str", "description": "Notification title.", "required": False},
    ],
    returns={"type": "bool", "description": "True if delivered successfully."},
)

generator = ToolGenerator()
tool = generator.generate(spec)

# Write source and tests
from pathlib import Path
Path("send_notification.py").write_text(tool.source_code, encoding="utf-8")
Path("test_send_notification.py").write_text(tool.test_code, encoding="utf-8")
Path("send_notification.md").write_text(tool.documentation, encoding="utf-8")
```

### Pattern 3: Batch generate a set of related tools

```python
from aumai_toolsmith.core import ToolGenerator, ToolSpecBuilder
from pathlib import Path

builder = ToolSpecBuilder()
generator = ToolGenerator()

tool_descriptions = [
    "fetch JSON data from a URL given a url string",
    "search a list of items for a query and return matching results",
    "verify whether a given email address is valid",
    "calculate the total given a list of prices",
]

output_dir = Path("./generated_tools")
output_dir.mkdir(exist_ok=True)

for desc in tool_descriptions:
    spec = builder.from_description(desc)
    tool = generator.generate(spec)
    src_path = output_dir / f"{spec.name}.py"
    test_path = output_dir / f"test_{spec.name}.py"
    src_path.write_text(tool.source_code, encoding="utf-8")
    test_path.write_text(tool.test_code, encoding="utf-8")
    print(f"Generated: {spec.name}")
```

### Pattern 4: Produce schemas for multiple formats at once

```python
import json
from aumai_toolsmith.core import ToolGenerator, ToolSpecBuilder

builder = ToolSpecBuilder()
generator = ToolGenerator()

spec = builder.from_description("translate text from one language to another given a text and target language")
openai_schema = generator.generate_openai_schema(spec)
mcp_schema = generator.generate_mcp_schema(spec)

print("=== OpenAI ===")
print(json.dumps(openai_schema, indent=2))

print("=== MCP ===")
print(json.dumps(mcp_schema, indent=2))
```

### Pattern 5: Use a template with a manually constructed spec

```python
from aumai_toolsmith.core import BUILT_IN_TEMPLATES, ToolGenerator
from aumai_toolsmith.models import ToolSpec

spec = ToolSpec(
    name="query_users",
    description="Query the users table for a given username.",
    parameters=[
        {"name": "username", "type": "str", "description": "Username to look up.", "required": True},
    ],
    returns={"type": "list", "description": "List of matching user rows."},
)

template = BUILT_IN_TEMPLATES["database_tool"]
generator = ToolGenerator()
tool = generator.generate(spec, template=template)
print(tool.source_code)
```

---

## Troubleshooting FAQ

**Q: The generated function name looks wrong.**

`ToolSpecBuilder._extract_name()` takes the first five meaningful words from the
description, filters stop words, and joins with underscores. If the result is
unexpected, use `ToolSpec(name="my_custom_name", ...)` directly to specify the
exact name you want.

---

**Q: No parameters were detected from my description.**

The builder looks for patterns like `given X`, `with X`, `for X`, `accepts X`,
`takes X`, `X parameter`, `input X`. If none match, it falls back to a single
`query: str` parameter. Rewrite your description to include one of these patterns,
or construct a `ToolSpec` manually with explicit `parameters`.

---

**Q: The return type is `str` but I want `dict`.**

The heuristic checks for words like `dict`, `object`, or `json` in the description.
Add one of these words — or construct a `ToolSpec` directly with
`returns={"type": "dict", "description": "..."}`.

---

**Q: `toolsmith schema` says `ModuleNotFoundError: No module named 'yaml'`**

Install PyYAML: `pip install pyyaml`. Alternatively, save your spec as a `.json`
file — the CLI will parse it without PyYAML.

---

**Q: The template output contains unfilled `{placeholders}`.**

Built-in templates fill `{name}`, `{params}`, `{return_type}`, and `{description}`.
Other placeholders like `{url_param}`, `{path_param}`, `{db_param}` remain as-is
for you to replace manually. They serve as markers showing where you need to wire
in runtime values.

---

**Q: Can I add my own custom templates?**

Yes. Create a `ToolTemplate` object and pass it directly to `ToolGenerator.generate()`:

```python
from aumai_toolsmith.models import ToolTemplate

my_template = ToolTemplate(
    template_id="redis_tool",
    name="Redis Tool",
    description="Calls Redis via the redis-py client.",
    skeleton="import redis\n\ndef {name}({params}) -> {return_type}:\n    ...",
)
tool = generator.generate(spec, template=my_template)
```

---

## Next Steps

- Read the [API Reference](api-reference.md) for complete class documentation.
- Explore [examples/quickstart.py](../examples/quickstart.py) for runnable demos.
- Read about [aumai-skillforge](../../aumai-skillforge/README.md) to register
  generated tools as composable skills.
- Join the [AumAI Discord](https://discord.gg/aumai) for community support.
