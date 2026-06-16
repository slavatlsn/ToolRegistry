# ToolRegistry – Абстрактный фреймворк для управления инструментами AI-агентов

`ToolRegistry` — это легковесное, гибкое ядро для регистрации, компиляции и вызова инструментов в системах на основе больших языковых моделей (LLM). 

---

## Быстрый старт

### 1. Регистрация инструментов

Используйте декоратор `@registry.tool`, чтобы зарегистрировать функцию. 

```python
from tools.registry import ToolRegistry

registry = ToolRegistry()

@registry.tool(description="Складывает два числа")
def add(a: float, b: float) -> float:
    return a + b

@registry.tool(description="Умножает два числа")
def multiply(a: float, b: float) -> float:
    return a * b
```

### 2. Компиляция инструментов для вашей LLM

Библиотека не поставляется со «встроенным» компилятором для конкретного API. В папке [`examples/`](./examples) лежит демонстрационный `OllamaCompiler`, который показывает, как адаптировать инструменты под формат function calling конкретного провайдера.

Вы можете взять этот пример за основу или написать свой компилятор с нуля:

```python
# Это пример из папки examples/
from examples.ollama_compiler import OllamaCompiler

compiler = OllamaCompiler()
tools_for_llm = registry.tools(compiler)  # Вернёт инструменты в нужном формате
```

Если при компиляции возникнут ошибки (например, невалидная схема), метод `registry.tools()` выбросит исключение с подробным описанием.

### 3. Вызов инструментов

Получив от модели список `tool_calls`, выполните их с помощью `registry.call()`:

```python
from tools.structs import ToolCall

# пример ответа модели
tool_calls = [
    {"name": "add", "arguments": {"a": 2, "b": 3}}
]

for call_data in tool_calls:
    call = ToolCall(name=call_data["name"], arguments=call_data["arguments"])
    result = registry.call(call)
    if result.error:
        print(f"Ошибка: {result.error}")
    else:
        print(f"Результат: {result.result}")
```

---

## Ручное управление схемами

Если вы хотите полностью контролировать входную или выходную схему (например, добавить описание полей, ограничения или сложные вложенные объекты), передайте их явно в декоратор. 

**Важно:** Если вы передали `input_schema` вручную, автоматическая генерация из аннотаций типов **не производится**. Компилятор просто использует то, что вы дали. При реализации собственных компиляторов учитывайте эту особенность.

```python
@registry.tool(
    description="Поиск книг по автору и году",
    input_schema={
        "type": "object",
        "properties": {
            "author": {"type": "string", "description": "Имя автора"},
            "year": {"type": "integer", "minimum": 1900, "maximum": 2025}
        },
        "required": ["author"]
    },
    output_schema={
        "type": "array",
        "items": {"type": "string"}
    }
)
def find_books(author: str, year: int = None) -> list[str]:
    # реализация ...
    return ["Book1", "Book2"]
```

---

## Создание собственного компилятора

Поскольку `examples/ollama_compiler.py` — это лишь демонстрация, для продакшена или других моделей (OpenAI, Anthropic Claude, Google Gemini и т.д.) вам нужно будет реализовать свой компилятор, унаследовавшись от абстрактного класса `ToolCompiler`.

Это дает полную свободу: вы можете генерировать JSON‑схемы, XML‑описания или плоские строки — всё, что поймет ваша модель.

```python
from tools.compiler import ToolCompiler
from tools.structs import Tool

class MyCustomCompiler(ToolCompiler):
    def compile(self, tool: Tool) -> dict:
        # 1. Берем схему из tool.input_schema (если есть)
        # 2. Или строим свою через introspection (как в примере)
        # 3. Возвращаем dict в формате вашего API
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema or self._build_schema(tool.execution)
        }

    def validate(self, compiled_tool: dict) -> str | None:
        # Необязательная проверка. Если что-то не так — возвращаем строку ошибки.
        # В примере этот метод проверяет наличие обязательных полей.
        if "name" not in compiled_tool:
            return "Missing name"
        return None
```

---

## Полный цикл работы с LLM

Ниже показан базовый сценарий: агент общается с моделью, использует инструменты и обрабатывает ответы. Обратите внимание, что компилятор здесь — пример из `examples/`.

```python
from tools.registry import ToolRegistry
from tools.structs import ToolCall
# Импортируем пример компилятора из папки examples
from examples.ollama_compiler import OllamaCompiler

# 1. Инициализация
compiler = OllamaCompiler()  # Это пример!
registry = ToolRegistry()

# 2. Регистрация инструментов
@registry.tool(description="Складывает два числа")
def add(a: float, b: float) -> float:
    return a + b

# 3. Компиляция для модели (используем пример)
tools_schema = registry.tools(compiler)

# 4. Цикл взаимодействия (гипотетический клиент)
messages = [{"role": "system", "content": "Ты — ассистент с калькулятором."}]

while True:
    user_input = input(">>> ")
    messages.append({"role": "user", "content": user_input})

    # 5. Запрос к модели, здесь вы можете использовать любую вашу модель, передавая параметры tools как требуется
    response = client.chat_with_messages(
        messages=messages,
        tools=tools_schema
    )

    # 6. Обработка вызовов инструментов
    for call_data in response.get("tool_calls", []):
        call = ToolCall(call_data["name"], call_data["arguments"])
        result = registry.call(call)
        messages.append({
            "role": "tool",
            "content": str(result.result) if not result.error else f"Ошибка: {result.error}",
            "name": call.name
        })

    # 7. Финальный ответ
    if response.get("response") and not response.get("tool_calls"):
        print("Ответ:", response["response"])
        break
```

---

## 📂 Структура проекта

```
.
├── tools/
│   ├── structs.py          # Dataclass'ы: Tool, ToolCall, ToolResult
│   ├── compiler.py         # Абстрактный базовый класс ToolCompiler
│   └── registry.py         # ToolRegistry и ToolStorage (ядро)
└── examples/               # Папка с примерами использования
    └── ollama_compiler.py  # Демо-компилятор в формат Ollama/OpenAI
```

---

## 📄 Лицензия

Проект распространяется под лицензией **MIT**. Вы можете свободно использовать, модифицировать и распространять код в любых целях.

---

## 🤝 Внесение вклада

Если вы написали крутой компилятор для Anthropic, Gemini или DeepSeek — присылайте его в папку `examples/` через Pull Request! Мы рады любым улучшениям и примерам интеграций.
