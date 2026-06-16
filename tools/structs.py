from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class Tool:
    name: str
    description: str

    execution: Callable

    input_schema: dict | None = None
    output_schema: dict | None = None

@dataclass
class ToolCall:
    name: str
    arguments: dict

@dataclass
class ToolResult:
    result: Any
    error: str | None = None

