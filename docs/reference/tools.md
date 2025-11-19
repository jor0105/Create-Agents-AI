# 🛠️ Referência Técnica de Ferramentas

> Guia completo sobre as ferramentas (tools) integradas e customizadas do **Create Agents AI**.

---

## 🔹 Ferramentas Built-in

### CurrentDateTool

- **Nome:** `currentdate`
- **Função:** Obtém data/hora em qualquer timezone
- **Disponibilidade:** Sempre disponível (não requer dependências extras)

**Exemplo de uso:**

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["currentdate"]
)
response = agent.chat("Que dia é hoje?")
print(response)
```

---

### ReadLocalFileTool

- **Nome:** `readlocalfile`
- **Função:** Lê arquivos TXT, PDF, Excel, CSV, Parquet, JSON, YAML
- **Requer:** `poetry install -E file-tools`
- **Limite:** 100MB por arquivo

**Exemplo de uso:**

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["readlocalfile"]
)
response = agent.chat("Leia o arquivo relatorio.pdf e resuma")
print(response)
```

---

## 🧩 Como Criar Ferramentas Customizadas

Você pode estender o sistema criando suas próprias ferramentas (tools) para qualquer finalidade.

```python
from createagents import BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Realiza cálculos matemáticos"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Expressão matemática"
            }
        },
        "required": ["expression"]
    }

    def execute(self, expression: str) -> str:
        """Executa o cálculo matemático informado."""
        try:
            return str(eval(expression))
        except Exception as e:
            return f"Erro: {e}"
```

**Como adicionar ao agente:**

```python
agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["currentdate", CalculatorTool()]
)
```

---

## ✅ Checklist de Instalação

- Instalação básica:
  ```bash
  poetry install
  ```
- Com file-tools (para leitura de arquivos):
  ```bash
  poetry install -E file-tools
  ```

---

## 🔍 Verificando Ferramentas Disponíveis

Veja como listar todas as ferramentas disponíveis para um agente:

```python
all_tools = agent.get_all_available_tools()  # Todas (sistema + customizadas)
print(list(all_tools.keys()))

system_tools = agent.get_system_available_tools()  # Apenas built-in
print(list(system_tools.keys()))
```

---

## 🧑‍💻 FAQ Técnico

**Como evitar duplicatas?**

O sistema gerencia automaticamente. Se você adicionar uma ferramenta do sistema explicitamente, ela aparecerá apenas uma vez.

**Como tratar erros ao executar tools?**

Use sempre try/except ao chamar métodos de execução de ferramentas customizadas:

```python
try:
    result = agent.chat("Calcule: 2+2")
    print(result)
except Exception as e:
    print(f"Erro ao executar ferramenta: {e}")
```

---

## 🔗 Links Relacionados

- [API Reference](../api.md)
- [Guia do Usuário](../user-guide/installation-user.md)
- [Guia do Desenvolvedor](../dev-guide/architecture-developer.md)

---

**Versão:** 0.1.0 | **Atualização:** 19/11/2025
