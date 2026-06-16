from tools.structs import *
from tools.compiler import ToolCompiler
from typing import List
from traceback import format_exc


class ToolStorage:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def add(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(
                f"Tool '{tool.name}' already registered"
            )

        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def remove(self, name: str):
        del self._tools[name]

    def list(self) -> list[str]:
        return list(self._tools.keys())

    def all(self):
        return self._tools.values()

    def __len__(self):
        return len(self._tools)

    def __contains__(self, name: str):
        return name in self._tools

from tools.structs import Tool, ToolCall, ToolResult


class ToolRegistry:
    def __init__(self):
        self._storage: ToolStorage = ToolStorage()

    def tool(self, description: str, input_schema: dict = None, output_schema: dict = None):

        def decorator(func):

            tool = Tool(
                name=func.__name__,
                description=description,
                execution=func,
                input_schema=input_schema,
                output_schema=output_schema
            )

            self._storage.add(tool)

            return func

        return decorator

    def call(self, call: ToolCall) -> ToolResult:
        if call.name not in self._storage:
            return ToolResult(
                result=None,
                error=f"Tool '{call.name}' not found"
            )

        tool = self._storage.get(call.name)

        try:
            result = tool.execution(**call.arguments)
            return ToolResult(result=result)

        except Exception as e:
            return ToolResult(result=None, error=f"{str(e)}\n\n{format_exc()}")

    def list(self) -> List[str]:
        return self._storage.list()

    def tools(self, compiler: ToolCompiler) -> List[dict]:
        compiled = compiler.test_and_compile(self._storage.all())
        if len(compiled['errors']) > 0:
            beautiful = "\n".join([f"{name}: {error}" for name, error in compiled["errors"].items()])
            raise RuntimeError(f'Compilation failed\n{beautiful}')
        else:
            return compiled['tools']