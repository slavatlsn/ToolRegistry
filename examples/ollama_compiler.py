from tools.compiler import ToolCompiler
from tools.structs import Tool
from inspect import signature
from typing import get_origin, get_args

def python_type_to_json_schema(tp):
    if tp == int:
        return {"type": "integer"}

    if tp == float:
        return {"type": "number"}

    if tp == str:
        return {"type": "string"}

    if tp == bool:
        return {"type": "boolean"}

    origin = get_origin(tp)

    if origin == list:
        item_type = get_args(tp)[0]
        return {
            "type": "array",
            "items": python_type_to_json_schema(item_type)
        }

    if origin == dict:
        key_type, value_type = get_args(tp)

        if key_type != str:
            raise TypeError("JSON object keys must be str")

        return {
            "type": "object",
            "additionalProperties": python_type_to_json_schema(value_type)
        }

    return {}

def build_input_schema(func):
    sig = signature(func)

    properties = {}
    required = []

    for name, param in sig.parameters.items():

        annotation = param.annotation

        schema = python_type_to_json_schema(annotation)

        properties[name] = schema

        if param.default is param.empty:
            required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


class OllamaCompiler(ToolCompiler):

    def compile(self, tool: Tool) -> dict:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema if tool.input_schema is not None else build_input_schema(tool.execution),
            }
        }

    def validate(self, compiled_tool: dict) -> str | None:

        if compiled_tool.get("type") != "function":
            return "Missing or invalid 'type' field"

        function = compiled_tool.get("function")

        if not isinstance(function, dict):
            return "Missing 'function' object"

        required = [
            "name",
            "description",
            "parameters"
        ]

        for field in required:
            if field not in function:
                return f"Missing function.{field}"

        parameters = function["parameters"]

        if not isinstance(parameters, dict):
            return "function.parameters must be dict"

        return None
