# 🏗️ Guia de Arquitetura para Desenvolvedores

Documentação completa da arquitetura do **Create Agents AI**, baseada em **Clean Architecture** e **princípios SOLID**.

---

## 📐 Estrutura de Camadas

```
┌─────────────────────────────────────┐
│       PRESENTATION                  │  CLI, UI (ChatCLIApplication)
│     (Interface do Usuário)          │  Command Handlers, Terminal UI
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        APPLICATION                  │  Facade (CreateAgent)
│    (Lógica da Aplicação)            │  Use Cases, DTOs, Services
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          DOMAIN                     │  Entities, Rules, Interfaces
│    (Regras de Negócio)              │  Agent, ToolExecutor, LoggerInterface
└──────────────▲──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│      INFRASTRUCTURE                 │  Adapters, Handlers, Config
│    (Detalhes Técnicos)              │  OpenAI, Ollama, Tools, Metrics
└─────────────────────────────────────┘
```

---

## 🎯 Camadas

### 1. Presentation (Apresentação)

**Localização:** `src/createagents/presentation/`

**Responsabilidade:** Interface de usuário e interação externa.

**Componentes:**

- **CLI Application:** `ChatCLIApplication` — aplicação CLI interativa para chat com agentes
- **Command Handlers:** Sistema baseado no **Command Pattern**
  - `ChatCommandHandler` — processamento de mensagens de chat
  - `HelpCommandHandler` — exibe ajuda e comandos disponíveis
  - `MetricsCommandHandler` — mostra métricas de performance
  - `ConfigsCommandHandler` — exibe configurações do agente
  - `ToolsCommandHandler` — lista ferramentas disponíveis
  - `ClearCommandHandler` — limpa histórico de conversação
- **UI Components:** `TerminalRenderer`, `TerminalFormatter`, `ColorScheme` — renderização colorida no terminal
- **I/O:** `InputReader` — leitura de entrada do usuário
- **Registry:** `CommandRegistry` — registro e resolução de comandos

---

### 2. Application (Aplicação)

**Localização:** `src/createagents/application/`

**Responsabilidade:** Orquestrar casos de uso do sistema.

**Componentes:**

- **Facade / Controller:** `CreateAgent` — fachada simples que cria agentes e expõe métodos como `chat` (async), `get_configs`, `get_all_available_tools`, `clear_history`, `export_metrics_*`.
- **Services:** `AgentService` — serviço que encapsula `Agent` com logging integrado
- **Use Cases (application/use_cases):**
  - `CreateAgentUseCase` — criação e validação de agentes (invocado por `AgentComposer`).
  - `ChatWithAgentUseCase` — orquestra mensagens **assíncronas** entre `Agent` e `ChatRepository` (adapters).
  - `GetAgentConfigUseCase` — retorna as configurações do agente.
  - `GetAllAvailableToolsUseCase` / `GetSystemAvailableToolsUseCase` — listagem de tools disponíveis.
- **DTOs (application/dtos):** Objetos de transferência:
  - `CreateAgentInputDTO`, `ChatInputDTO`, `AgentConfigOutputDTO` — comunicação entre controller/use-cases
  - **`StreamingResponseDTO`** — wrapper para AsyncGenerator que permite iteração e await de respostas em streaming
- **Interfaces (application/interfaces):** `ChatRepository` — contrato que os adapters implementam com suporte **assíncrono**

---

### 3. Domain (Domínio)

**Localização:** `src/createagents/domain/`

**Responsabilidade:** Regras de negócio puras, independentes de tecnologia.

**Componentes:**

- **Entities:** `Agent` (entidade principal)
- **Value Objects:** `Message`, `MessageRole`, `History`, `SupportedConfigs`, `SupportedProviders`, `BaseTool` (ferramentas), `ChatResponse`
- **Domain Services:** `ToolExecutor` (execução **assíncrona** de ferramentas), `ToolExecutionResult`
- **Interfaces (domain/interfaces):** **`LoggerInterface`** — abstração de logging no domínio (DIP - Dependency Inversion Principle)
- **Exceptions:** `domain.exceptions` (ex.: `AgentException`, `InvalidAgentConfigException`, `UnsupportedConfigException`)

---

### 4. Infrastructure (Infraestrutura)

**Localização:** `src/createagents/infra/`

**Responsabilidade:** Implementar detalhes técnicos e integrações externas.

**Componentes:**

- **Adapters (Chat):**
  - `OpenAIChatAdapter` — integração com OpenAI
  - `OllamaChatAdapter` — integração com Ollama
- **Handlers (Async Streaming):**
  - `OpenAIHandler` / `OpenAIStreamHandler` — processamento de chamadas não-streaming e streaming OpenAI
  - `OllamaHandler` / `OllamaStreamHandler` — processamento de chamadas não-streaming e streaming Ollama
- **Clients:**
  - `OpenAIClient` — cliente HTTP para OpenAI
  - `OllamaClient` — cliente HTTP para Ollama
- **Common Adapters:**
  - `MetricsRecorder` — gravação centralizada de métricas (OpenAI e Ollama)
- **Tools:**
  - `CurrentDateTool` — ferramenta de data/hora
  - `ReadLocalFileTool` — leitura de arquivos (PDF, Excel, CSV, Parquet, JSON, YAML, TXT)
- **Factory:** `ChatAdapterFactory` — criação de adapters baseada em provider
- **Config:** `EnvironmentConfig`, `LoggingConfig`, `StandardLogger` (implementação de `LoggerInterface`), `ChatMetrics`

---

## 🎨 Princípios SOLID

### Single Responsibility (SRP)

Cada classe tem uma única responsabilidade:

```python
Agent          # Representa um agente
History        # Gerencia histórico
ChatWithAgentUseCase  # Orquestra conversa
```

### Open/Closed (OCP)

Aberto para extensão, fechado para modificação:

```python
# Adicionar novo provider sem modificar código existente
class ClaudeAdapter(ChatRepository):
    def chat(self, ...): pass
```

### Liskov Substitution (LSP)

Adapters são intercambiáveis:

```python
# Qualquer adapter pode substituir outro
adapter: ChatRepository = OpenAIChatAdapter()
# ou
adapter: ChatRepository = OllamaChatAdapter()
```

### Interface Segregation (ISP)

Interfaces específicas e focadas:

```python
class ChatRepository(ABC):
    @abstractmethod
    def chat(self, ...) -> str:
        pass
```

### Dependency Inversion (DIP)

Depende de abstrações, não de implementações:

```python
class ChatWithAgentUseCase:
    def __init__(self, chat_repository: ChatRepository):  # Interface
        self.__chat_repository = chat_repository

# Exemplo com LoggerInterface (DIP no domínio)
class ToolExecutor:
    def __init__(self, logger: LoggerInterface):  # Abstração
        self._logger = logger  # Não depende de StandardLogger diretamente
```

---

## 🔧 Padrões de Design

### Repository Pattern

```python
class ChatRepository(ABC):
    @abstractmethod
    def chat(self, ...) -> str:
        pass

class OpenAIChatAdapter(ChatRepository):
    def chat(self, ...): # Implementação
```

### Factory Pattern

```python
class ChatAdapterFactory:
    @classmethod
    def create(
        cls,
        provider: str,
        model: str,
    ) -> ChatRepository:

        provider_lower = provider.lower()
        adapter: ChatRepository

        if provider_lower == "openai":
            adapter = OpenAIChatAdapter()
        elif provider_lower == "ollama":
            adapter = OllamaChatAdapter()
        else:
            raise ValueError(f"Invalid provider: {provider}.")
        return adapter
```

### Facade Pattern

```python
# CreateAgent é uma fachada simplificada
class CreateAgent:
    def __init__(self, provider, model, ...):
        # Esconde complexidade da criação
        self.__agent = AgentComposer.create_agent(...)
        self.__chat_use_case = AgentComposer.create_chat_use_case(...)
```

### Value Object Pattern

```python
@dataclass(frozen=True)  # Imutável
class Message:
    role: MessageRole
    content: str
```

---

## 🔄 Fluxo de Dados

### Fluxo Síncrono (await response)

```
User → CreateAgent.chat()
    → ChatWithAgentUseCase.execute() [async]
        → ChatRepository.chat() [async]
            → OpenAIHandler / OllamaHandler
                → StreamHandler (processa streaming)
                    → API Externa (OpenAI / Ollama)
                    ← Tokens em streaming
                ← Response completo
            ← AsyncGenerator
        ← StreamingResponseDTO
    ← await response (string completa)
```

### Fluxo Assíncrono (async for)

```
User → CreateAgent.chat()
    → ChatWithAgentUseCase.execute() [async]
        → ChatRepository.chat() [async]
            → StreamHandler.handle_streaming()
                → async for token in api_stream:
                    → yield token  # Streaming em tempo real
            ← AsyncGenerator[str]
        ← StreamingResponseDTO
    → async for token in response:
        → print(token, end='')  # Exibe token por token
```

### Fluxo CLI

```
Terminal → ChatCLIApplication.run()
    → CommandRegistry.find_handler(user_input)
        → CommandHandler.execute()
            → CreateAgent.chat() [se ChatCommandHandler]
                → async for token in response:
                    → TerminalRenderer.render_token()
```

---

## 💡 Benefícios da Arquitetura

### 🧪 Testabilidade

```python
# Mock fácil de dependências
mock_repo = Mock(spec=ChatRepository)
use_case = ChatWithAgentUseCase(mock_repo)
```

### 🔄 Flexibilidade

```python
# Trocar provider sem mudar código
agent = CreateAgent(provider="ollama", model="llama2")
```

### 📈 Escalabilidade

- Adicionar novos providers facilmente
- Extensível via interfaces
- Preparado para crescimento

### 🛡️ Manutenibilidade

- Código organizado em camadas
- Responsabilidades claras
- Fácil localizar e corrigir bugs

---

## 🔄 Padrões Assíncronos

### Streaming com AsyncGenerator

```python
# Handler retorna AsyncGenerator
async def handle_streaming(self, ...) -> AsyncGenerator[str, None]:
    async for chunk in api_response:
        yield chunk  # Stream em tempo real

# DTO encapsula AsyncGenerator
class StreamingResponseDTO:
    def __init__(self, generator: AsyncGenerator[str, None]):
        self._generator = generator

    async def __anext__(self):  # Permite async for
        return await self._generator.__anext__()

    def __await__(self):  # Permite await
        async def _consume():
            return ''.join([token async for token in self])
        return _consume().__await__()
```

---

**Versão:** 0.1.3 | **Atualização:** 01/12/2025
