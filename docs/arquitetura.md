# 🏗️ Arquitetura

Documentação da arquitetura do sistema seguindo **Clean Architecture** e **SOLID principles**.

---

## 📐 Estrutura de Camadas

```
┌─────────────────────────────────────┐
│        PRESENTATION                 │  AIAgent Controller
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

---

## 🎯 Camadas

### 1. Domain (Domínio)

**Localização:** `src/domain/`

**Responsabilidade:** Regras de negócio puras, independentes de tecnologia.

**Componentes:**

- **Entities:** `Agent` (entidade principal)
- **Value Objects:** `Message`, `History`, `MessageRole`
- **Base Classes:** `BaseTool` (para ferramentas)
- **Exceptions:** Erros de domínio

**Características:**

- ✅ Zero dependências externas
- ✅ Lógica de negócio pura
- ✅ 100% testável

---

### 2. Application (Aplicação)

**Localização:** `src/application/`

**Responsabilidade:** Orquestrar casos de uso do sistema.

**Componentes:**

- **Use Cases:**
  - `CreateAgentUseCase` - Criar agente
  - `ChatWithAgentUseCase` - Conversar com agente
  - `GetAgentConfigUseCase` - Obter configurações
- **DTOs:** Transferência de dados entre camadas
- **Interfaces:** `ChatRepository` (contrato para adapters)

**Características:**

- ✅ Coordena entidades do domínio
- ✅ Define interfaces para infraestrutura
- ✅ Independente de frameworks

---

### 3. Infrastructure (Infraestrutura)

**Localização:** `src/infra/`

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

**Características:**

- ✅ Implementa interfaces da Application
- ✅ Substituível sem afetar negócio
- ✅ Contém detalhes de bibliotecas externas

---

### 4. Presentation (Apresentação)

**Localização:** `src/presentation/`

**Responsabilidade:** Interface pública com o usuário.

**Componentes:**

- **AIAgent:** Controller principal (fachada simplificada)

**Características:**

- ✅ API intuitiva e fácil de usar
- ✅ Esconde complexidade interna
- ✅ Pode ser substituída (CLI, API REST, GUI)

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
    @staticmethod
    def create(model: str, local_ai: Optional[str] = None):
        if local_ai == "ollama":
            return OllamaChatAdapter(model)
        elif "gpt" in model.lower():
            return OpenAIChatAdapter(model)
        else:
            return OllamaChatAdapter(model)
```

### Facade Pattern

```python
# AIAgent é uma fachada simplificada
class AIAgent:
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

```
User → AIAgent.chat()
    → ChatWithAgentUseCase.execute()
        → ChatRepository.chat()
            → OpenAIChatAdapter / OllamaChatAdapter
                → API Externa (OpenAI / Ollama)
            ← Response
        ← ChatOutputDTO
    ← response: str
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
agent = AIAgent(provider="ollama", model="llama2")
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

**Versão:** 0.1.0 | **Atualização:** Novembro 2025
