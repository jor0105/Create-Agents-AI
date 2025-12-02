# Arquitetura da CLI

Documentação técnica da camada Presentation (CLI) do CreateAgents AI.

---

## 📐 Visão Geral

A CLI segue o **Command Pattern** para processar entrada do usuário e executar ações. É totalmente desacoplada da camada de aplicação através de interfaces.

```
ChatCLIApplication (orquestrador)
    ├── CommandRegistry (registro de comandos)
    ├── TerminalRenderer (UI/renderização)
    ├── InputReader (leitura de entrada)
    └── CommandHandlers (processadores específicos)
        ├── ChatCommandHandler
        ├── HelpCommandHandler
        ├── MetricsCommandHandler
        ├── ConfigsCommandHandler
        ├── ToolsCommandHandler
        └── ClearCommandHandler
```

---

## 🎯 Componentes Principais

### 1. ChatCLIApplication

**Responsabilidade**: Orquestrador principal do ciclo de vida da CLI.

**Localização**: `src/createagents/presentation/cli/application/chat_cli_app.py`

```python
class ChatCLIApplication:
    """Main CLI application orchestrator.

    Responsibility: Orchestrate the CLI application lifecycle.
    This follows:
    - SRP: Only handles application orchestration
    - DIP: Depends on abstractions (CommandHandler interface)
    - OCP: New commands can be added by registering new handlers
    """

    def __init__(self, agent: 'CreateAgent'):
        self._agent = agent
        self._renderer = TerminalRenderer()
        self._input_reader = InputReader()
        self._registry = CommandRegistry()
        self._setup_commands()

    def run(self) -> None:
        """Start the CLI application main loop."""
        # Loop principal
```

**Métodos**:

- `__init__(agent)` - Inicializa componentes
- `_setup_commands()` - Registra handlers de comandos
- `run()` - Loop principal da aplicação
- `_is_exit_command(input)` - Verifica comandos de saída

---

### 2. CommandHandler (Interface)

**Responsabilidade**: Interface abstrata para handlers de comandos.

**Localização**: `src/createagents/presentation/cli/commands/base_command.py`

```python
class CommandHandler(ABC):
    """Abstract base class for command handlers.

    This implements the Command Pattern, allowing dynamic
    command registration and execution.
    """

    def __init__(self, renderer: TerminalRenderer):
        self._renderer = renderer

    @abstractmethod
    def can_handle(self, user_input: str) -> bool:
        """Check if this handler can process the input."""
        pass

    @abstractmethod
    def execute(self, agent: 'CreateAgent', user_input: str) -> None:
        """Execute the command."""
        pass

    @abstractmethod
    def get_aliases(self) -> List[str]:
        """Get command aliases."""
        pass
```

---

### 3. CommandRegistry

**Responsabilidade**: Registro e resolução de comandos.

**Localização**: `src/createagents/presentation/cli/application/command_registry.py`

```python
class CommandRegistry:
    """Registry for command handlers.

    Responsibility: Maintain and resolve command handlers.
    This follows OCP: new handlers can be added without modification.
    """

    def __init__(self):
        self._handlers: List[CommandHandler] = []

    def register(self, handler: CommandHandler) -> None:
        """Register a command handler."""
        self._handlers.append(handler)

    def find_handler(self, user_input: str) -> Optional[CommandHandler]:
        """Find the first handler that can process the input."""
        for handler in self._handlers:
            if handler.can_handle(user_input):
                return handler
        return None
```

**Padrão de Registro**:
Os handlers são registrados em ordem, do mais específico ao mais genérico. O `ChatCommandHandler` deve ser sempre o último (handler padrão).

---

### 4. Command Handlers

#### ChatCommandHandler

**Responsabilidade**: Processar mensagens de chat (handler padrão).

```python
class ChatCommandHandler(CommandHandler):
    """Handles regular chat messages (default handler)."""

    def can_handle(self, user_input: str) -> bool:
        # Aceita qualquer entrada (fallback)
        return True

    def execute(self, agent: 'CreateAgent', user_input: str) -> None:
        # Processa streaming assíncrono
        asyncio.run(self._async_execute(agent, user_input))
```

#### HelpCommandHandler

**Responsabilidade**: Exibir ajuda e lista de comandos.

```python
class HelpCommandHandler(CommandHandler):
    def can_handle(self, user_input: str) -> bool:
        normalized = self._normalize_input(user_input)
        return normalized in self.get_aliases()

    def get_aliases(self) -> List[str]:
        return ['/help', 'help']
```

#### MetricsCommandHandler

**Responsabilidade**: Exibir métricas de performance.

```python
class MetricsCommandHandler(CommandHandler):
    def execute(self, agent: 'CreateAgent', user_input: str) -> None:
        metrics = agent.get_metrics()
        # Formata e renderiza métricas
```

_(Outros handlers seguem estrutura similar)_

---

### 5. TerminalRenderer

**Responsabilidade**: Renderização de UI no terminal.

**Localização**: `src/createagents/presentation/cli/ui/terminal_renderer.py`

```python
class TerminalRenderer:
    """Handles terminal rendering with colors and formatting.

    Responsibility: Encapsulate all terminal output logic.
    This follows SRP by handling only rendering concerns.
    """

    def __init__(self):
        self._formatter = TerminalFormatter()
        self._colors = ColorScheme()

    def render_welcome_screen(self) -> None:
        """Display welcome message."""

    def render_prompt(self) -> None:
        """Display user input prompt."""

    def render_assistant_token(self, token: str) -> None:
        """Render a single token from assistant."""

    def render_system_message(self, message: str) -> None:
        """Render a system message."""

    def render_error(self, message: str) -> None:
        """Render an error message."""
```

**Métodos de Renderização**:

- `render_welcome_screen()` - Tela de boas-vindas
- `render_prompt()` - Prompt de entrada
- `render_input_indicator()` - Indicador ✎
- `render_assistant_token(token)` - Token individual do agente
- `render_thinking_indicator()` - Indicador "pensando..."
- `render_system_message(msg)` - Mensagem do sistema
- `render_error(msg)` - Mensagem de erro
- `render_metrics(metrics)` - Exibir métricas
- `render_configs(configs)` - Exibir configurações
- `render_tools(tools)` - Exibir ferramentas

---

### 6. TerminalFormatter

**Responsabilidade**: Formatação de markdown para terminal.

**Localização**: `src/createagents/presentation/cli/ui/terminal_formatter.py`

```python
class TerminalFormatter:
    """Formats markdown text for terminal display.

    Converts markdown elements to terminal-compatible formatting.
    """

    @staticmethod
    def format_markdown(text: str) -> str:
        """Convert markdown to terminal formatting."""
        # Converte **bold**, *italic*, `code`, etc.
```

---

### 7. ColorScheme

**Responsabilidade**: Define esquema de cores do terminal.

**Localização**: `src/createagents/presentation/cli/ui/color_scheme.py`

```python
class ColorScheme:
    """Defines color scheme for terminal output."""

    PRIMARY = "\033[36m"      # Cyan
    SUCCESS = "\033[32m"      # Green
    WARNING = "\033[33m"      # Yellow
    ERROR = "\033[31m"        # Red
    INFO = "\033[34m"         # Blue
    COMMAND = "\033[35m"      # Magenta
    RESET = "\033[0m"
```

---

## 🔄 Fluxo de Execução

### 1. Inicialização

```
main()
  → ChatCLIApplication(agent)
      → __init__
          → TerminalRenderer()
          → InputReader()
          → CommandRegistry()
          → _setup_commands()
              → registry.register(HelpCommandHandler)
              → registry.register(MetricsCommandHandler)
              → ... (outros comandos)
              → registry.register(ChatCommandHandler) ← ÚLTIMO
```

### 2. Loop Principal

```
app.run()
  → renderer.render_welcome_screen()
  → while True:
      → renderer.render_prompt()
      → user_input = input_reader.read_user_input()
      → if _is_exit_command(user_input): break
      → handler = registry.find_handler(user_input)
      → handler.execute(agent, user_input)
```

### 3. Processamento de Comando

```
# Exemplo: /metrics
registry.find_handler("/metrics")
  → itera handlers registrados
  → MetricsCommandHandler.can_handle("/metrics") → True
  → retorna MetricsCommandHandler

MetricsCommandHandler.execute(agent, "/metrics")
  → metrics = agent.get_metrics()
  → renderer.render_metrics(metrics)
```

### 4. Processamento de Chat (Streaming)

```
ChatCommandHandler.execute(agent, "Olá")
  → asyncio.run(_async_execute(agent, "Olá"))
      → renderer.render_thinking_indicator()
      → response = await agent.chat("Olá")
      → async for token in response:
          → renderer.render_assistant_token(token)
      → renderer.clear_thinking_indicator()
```

---

## 🎨 Princípios Arquiteturais

### Single Responsibility (SRP)

Cada classe tem uma responsabilidade única:

- `ChatCLIApplication`: Orquestração
- `CommandRegistry`: Registro e resolução
- `TerminalRenderer`: Renderização
- `CommandHandler`: Processamento de comando específico

### Open/Closed (OCP)

Aberto para extensão via novos handlers:

```python
# Adicionar novo comando sem modificar código existente
class CustomCommandHandler(CommandHandler):
    def can_handle(self, user_input: str) -> bool:
        return user_input.startswith('/custom')

    def execute(self, agent, user_input):
        # Implementação customizada
        pass

    def get_aliases(self):
        return ['/custom']

# Registrar
registry.register(CustomCommandHandler(renderer))
```

### Dependency Inversion (DIP)

Handlers dependem de abstrações (`CommandHandler`), não implementações concretas.

### Command Pattern

Cada handler encapsula uma ação como objeto, permitindo:

- Parametrização de clientes com diferentes solicitações
- Enfileiramento de solicitações
- Suporte a operações reversíveis

---

## 🛠️ Adicionando Novos Comandos

### Passo 1: Criar Handler

```python
# src/createagents/presentation/cli/commands/my_command.py
from .base_command import CommandHandler

class MyCommandHandler(CommandHandler):
    def can_handle(self, user_input: str) -> bool:
        return self._normalize_input(user_input) in self.get_aliases()

    def execute(self, agent: 'CreateAgent', user_input: str) -> None:
        # Sua lógica aqui
        result = self._my_logic(agent)
        self._renderer.render_system_message(result)

    def get_aliases(self) -> List[str]:
        return ['/mycommand', 'mycommand']

    def _my_logic(self, agent):
        # Implementação
        return "Resultado do comando"
```

### Passo 2: Registrar Handler

```python
# src/createagents/presentation/cli/application/chat_cli_app.py
def _setup_commands(self) -> None:
    # ...outros comandos...
    self._registry.register(MyCommandHandler(self._renderer))
    # ChatCommandHandler deve ser sempre último
    self._registry.register(ChatCommandHandler(self._renderer))
```

### Passo 3: Exportar (Opcional)

```python
# src/createagents/presentation/cli/commands/__init__.py
from .my_command import MyCommandHandler

__all__ = [
    # ...outros...
    'MyCommandHandler',
]
```

---

## 📊 Testabilidade

A arquitetura permite fácil testabilidade:

```python
import pytest
from unittest.mock import Mock

def test_help_command_handler():
    # Mock renderer
    mock_renderer = Mock()
    handler = HelpCommandHandler(mock_renderer)

    # Mock agent
    mock_agent = Mock()

    # Test can_handle
    assert handler.can_handle("/help") == True
    assert handler.can_handle("other") == False

    # Test execute
    handler.execute(mock_agent, "/help")
    mock_renderer.render_system_message.assert_called_once()
```

---

## 💡 Best Practices

1. **Handler Registration Order**: Específico → Genérico
2. **ChatCommandHandler Last**: Sempre registre como último (fallback)
3. **Use Renderer**: Nunca faça `print()` diretamente, use `self._renderer`
4. **Normalize Input**: Use `_normalize_input()` para comparações
5. **Async Awareness**: Chat é assíncrono, use `asyncio.run()` se necessário

---

## 📚 Próximos Passos

- [Guia Async](async-guide.md)
- [API Reference - Commands](../reference/commands.md)
- [Contribuindo](contribute.md)

---

**Versão:** 0.1.3 | **Atualização:** 01/12/2025
