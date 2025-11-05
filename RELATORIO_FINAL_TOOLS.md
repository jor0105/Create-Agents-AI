# Resumo do Projeto: Sistema de Ferramentas para Agente de IA

## Objetivo Geral

Desenvolver um sistema robusto de ferramentas para um agente de IA, garantindo que ele seja extensível, modular e aderente aos princípios de Clean Architecture e SOLID. O sistema deve permitir que o agente utilize ferramentas específicas para realizar tarefas, como buscar informações na web ou consultar preços de ações, de forma eficiente e integrada.

## Objetivos Específicos

1. **Definir uma Interface Base para Ferramentas**:

   - Criar uma abstração que padronize a implementação de novas ferramentas.
   - Garantir que todas as ferramentas sigam um contrato comum.

2. **Implementar Ferramentas Concretas**:

   - Ferramentas como `WebSearchTool` e `StockPriceTool` foram desenvolvidas para demonstrar o funcionamento do sistema.

3. **Gerenciar Ferramentas Disponíveis**:

   - Criar um registro centralizado (`available_tools.py`) para gerenciar as ferramentas disponíveis no sistema.

4. **Garantir a Integração com o Agente**:

   - Atualizar o fluxo de criação do agente para incluir as ferramentas disponíveis.

5. **Testar e Validar o Sistema**:

   - Criar testes unitários e exemplos de uso para validar a estrutura e funcionalidade das ferramentas.

6. **Seguir Princípios de Arquitetura Limpa**:
   - Garantir a separação de responsabilidades entre camadas (domínio, aplicação, infraestrutura, apresentação).

## Progresso Atual

### Implementações Concluídas

- **Interface Base (`BaseTool`)**:
  - Criada como uma classe abstrata para padronizar ferramentas.
- **Ferramentas Concretas**:
  - `WebSearchTool`: Realiza buscas na web.
  - `StockPriceTool`: Consulta preços de ações.
- **Registro de Ferramentas**:
  - `available_tools.py`: Gerencia as ferramentas disponíveis.
- **Integração com o Agente**:
  - Atualizado o fluxo de criação do agente para incluir ferramentas.
- **Testes e Exemplos**:
  - `test_tools_structure.py`: Valida a estrutura das ferramentas.
  - `exemplo_uso_tools.py`: Demonstra o uso das ferramentas.

### Problemas Resolvidos

- **Erros de Importação**:
  - Ajustados para evitar dependências circulares.
- **Problemas de Tipagem**:
  - Adicionados métodos e validações para garantir segurança de tipos.
- **Duplicação de Código**:
  - Removida para melhorar a manutenibilidade.

### Resultados Validados

- Todos os testes e exemplos foram executados com sucesso, confirmando a funcionalidade do sistema.

## Próximos Passos

1. **Implementar Tool Calling**:

   - Permitir que o agente detecte e execute ferramentas com base em comandos recebidos.
   - **Subtarefas**:
     - Criar um parser para identificar chamadas de ferramentas em mensagens.
     - Atualizar os adapters OpenAI e Ollama para suportar tool calling.
     - Garantir que os resultados das ferramentas sejam processados corretamente pelo agente.

2. **Adicionar Novas Ferramentas**:

   - Expandir o sistema com ferramentas adicionais conforme necessário.

3. **Testar Integração Completa**:

   - Validar o fluxo completo, desde a detecção de chamadas até a execução e retorno de resultados.

4. **Documentar o Sistema**:

   - Finalizar a documentação técnica e de uso para facilitar a manutenção e expansão futura.

5. **Refinar o Sistema**:
   - Melhorar o tratamento de erros e a experiência do usuário.

## Conclusão

O sistema de ferramentas para o agente de IA está em um estágio avançado de desenvolvimento, com a base sólida e funcional. O foco agora é integrar as ferramentas ao fluxo do agente, permitindo que ele detecte e execute ferramentas dinamicamente. Com isso, o agente será capaz de realizar tarefas complexas de forma autônoma e eficiente.

---

### ✅ **SISTEMA DE TOOLS IMPLEMENTADO COM SUCESSO**

## Resumo da Implementação

O sistema de tools foi completamente implementado seguindo **Clean Architecture** e **princípios SOLID**. A implementação está funcional, testada e documentada.

## Componentes Implementados

### 1. **Domain Layer** ✅

- ✅ `BaseTool` - Interface abstrata para todas as ferramentas

  - Método `get_schema()` - Retorna schema genérico (provider-agnostic)
  - Método `execute()` - Executa a funcionalidade da tool
  - Atributos: `name`, `description`, `parameters`

- ✅ `ToolExecutor` (Domain Service)

  - Executa tools de forma segura
  - Gerencia múltiplas tools
  - Retorna `ToolExecutionResult` estruturado
  - **14 testes unitários passando** ✅

- ✅ `ToolExecutionResult` (Value Object)
  - Representa resultado de execução
  - Métodos: `to_dict()`, `to_llm_message()`

### 2. **Infrastructure Layer** ✅

- ✅ **Concrete Tools**:

  - `WebSearchTool` - Busca web (mock)
  - `StockPriceTool` - Preços de ações B3 (mock)
  - Schemas JSON completos

- ✅ **OpenAI Adapter**:

  - `ToolSchemaFormatter` - Converte schema genérico → OpenAI format
  - `ToolCallParser` - Extrai tool calls das respostas
  - `OpenAIChatAdapter` - Loop de tool calling implementado
    - Detecção automática de tool calls
    - Execução via `ToolExecutor`
    - Envio de resultados de volta ao LLM
    - Máximo de iterações configurável

- ✅ **Ollama Adapter**:

  - Suporte via prompt engineering
  - Tools descritas no system prompt

- ✅ **Registry**:
  - `AvailableTools` - Registro centralizado de tools

### 3. **Application Layer** ✅

- ✅ `CreateAgentUseCase` - Aceita tools opcionais
- ✅ `ChatWithAgentUseCase` - Repassa tools ao adapter
- ✅ `FormatInstructionsUseCase` - Formata tools no prompt
- ✅ `ChatRepository` interface atualizada

### 4. **Testes** ✅

- ✅ 14 testes unitários para `ToolExecutor` (100% passing)
- ✅ Testes de edge cases e error handling
- ✅ Testes de formatação de resultados

### 5. **Documentação** ✅

- ✅ `examples/exemplo_agent_com_tools.py` - Exemplos práticos
- ✅ Diagramas de arquitetura
- ✅ Guia de criação de novas tools

## Princípios SOLID Aplicados

### ✅ Single Responsibility Principle (SRP)

- `BaseTool`: Define contrato para ferramentas
- `ToolExecutor`: Gerencia execução
- `ToolSchemaFormatter`: Formata schemas
- `ToolCallParser`: Interpreta respostas

### ✅ Open/Closed Principle (OCP)

- Novas tools podem ser adicionadas sem modificar código existente
- Apenas implementar `BaseTool` e registrar

### ✅ Liskov Substitution Principle (LSP)

- Qualquer `BaseTool` pode substituir outra

### ✅ Interface Segregation Principle (ISP)

- Interface mínima e focada
- Adapters específicos por provedor

### ✅ Dependency Inversion Principle (DIP)

- **Domain não conhece infraestrutura** ✅
- Schema genérico convertido por adapters
- `get_schema()` retorna formato agnóstico
- `ToolSchemaFormatter` converte para OpenAI (infra layer)

## Fluxo de Execução (OpenAI)

```
User Message
    ↓
OpenAIChatAdapter
    ↓
[Tools convertidas via ToolSchemaFormatter]
    ↓
OpenAI API (com tools parameter)
    ↓
Response com tool_calls?
    ├─ NÃO → Retorna resposta final
    └─ SIM → ToolCallParser extrai calls
              ↓
          ToolExecutor executa
              ↓
          Resultados → OpenAI API
              ↓
          [Loop até resposta final]
              ↓
          Retorna ao usuário
```

## Arquitetura Clean

```
┌────────────────────────────────────────┐
│         PRESENTATION                    │
└──────────────┬─────────────────────────┘
               │
┌──────────────▼─────────────────────────┐
│         APPLICATION                     │
│  (Use Cases)                            │
└──────────────┬─────────────────────────┘
               │
┌──────────────▼─────────────────────────┐
│         DOMAIN                          │
│  • BaseTool (interface) ←─────────┐   │
│  • ToolExecutor (service)          │   │
│  • ToolExecutionResult (VO)        │   │
└────────────────────────────────────┼───┘
                                     │
┌────────────────────────────────────▼───┐
│         INFRASTRUCTURE                  │
│  • WebSearchTool                        │
│  • StockPriceTool                       │
│  • ToolSchemaFormatter (OpenAI)         │
│  • ToolCallParser (OpenAI)              │
│  • OpenAIChatAdapter                    │
└─────────────────────────────────────────┘
```

## Como Usar

### Criar Agent com Tools

```python
from src.infra.config import AvailableTools
from src.application.use_cases import CreateAgentUseCase
from src.application.dtos import CreateAgentInputDTO

# Obter tools
tools = list(AvailableTools.get_available_tools().values())

# Criar agent
agent = CreateAgentUseCase().execute(
    CreateAgentInputDTO(
        provider="openai",
        model="gpt-4",
        tools=tools  # Tools são passadas aqui
    )
)
```

### Criar Nova Tool

```python
from src.domain import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "What this tool does"
    parameters = {
        "type": "object",
        "properties": {
            "param": {"type": "string"}
        },
        "required": ["param"]
    }

    def execute(self, param: str) -> str:
        return f"Result: {param}"
```

## Testes

```bash
# Rodar testes do ToolExecutor
source .venv/bin/activate
python -m pytest tests/domain/services/test_tool_executor.py -v

# Resultado: 14 passed ✅
```

## Próximas Melhorias (Opcional)

- [ ] Implementar CalculatorTool real
- [ ] Adicionar suporte a tools assíncronas
- [ ] Implementar tool caching
- [ ] Adicionar métricas de uso de tools
- [ ] Suporte a tools com streaming
- [ ] Tool com side effects (escrita em DB, etc)
