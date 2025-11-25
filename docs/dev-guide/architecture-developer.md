# 🏗️ Guia de Arquitetura para Desenvolvedores

Documentação completa da arquitetura do **Create Agents AI**, baseada em **Clean Architecture** e **princípios SOLID**.

______________________________________________________________________

## 📐 Estrutura de Camadas

```
┌─────────────────────────────────────┐
│        application                 │  CreateAgent Controller
│     (Interface do Usuário)          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        APPLICATION                  │  Use Cases & DTOs
│    (Lógica da Aplicação)            │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          DOMAIN                     │  Entities, Rules
│    (Regras de Negócio)              │
└──────────────▲──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│      INFRASTRUCTURE                 │  Adapters, Config
│    (Detalhes Técnicos)              │
└─────────────────────────────────────┘
```

______________________________________________________________________

## 🎯 Camadas

### 1. Domain (Domínio)

**Localização:** `src/createagents/domain/`

**Responsabilidade:** Regras de negócio puras, independentes de tecnologia.

**Componentes:**

- **Entities:** `Agent` (entidade principal)
- **Value Objects:** `Message`, `MessageRole`, `History`, `SupportedConfigs`, `SupportedProviders`, `BaseTool` (ferramentas)
- **Domain Services:** `ToolExecutor`, `ToolExecutionResult` (execução segura de ferramentas)
- **Exceptions:** `domain.exceptions` (ex.: `AgentException`, `InvalidAgentConfigException`, `UnsupportedConfigException`)

______________________________________________________________________

### 2. Application (Aplicação)

**Localização:** `src/createagents/application/`

**Responsabilidade:** Orquestrar casos de uso do sistema.

**Componentes:**

- **Facade / Controller:** `CreateAgent` — fachada simples que cria agentes e expõe métodos como `chat`, `get_configs`, `get_all_available_tools`, `clear_history`, `export_metrics_*`.
- **Use Cases (application/use_cases):**
  - `CreateAgentUseCase` — criação e validação de agentes (invocado por `AgentComposer`).
  - `ChatWithAgentUseCase` — orquestra mensagens entre `Agent` e `ChatRepository` (adapters).
  - `GetAgentConfigUseCase` — retorna as configurações do agente.
  - `GetAllAvailableToolsUseCase` / `GetSystemAvailableToolsUseCase` — listagem de tools disponíveis.
- **DTOs (application/dtos):** Objetos de transferência como `CreateAgentInputDTO`, `ChatInputDTO`, `AgentConfigOutputDTO` usados para comunicação entre controller/use-cases.
- **Interfaces (application/interfaces):** `ChatRepository` — contrato que os adapters (`OpenAIChatAdapter`, `OllamaChatAdapter`) implementam para manter a camada de aplicação independente das integrações.

______________________________________________________________________

### 3. Infrastructure (Infraestrutura)

**Localização:** `src/createagents/infra/`

**Responsabilidade:** Implementar detalhes técnicos e integrações externas.

**Componentes:**

- **Adapters:**
  - `OpenAIChatAdapter` - Integração com OpenAI
  - `OllamaChatAdapter` - Integração com Ollama
- **Tools:**
  - `CurrentDateTool` - Ferramenta de data/hora
  - `ReadLocalFileTool` - Leitura de arquivos
- **Factory:** `ChatAdapterFactory` - Criação de adapters
- **Config:** `EnvironmentConfig`, `LoggingConfig`, `MetricsCollector`

______________________________________________________________________

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
```

______________________________________________________________________

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

______________________________________________________________________

## 🔄 Fluxo de Dados

```
User → CreateAgent.chat()
    → ChatWithAgentUseCase.execute()
        → ChatRepository.chat()
            → OpenAIChatAdapter / OllamaChatAdapter
                → API Externa (OpenAI / Ollama)
            ← Response
        ← ChatOutputDTO
    ← response: str
```

______________________________________________________________________

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

______________________________________________________________________

**Versão:** 0.1.1 | **Atualização:** 25/11/2025
