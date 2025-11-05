# 🏗️ Arquitetura Completa: Sistema de Agentes com Tools

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura em Camadas](#arquitetura-em-camadas)
3. [Fluxo Completo de Criação de Agente](#fluxo-completo-de-criação-de-agente)
4. [Fluxo Completo de Chat com Tools](#fluxo-completo-de-chat-com-tools)
5. [Componentes Detalhados](#componentes-detalhados)
6. [Princípios SOLID Aplicados](#princípios-solid-aplicados)

---

## 🎯 Visão Geral

Seu sistema implementa um **Agent de IA com suporte a Tools (ferramentas)** seguindo **Clean Architecture** e **SOLID**. O sistema permite que agentes de IA:

- 📞 **Façam chamadas a ferramentas externas** (web search, consulta de preços, etc.)
- 🔄 **Escolham automaticamente qual ferramenta usar** (com OpenAI)
- 🧠 **Mantenham contexto de conversação**
- 🔌 **Funcionem com múltiplos provedores** (OpenAI, Ollama)

---

## 🏛️ Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│                  (AgentController - API)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ CreateAgentUseCase│  │ChatWithAgentUseCase│ │FormatInstr... │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              DTOs (CreateAgentInputDTO, etc)              │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                                │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  Agent Entity  │  │   History VO   │  │ BaseTool (ABC)   │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         ToolExecutor (Domain Service)                      │ │
│  │  • execute_tool(name, **kwargs) → ToolExecutionResult     │ │
│  │  • execute_multiple_tools(...)                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         ToolExecutionResult (Value Object)                 │ │
│  │  • tool_name, success, result, error                      │ │
│  │  • to_dict(), to_llm_message()                            │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │            CONCRETE TOOLS (implementam BaseTool)           │ │
│  │  • WebSearchTool → name, description, parameters, execute()│ │
│  │  • StockPriceTool → name, description, parameters, execute│ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         AvailableTools (Registry Pattern)                  │ │
│  │  __AVAILABLE_TOOLS = {                                     │ │
│  │    "web_search": WebSearchTool(),                          │ │
│  │    "stock_price": StockPriceTool()                         │ │
│  │  }                                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              OPENAI ADAPTER                                │ │
│  │  • OpenAIChatAdapter (implementa ChatRepository)           │ │
│  │  • ToolSchemaFormatter → converte BaseTool → OpenAI format│ │
│  │  • ToolCallParser → extrai tool calls das respostas       │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              OLLAMA ADAPTER                                │ │
│  │  • OllamaChatAdapter (implementa ChatRepository)           │ │
│  │  • Tools via prompt engineering (não native support)      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo Completo de Criação de Agente

### Passo a Passo:

```
1️⃣ USUÁRIO CRIA DTO
   ↓
   CreateAgentInputDTO(
     provider="openai",
     model="gpt-4",
     tools=["web_search", "stock_price"]  ← Pode ser string OU BaseTool
   )

2️⃣ DTO.VALIDATE() É CHAMADO
   ↓
   • Valida provider, model, etc
   • CONVERTE tools de string → BaseTool
   • Consulta AvailableTools.get_available_tools()
   • Substitui ["web_search"] → [WebSearchTool()]
   • Valida que cada tool tem execute(), name, description

3️⃣ CreateAgentUseCase.execute(dto)
   ↓
   • Chama dto.validate()
   • Chama dto.get_validated_tools() → List[BaseTool]
   • Chama FormatInstructionsUseCase

4️⃣ FormatInstructionsUseCase
   ↓
   • Recebe instructions + tools
   • SE tools existe:
     - Itera sobre cada tool
     - Chama tool.get_schema_for_llm()
     - Adiciona descrição das tools nas instruções:

       "Você pode usar as seguintes ferramentas:
        <tool>
          <name>web_search</name>
          <description>Use this to search web...</description>
        </tool>"

   • Retorna: instructions_originais + descrição_tools

5️⃣ CRIA ENTIDADE AGENT
   ↓
   Agent(
     provider="openai",
     model="gpt-4",
     instructions=instructions_formatadas,  ← COM descrição das tools
     tools=[WebSearchTool(), StockPriceTool()],  ← Tools validadas
     history=History()
   )

6️⃣ Agent.__post_init__()
   ↓
   • Valida provider está em SupportedProviders
   • Valida config
   • NÃO valida tools (já validadas no DTO)

✅ RETORNA AGENT PRONTO
```

### Diagrama Visual:

```
┌──────────────────┐
│   User Code      │
└────────┬─────────┘
         │ CreateAgentInputDTO(tools=["web_search"])
         ▼
┌─────────────────────────────┐
│  CreateAgentInputDTO        │
│  • validate()               │◄──┐
│    ├─ Valida campos         │   │
│    └─ Converte tools ───────┼───┤
│                             │   │
│  tools: List[str|BaseTool] │   │
│         ↓ após validate     │   │
│  tools: List[BaseTool]      │   │
└────────┬────────────────────┘   │
         │                        │
         │                        │ Consulta
         ▼                        │
┌─────────────────────────────┐   │
│  AvailableTools (Registry)  │   │
│  {                          │   │
│   "web_search": WebSearch..│───┘
│   "stock_price": StockPrice│
│  }                          │
└─────────────────────────────┘
         │
         │ tools validadas
         ▼
┌─────────────────────────────┐
│  CreateAgentUseCase         │
│  • get_validated_tools()    │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ FormatInstructionsUseCase   │
│  • Adiciona descrição tools │
│    nas instructions         │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│       Agent Entity          │
│  provider: "openai"         │
│  model: "gpt-4"             │
│  instructions: "..." + tools│
│  tools: [WebSearch, Stock]  │
│  history: History()         │
└─────────────────────────────┘
```

---

## 💬 Fluxo Completo de Chat com Tools (OpenAI)

### Cenário: "What is the price of PETR4?"

```
┌─────────────────────────────────────────────────────────────────┐
│  1️⃣ USER SENDS MESSAGE                                          │
└─────────────────────────────────────────────────────────────────┘
   ChatInputDTO(message="What is the price of PETR4?")
   ↓
┌─────────────────────────────────────────────────────────────────┐
│  2️⃣ ChatWithAgentUseCase.execute(agent, input_dto)              │
└─────────────────────────────────────────────────────────────────┘
   • Valida input
   • Chama chat_repository.chat(
       model=agent.model,
       instructions=agent.instructions,  ← Contém descrição das tools
       history=agent.history.to_dict_list(),
       user_ask="What is the price of PETR4?",
       tools=agent.tools  ← [WebSearchTool, StockPriceTool]
     )
   ↓
┌─────────────────────────────────────────────────────────────────┐
│  3️⃣ OpenAIChatAdapter.chat(...)                                 │
└─────────────────────────────────────────────────────────────────┘
   • Recebe tools: List[BaseTool]
   • Converte para formato OpenAI:

   tools_openai = ToolSchemaFormatter.format_tools_for_openai(tools)

   tools_openai = [
     {
       "type": "function",
       "function": {
         "name": "get_stock_price",
         "description": "Use this to get stock prices...",
         "parameters": {
           "type": "object",
           "properties": {
             "ticker": {"type": "string", "description": "..."}
           },
           "required": ["ticker"]
         }
       }
     }
   ]

   • Cria ToolExecutor(tools)
   • Monta mensagens:
     [
       {"role": "system", "content": instructions},
       {"role": "user", "content": "What is the price of PETR4?"}
     ]
   ↓
┌─────────────────────────────────────────────────────────────────┐
│  4️⃣ LOOP DE TOOL CALLING (iteração 1)                           │
└─────────────────────────────────────────────────────────────────┘
   • Chama OpenAI API com:
     - messages
     - tools=tools_openai  ← Informando tools disponíveis

   • OpenAI analisa e decide chamar tool
   • Retorna response com tool_calls:

   response.choices[0].message.tool_calls = [
     {
       "id": "call_abc123",
       "type": "function",
       "function": {
         "name": "get_stock_price",
         "arguments": '{"ticker": "PETR4"}'
       }
     }
   ]
   ↓
┌─────────────────────────────────────────────────────────────────┐
│  5️⃣ DETECTA TOOL CALLS                                          │
└─────────────────────────────────────────────────────────────────┘
   • ToolCallParser.has_tool_calls(response) → True
   • ToolCallParser.extract_tool_calls(response) → [
       {
         "id": "call_abc123",
         "name": "get_stock_price",
         "arguments": {"ticker": "PETR4"}
       }
     ]
   ↓
┌─────────────────────────────────────────────────────────────────┐
│  6️⃣ ADICIONA MENSAGEM DO ASSISTANT COM TOOL_CALLS               │
└─────────────────────────────────────────────────────────────────┘
   assistant_msg = {
     "role": "assistant",
     "content": null,
     "tool_calls": [
       {
         "id": "call_abc123",
         "type": "function",
         "function": {
           "name": "get_stock_price",
           "arguments": '{"ticker": "PETR4"}'
         }
       }
     ]
   }
   messages.append(assistant_msg)
   ↓
┌─────────────────────────────────────────────────────────────────┐
│  7️⃣ EXECUTA TOOL                                                │
└─────────────────────────────────────────────────────────────────┘
   tool_executor.execute_tool(
     tool_name="get_stock_price",
     ticker="PETR4"
   )
   ↓
   ToolExecutor procura tool no _tools_map
   ↓
   Encontra StockPriceTool
   ↓
   Chama StockPriceTool.execute(ticker="PETR4")
   ↓
   StockPriceTool retorna: "The price of PETR4 is R$ 38.50"
   ↓
   Retorna ToolExecutionResult(
     tool_name="get_stock_price",
     success=True,
     result="The price of PETR4 is R$ 38.50",
     execution_time_ms=15.2
   )
   ↓
┌─────────────────────────────────────────────────────────────────┐
│  8️⃣ FORMATA RESULTADO DA TOOL PARA OPENAI                       │
└─────────────────────────────────────────────────────────────────┘
   tool_result_msg = ToolCallParser.format_tool_results_for_llm(
     tool_call_id="call_abc123",
     tool_name="get_stock_price",
     result="The price of PETR4 is R$ 38.50"
   )

   tool_result_msg = {
     "role": "tool",
     "tool_call_id": "call_abc123",
     "name": "get_stock_price",
     "content": "The price of PETR4 is R$ 38.50"
   }

   messages.append(tool_result_msg)
   ↓
┌─────────────────────────────────────────────────────────────────┐
│  9️⃣ LOOP DE TOOL CALLING (iteração 2)                           │
└─────────────────────────────────────────────────────────────────┘
   • Chama OpenAI API novamente com messages atualizado:
     [
       {"role": "system", "content": instructions},
       {"role": "user", "content": "What is the price of PETR4?"},
       {"role": "assistant", "tool_calls": [...]},
       {"role": "tool", "content": "The price of PETR4 is R$ 38.50"}
     ]

   • OpenAI processa o resultado da tool
   • Decide NÃO chamar mais tools
   • Retorna resposta final:

   response.choices[0].message.content =
     "The current price of PETR4 stock is R$ 38.50."
   ↓
┌─────────────────────────────────────────────────────────────────┐
│  🔟 RETORNA RESPOSTA FINAL                                       │
└─────────────────────────────────────────────────────────────────┘
   • ToolCallParser.has_tool_calls(response) → False
   • Extrai content = "The current price of PETR4 stock is R$ 38.50."
   • Registra métricas
   • Retorna content para ChatWithAgentUseCase
   ↓
┌─────────────────────────────────────────────────────────────────┐
│  1️⃣1️⃣ ChatWithAgentUseCase ATUALIZA HISTÓRICO                    │
└─────────────────────────────────────────────────────────────────┘
   • agent.add_user_message("What is the price of PETR4?")
   • agent.add_assistant_message("The current price... R$ 38.50")
   • Retorna ChatOutputDTO(response="...")
   ↓
✅ USUÁRIO RECEBE RESPOSTA
```

### Diagrama de Sequência Visual:

```
User         UseCase         Adapter         OpenAI        ToolExecutor     Tool
 │              │               │               │               │            │
 │─ ask ──────>│               │               │               │            │
 │              │─ chat ──────>│               │               │            │
 │              │               │─ API call ──>│               │            │
 │              │               │  (with tools) │               │            │
 │              │               │               │               │            │
 │              │               │<─ tool_calls ─│               │            │
 │              │               │               │               │            │
 │              │               │─ execute ────────────────────>│            │
 │              │               │               │               │─ execute ─>│
 │              │               │               │               │<─ result ──│
 │              │               │<─ ToolExecution               │            │
 │              │               │   Result                      │            │
 │              │               │               │               │            │
 │              │               │─ API call ──>│               │            │
 │              │               │  (with result)│               │            │
 │              │               │               │               │            │
 │              │               │<─ final resp ─│               │            │
 │              │<─ response ───│               │               │            │
 │<─ answer ───│               │               │               │            │
```

---

## 🧩 Componentes Detalhados

### 1. BaseTool (Domain Layer - Abstract)

**Localização:** `src/domain/value_objects/base_tools.py`

**Responsabilidade:** Definir o contrato que todas as tools devem seguir.

```python
class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool description"
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {},
    }

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Executa a funcionalidade da tool"""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Retorna schema genérico (provider-agnostic)"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    def get_schema_for_llm(self) -> dict:
        """Schema simplificado para prompts"""
        return {
            "name": self.name,
            "description": self.description,
        }
```

**Por que no Domain?**

- ✅ É uma regra de negócio: "toda ferramenta deve ter nome, descrição e executar algo"
- ✅ Não depende de infraestrutura
- ✅ Pode ser testada isoladamente

---

### 2. ToolExecutor (Domain Service)

**Localização:** `src/domain/services/tool_executor.py`

**Responsabilidade:** Executar tools de forma segura e retornar resultados estruturados.

```python
class ToolExecutor:
    def __init__(self, tools: Optional[List[BaseTool]] = None):
        self._tools_map: Dict[str, BaseTool] = {}
        if tools:
            for tool in tools:
                self._tools_map[tool.name] = tool

    def execute_tool(self, tool_name: str, **kwargs) -> ToolExecutionResult:
        # 1. Valida se tool existe
        if not self.has_tool(tool_name):
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' not found"
            )

        # 2. Executa com tratamento de erros
        try:
            tool = self._tools_map[tool_name]
            result = tool.execute(**kwargs)
            return ToolExecutionResult(
                tool_name=tool_name,
                success=True,
                result=result
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=str(e)
            )
```

**Por que no Domain?**

- ✅ Orquestra execução de tools (lógica de negócio)
- ✅ Não sabe NADA sobre OpenAI, Ollama, HTTP, etc
- ✅ Trabalha apenas com abstrações (BaseTool)

---

### 3. WebSearchTool & StockPriceTool (Infrastructure)

**Localização:** `src/infra/adapters/Tools/`

**Responsabilidade:** Implementar funcionalidades concretas.

```python
class StockPriceTool(BaseTool):
    name = "get_stock_price"
    description = "Use this to get stock prices from B3..."
    parameters = {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker (e.g., 'PETR4')"
            }
        },
        "required": ["ticker"]
    }

    def execute(self, ticker: str) -> str:
        # Mock database
        db_prices = {
            "PETR4": 38.50,
            "VALE3": 65.10,
        }

        price = db_prices.get(ticker.upper())
        if price:
            return f"The price of {ticker} is R$ {price:.2f}"
        else:
            return f"Ticker '{ticker}' not found"
```

**Por que na Infrastructure?**

- ✅ Implementação concreta (não abstrata)
- ✅ Poderia chamar APIs externas, banco de dados, etc
- ✅ Substituível sem afetar o domínio

---

### 4. AvailableTools (Infrastructure - Registry Pattern)

**Localização:** `src/infra/config/available_tools.py`

**Responsabilidade:** Centralizar o registro de todas as tools disponíveis.

```python
class AvailableTools:
    __AVAILABLE_TOOLS: Dict[str, BaseTool] = {
        "web_search": WebSearchTool(),
        "stock_price": StockPriceTool(),
    }

    @classmethod
    def get_available_tools(cls) -> Dict[str, BaseTool]:
        return cls.__AVAILABLE_TOOLS.copy()
```

**Vantagens:**

- ✅ Single Source of Truth
- ✅ Fácil adicionar novas tools (basta registrar aqui)
- ✅ DTO pode converter strings → BaseTool consultando este registry

---

### 5. ToolSchemaFormatter (Infrastructure - OpenAI)

**Localização:** `src/infra/adapters/OpenAI/tool_schema_formatter.py`

**Responsabilidade:** Converter schema genérico → formato OpenAI.

```python
class ToolSchemaFormatter:
    @staticmethod
    def format_tool_for_openai(tool: BaseTool) -> Dict[str, Any]:
        schema = tool.get_schema()  # ← Pega schema genérico

        # Converte para formato OpenAI
        return {
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": schema["parameters"],
            },
        }
```

**Por que separado?**

- ✅ **Dependency Inversion Principle**: Domain não conhece OpenAI
- ✅ Se mudar API da OpenAI, só mexe aqui
- ✅ Fácil criar `ToolSchemaFormatterOllama` depois

---

### 6. ToolCallParser (Infrastructure - OpenAI)

**Localização:** `src/infra/adapters/OpenAI/tool_call_parser.py`

**Responsabilidade:** Extrair tool calls das respostas da OpenAI.

```python
class ToolCallParser:
    @staticmethod
    def has_tool_calls(response: Any) -> bool:
        """Verifica se resposta tem tool calls"""
        try:
            message = response.choices[0].message
            return hasattr(message, "tool_calls") and message.tool_calls
        except:
            return False

    @staticmethod
    def extract_tool_calls(response: Any) -> List[Dict[str, Any]]:
        """Extrai tool calls estruturados"""
        if not ToolCallParser.has_tool_calls(response):
            return []

        tool_calls = []
        for tc in response.choices[0].message.tool_calls:
            tool_calls.append({
                "id": tc.id,
                "name": tc.function.name,
                "arguments": json.loads(tc.function.arguments)
            })
        return tool_calls

    @staticmethod
    def format_tool_results_for_llm(tool_call_id, tool_name, result):
        """Formata resultado para enviar de volta à OpenAI"""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": str(result)
        }
```

**Por que separado?**

- ✅ OpenAI tem formato específico de tool calls
- ✅ Isolado em um componente reutilizável
- ✅ Fácil de testar

---

### 7. OpenAIChatAdapter - Loop de Tool Calling

**Localização:** `src/infra/adapters/OpenAI/openai_chat_adapter.py`

**Responsabilidade:** Implementar o loop de tool calling.

```python
class OpenAIChatAdapter(ChatRepository):
    def chat(self, ..., tools: Optional[List[BaseTool]] = None) -> str:
        # 1. Converter tools para formato OpenAI
        if tools:
            tool_schemas = ToolSchemaFormatter.format_tools_for_openai(tools)
            tool_executor = ToolExecutor(tools)

        # 2. Loop de tool calling
        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            # 3. Chamar OpenAI
            response = self.__call_openai_api(model, messages, config, tool_schemas)

            # 4. Verificar se tem tool calls
            if ToolCallParser.has_tool_calls(response):
                # 5. Adicionar mensagem do assistant
                assistant_msg = ToolCallParser.get_assistant_message_with_tool_calls(response)
                messages.append(assistant_msg)

                # 6. Extrair tool calls
                tool_calls = ToolCallParser.extract_tool_calls(response)

                # 7. Executar cada tool
                for tc in tool_calls:
                    result = tool_executor.execute_tool(tc["name"], **tc["arguments"])

                    # 8. Formatar resultado
                    tool_msg = ToolCallParser.format_tool_results_for_llm(
                        tc["id"], tc["name"], result.result
                    )
                    messages.append(tool_msg)

                # 9. Continuar loop (próxima iteração)
                continue

            # 10. Sem tool calls → resposta final
            return response.choices[0].message.content

        # Max iterations atingido
        raise ChatException("Max tool iterations exceeded")
```

**Fluxo do Loop:**

```
Iteração 1: User message → OpenAI → Tool calls → Execute → Add results
Iteração 2: Messages + Results → OpenAI → Final response
```

---

### 8. FormatInstructionsUseCase

**Localização:** `src/application/use_cases/format_instructions_use_case.py`

**Responsabilidade:** Adicionar descrição das tools nas instruções do sistema.

```python
class FormatInstructionsUseCase:
    def execute(self, instructions: str, tools: List[BaseTool]) -> str:
        if not tools:
            return instructions

        # Adicionar descrição das tools
        prompt_part = "Você pode usar as seguintes ferramentas:\n\n"
        for tool in tools:
            schema = tool.get_schema_for_llm()
            prompt_part += f"<tool>\n"
            prompt_part += f"  <name>{schema['name']}</name>\n"
            prompt_part += f"  <description>{schema['description']}</description>\n"
            prompt_part += f"</tool>\n\n"

        return instructions + "\n\n" + prompt_part
```

**Por que isso?**

- ✅ Para **Ollama**: Não tem native tool calling, precisa de prompt engineering
- ✅ Para **OpenAI**: Ajuda o modelo entender melhor as tools
- ✅ Separa responsabilidade de formatação

---

## 🎯 Princípios SOLID Aplicados

### 1. **Single Responsibility Principle (SRP)** ✅

Cada classe tem UMA responsabilidade:

| Classe                | Responsabilidade                 |
| --------------------- | -------------------------------- |
| `BaseTool`            | Definir contrato de tools        |
| `ToolExecutor`        | Executar tools com segurança     |
| `ToolSchemaFormatter` | Converter schemas para OpenAI    |
| `ToolCallParser`      | Interpretar respostas OpenAI     |
| `WebSearchTool`       | Buscar na web                    |
| `StockPriceTool`      | Consultar preços                 |
| `AvailableTools`      | Registrar tools disponíveis      |
| `OpenAIChatAdapter`   | Gerenciar comunicação com OpenAI |

---

### 2. **Open/Closed Principle (OCP)** ✅

Sistema **aberto para extensão**, **fechado para modificação**:

```python
# ✅ ADICIONAR NOVA TOOL (sem modificar código existente)

# 1. Criar nova tool
class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Performs calculations"
    parameters = {...}

    def execute(self, expression: str) -> str:
        return str(eval(expression))

# 2. Registrar em AvailableTools
class AvailableTools:
    __AVAILABLE_TOOLS = {
        "web_search": WebSearchTool(),
        "stock_price": StockPriceTool(),
        "calculator": CalculatorTool(),  ← ADICIONAR AQUI
    }

# 3. Usar
agent = CreateAgentUseCase().execute(
    CreateAgentInputDTO(
        provider="openai",
        model="gpt-4",
        tools=["calculator"]  ← Funciona automaticamente!
    )
)
```

---

### 3. **Liskov Substitution Principle (LSP)** ✅

Qualquer `BaseTool` pode substituir outra:

```python
def process_tools(tools: List[BaseTool]):
    for tool in tools:
        tool.execute(...)  # Funciona para QUALQUER BaseTool
```

---

### 4. **Interface Segregation Principle (ISP)** ✅

Interface mínima e focada:

```python
class BaseTool(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        pass

    def get_schema(self) -> Dict[str, Any]:
        pass
```

**Não força implementações a ter métodos desnecessários.**

---

### 5. **Dependency Inversion Principle (DIP)** ✅

**CRUCIAL:** Domain não depende de Infrastructure!

```
❌ ERRADO:
   Domain → OpenAI (depende de infraestrutura)

✅ CORRETO:
   Domain ← BaseTool (abstração)
      ↑
   Infrastructure → WebSearchTool (implementa abstração)
   Infrastructure → ToolSchemaFormatter (converte para OpenAI)
```

**Prova:**

- `BaseTool.get_schema()` retorna formato **genérico**
- `ToolSchemaFormatter` (infraestrutura) converte para OpenAI
- Se mudar de OpenAI → Anthropic, só muda infraestrutura

---

## 🔍 Análise do Código Atual

### ✅ O que está CORRETO:

1. **Separação de Camadas**: Domain não conhece OpenAI ✅
2. **BaseTool abstrato**: Contrato bem definido ✅
3. **ToolExecutor no Domain**: Lógica de negócio isolada ✅
4. **ToolSchemaFormatter separado**: Conversão isolada ✅
5. **ToolCallParser**: Parse de respostas isolado ✅
6. **Loop de tool calling**: Implementado corretamente ✅
7. **Validação no DTO**: Converte strings → BaseTool ✅
8. **Registry Pattern**: AvailableTools centralizado ✅

### ⚠️ Pontos de Atenção:

1. **FormatInstructionsUseCase**:

   - Adiciona tools no prompt (OK para Ollama)
   - Para OpenAI, não é necessário (já usa native tool calling)
   - **Sugestão**: Criar formatação condicional por provider

2. **Ollama não tem loop de tool calling**:

   - Só adiciona tools no prompt
   - Model precisa "adivinhar" quando usar
   - **Sugestão**: Implementar parser de respostas Ollama para detectar tentativas de tool calls

3. **Tool results não são adicionados ao histórico**:
   - Apenas resposta final é salva
   - **Sugestão**: Adicionar `add_tool_message()` ao Agent

---
