"""
Teste unitário para verificar o formato de tool calling do Ollama.
Valida que as tools estão sendo formatadas corretamente.
"""

from src.domain.value_objects.base_tools import BaseTool
from src.infra.adapters.Ollama.ollama_tool_schema_formatter import (
    OllamaToolSchemaFormatter,
)


class MockTool(BaseTool):
    """Tool de teste."""

    name = "mock_tool"
    description = "A mock tool for testing"
    parameters = {
        "type": "object",
        "properties": {"param1": {"type": "string", "description": "First parameter"}},
        "required": ["param1"],
    }

    def execute(self, param1: str) -> str:
        return f"Executed with {param1}"


def test_format_single_tool():
    """Testa formatação de uma única tool."""
    tool = MockTool()
    formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([tool])

    assert len(formatted) == 1
    assert formatted[0]["type"] == "function"
    assert formatted[0]["function"]["name"] == "mock_tool"
    assert formatted[0]["function"]["description"] == "A mock tool for testing"
    assert "parameters" in formatted[0]["function"]


def test_format_multiple_tools():
    """Testa formatação de múltiplas tools."""

    class Tool1(BaseTool):
        name = "tool1"
        description = "First tool"
        parameters = {"type": "object", "properties": {}}

        def execute(self):
            pass

    class Tool2(BaseTool):
        name = "tool2"
        description = "Second tool"
        parameters = {"type": "object", "properties": {}}

        def execute(self):
            pass

    tools = [Tool1(), Tool2()]
    formatted = OllamaToolSchemaFormatter.format_tools_for_ollama(tools)

    assert len(formatted) == 2
    assert formatted[0]["function"]["name"] == "tool1"
    assert formatted[1]["function"]["name"] == "tool2"


def test_format_empty_tools_list():
    """Testa formatação de lista vazia."""
    formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([])
    assert formatted == []


def test_tool_schema_structure():
    """Testa que a estrutura do schema está correta para Ollama."""
    tool = MockTool()
    formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([tool])

    expected_structure = {
        "type": "function",
        "function": {
            "name": "mock_tool",
            "description": "A mock tool for testing",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "First parameter"}
                },
                "required": ["param1"],
            },
        },
    }

    assert formatted[0] == expected_structure


def test_tool_parameters_preserved():
    """Testa que os parâmetros da tool são preservados corretamente."""
    tool = MockTool()
    formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([tool])

    params = formatted[0]["function"]["parameters"]
    assert params["type"] == "object"
    assert "param1" in params["properties"]
    assert params["properties"]["param1"]["type"] == "string"
    assert "required" in params
    assert "param1" in params["required"]


if __name__ == "__main__":
    # Executar testes manualmente
    print("Executando testes de formatação de tools do Ollama...\n")

    try:
        test_format_single_tool()
        print("✅ test_format_single_tool - PASSOU")

        test_format_multiple_tools()
        print("✅ test_format_multiple_tools - PASSOU")

        test_format_empty_tools_list()
        print("✅ test_format_empty_tools_list - PASSOU")

        test_tool_schema_structure()
        print("✅ test_tool_schema_structure - PASSOU")

        test_tool_parameters_preserved()
        print("✅ test_tool_parameters_preserved - PASSOU")

        print("\n" + "=" * 60)
        print("TODOS OS TESTES PASSARAM! ✨")
        print("=" * 60)
        print("\n✅ A formatação de tools do Ollama está correta!")
        print("✅ Estrutura compatível com a API nativa da Ollama")
        print("✅ Similar ao formato do OpenAI")

    except AssertionError as e:
        print(f"\n❌ FALHA: {e}")
        import traceback

        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback

        traceback.print_exc()
