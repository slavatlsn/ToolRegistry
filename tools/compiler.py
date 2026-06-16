from abc import ABC, abstractmethod
from tools.structs import Tool
from typing import Optional, Iterable, Any
from traceback import format_exc
import json


class ToolCompiler(ABC):

    @abstractmethod
    def compile(self, tool: Tool) -> dict:
        pass

    def validate(self, compiled_tool: dict) -> Optional[str]:
        """
        Returns:
            errors: [Строковое описание ошибки или None]"""
        return None

    def test_and_compile(self, tools: Iterable[Tool]) -> dict[str, Any]:
        """
        Returns:
            compiled_tools: скомпилированные инструменты в случае успеха
            errors: {[имя_инструмента]: [ошибка компиляции]}
        """

        compiled_tools = []
        errors = {}

        for tool in tools:

            try:
                compiled = self.compile(tool)

                if not isinstance(compiled, dict):
                    raise TypeError(
                        f"compile() returned {type(compiled).__name__}, expected dict"
                    )

                if not compiled:
                    raise ValueError("compile() returned empty dict")

                json.dumps(compiled)
                error = self.validate(compiled)
                if error is not None:
                    errors[tool.name] = error
                else:
                    compiled_tools.append(compiled)

            except Exception as e:
                errors[tool.name] = f"{str(e)}\n\n{format_exc()}"

        return {'tools': compiled_tools, 'errors': errors}