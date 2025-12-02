# Guia de Uso da CLI Interativa

A CLI (Command-Line Interface) do CreateAgents AI oferece uma interface interativa profissional para conversar com seus agentes de IA.

---

## 🚀 Início Rápido

```python
from createagents import CreateAgent

# Criar agente
agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    name="Assistente",
    instructions="Você é um assistente prestativo",
)

# Iniciar CLI interativa
agent.start_cli()
```

---

## ✨ Recursos

- **🎨 Interface Colorida**: Sintaxe highlight e formatação markdown
- **⚡ Streaming em Tempo Real**: Respostas aparecem token por token
- **🎯 Comandos Integrados**: 7 comandos para controle total
- **🔧 Indicadores de Status**: Mostra quando o agente está pensando
- **📊 Métricas em Tempo Real**: Visualize performance instantaneamente

---

## 📋 Comandos Disponíveis

### `/help` - Ajuda

Exibe lista de comandos disponíveis.

```
Você: /help
```

**Aliases**: `/help`, `help`

### `/metrics` - Métricas

Mostra estatísticas de performance do agente:

- Número de chamadas
- Tokens usados (prompt + completion)
- Latência média
- Taxa de sucesso
- Métricas Ollama: load_duration, prompt_eval_duration, eval_duration

```
Você: /metrics
```

**Aliases**: `/metrics`, `metrics`

**Exemplo de saída**:

```
📊 Métricas de Performance

Chamada #1 | ✅ Sucesso
  └─ Modelo: gpt-4
  └─ Latência: 1,245ms
  └─ Tokens: 150 (prompt: 45, completion: 105)

Chamada #2 | ✅ Sucesso
  └─ Modelo: gpt-4
  └─ Latência: 982ms
  └─ Tokens: 230 (prompt: 110, completion: 120)

📈 Estatísticas Gerais
  Total de chamadas: 2
  Taxa de sucesso: 100%
  Latência média: 1,113ms
  Total de tokens: 380
```

### `/configs` - Configurações

Mostra configurações atuais do agente:

- Nome
- Provider e modelo
- Instruções
- Parâmetros de configuração
- Ferramentas disponíveis
- Tamanho do histórico

```
Você: /configs
```

**Aliases**: `/configs`, `configs`

### `/tools` - Ferramentas

Lista todas as ferramentas disponíveis para o agente.

```
Você: /tools
```

**Aliases**: `/tools`, `tools`

**Exemplo de saída**:

```
🛠️ Ferramentas Disponíveis

• currentdate
  └─ Retorna a data e hora atual em qualquer timezone

• readlocalfile
  └─ Lê e extrai conteúdo de arquivos locais (PDF, Excel, CSV, etc)
```

### `/clear` - Limpar Histórico

Limpa todo o histórico de conversação e inicia uma nova sessão.

```
Você: /clear
```

**Aliases**: `/clear`, `clear`

### Chat Normal

Qualquer texto que não seja um comando é enviado como mensagem ao agente.

```
Você: Explique Clean Architecture
```

O agente responderá com streaming em tempo real.

### `exit` / `quit` - Sair

Encerra a aplicação CLI.

```
Você: exit
```

ou

```
Você: quit
```

---

## 🎨 Interface e Formatação

### Cores e Destaque

A CLI usa um esquema de cores profissional:

- **Prompts**: Cor primária (cyan)
- **Respostas do Agente**: Verde
- **Mensagens do Sistema**: Amarelo
- **Erros**: Vermelho
- **Comandos**: Magenta

### Formatação Markdown

A renderização suporta:

- **Negrito**: `**texto**`
- _Itálico_: `*texto*`
- `Código inline`: `` `código` ``
- Blocos de código com syntax highlighting
- Listas e cabeçalhos

### Indicadores de Status

Durante o processamento:

```
⏳ Processando...
```

Durante streaming:

```
✨ [Agente está digitando...]
```

---

## 💡 Exemplos de Uso

### Exemplo 1: Assistente de Programação

```python
from createagents import CreateAgent

code_assistant = CreateAgent(
    provider="openai",
    model="gpt-4",
    name="Code Expert",
    instructions="Você é um especialista em Python. Sempre forneça exemplos."
)

# Iniciar CLI interativa
code_assistant.start_cli()
```

**Interação**:

```
Você: Como criar um decorator em Python?
[Resposta em streaming...]

Você: /metrics
[Exibe estatísticas da chamada]

Você: /clear
[Limpa histórico para novo tópico]
```

### Exemplo 2: Agente com Ferramentas

```python
from createagents import CreateAgent

agent_with_tools = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["currentdate", "readlocalfile"]
)

# Iniciar CLI
agent_with_tools.start_cli()
```

**Interação**:

```
Você: /tools
[Lista ferramentas disponíveis]

Você: Que dia é hoje?
[Agente usa CurrentDateTool automaticamente]

Você: Leia o arquivo report.pdf
[Agente usa ReadLocalFileTool]
```

### Exemplo 3: Ollama Local

```python
from createagents import CreateAgent

local_agent = CreateAgent(
    provider="ollama",
    model="llama3.2",
    name="Assistente Local"
)

# Iniciar CLI
local_agent.start_cli()
```

---

## 🔧 Personalização

### Usando a CLI Programaticamente

A CLI é iniciada através do método `start_cli()` da facade `CreateAgent`:

```python
from createagents import CreateAgent

agent = CreateAgent(provider="openai", model="gpt-4")
agent.start_cli()  # Inicia loop interativo
```

Internamente, este método:

1. Importa `ChatCLIApplication` da camada de apresentação
2. Instancia a aplicação CLI com o agente
3. Executa o loop principal

---

## 🐛 Troubleshooting

### CLI não inicia

**Problema**: Erro ao chamar `agent.start_cli()`

**Solução**: Certifique-se de que está na versão mais recente:

```bash
pip install --upgrade createagents
```

### Caracteres especiais não aparecem

**Problema**: Emojis ou caracteres Unicode não renderizam

**Solução**: Use um terminal com suporte UTF-8 (Windows Terminal, iTerm2, etc.)

### Streaming muito lento

**Problema**: Tokens aparecem muito devagar

**Solução**:

1. Verifique sua conexão de internet (para OpenAI)
2. Para Ollama, verifique se o modelo está carregado
3. Considere usar um modelo menor/mais rápido

---

## 📚 Próximos Passos

- [Guia de Streaming](streaming-guide.md)
- [Arquitetura CLI (Desenvolvedores)](../dev-guide/cli-architecture.md)
- [API Reference](../reference/commands.md)

---

**Versão:** 0.1.3 | **Atualização:** 01/12/2025
