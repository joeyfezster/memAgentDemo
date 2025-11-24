from typing import Any, Protocol


class Tool(Protocol):
    name: str
    description: str

    def get_input_schema(self) -> dict:
        """Return JSON schema for tool inputs compatible with Anthropic's format"""
        ...

    async def execute(self, **kwargs: Any) -> dict:
        """Execute tool and return results as a dictionary"""
        ...


def to_anthropic_schema(tool: Tool) -> dict:
    """
    Convert a Tool to Anthropic's tool definition format.
    """
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.get_input_schema(),
    }


class ToolRegistry:
    """Registry for managing available tools"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool by its name"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Get a tool by name, returns None if not found"""
        return self._tools.get(name)

    def get_anthropic_schemas(self) -> list[dict]:
        """Get all tool schemas in Anthropic's format"""
        return [to_anthropic_schema(tool) for tool in self._tools.values()]

    async def execute(self, name: str, **kwargs: Any) -> dict:
        """Execute a tool by name with the provided arguments"""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found in registry")
        return await tool.execute(**kwargs)
