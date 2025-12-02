# Referência de Comandos CLI

Referência completa de todos os comandos disponíveis na CLI interativa do CreateAgents AI.

---

## 📋 Visão Geral

A CLI oferece **7 comandos integrados** para controle total do agente:

| Comando     | Aliases           | Descrição                         |
| ----------- | ----------------- | --------------------------------- |
| `/help`     | `/help`, `help`   | Exibe ajuda e lista de comandos   |
| `/metrics`  | `/metrics`        | Mostra métricas de performance    |
| `/configs`  | `/configs`        | Exibe configurações do agente     |
| `/tools`    | `/tools`          | Lista ferramentas disponíveis     |
| `/clear`    | `/clear`, `clear` | Limpa histórico de conversação    |
| **Chat**    | (qualquer texto)  | Envia mensagem ao agente (padrão) |
| `exit/quit` | `exit`, `quit`    | Encerra a aplicação               |

---

## 🔧 Comandos Detalhados

### `/help` - Ajuda

**Descrição**: Exibe lista de comandos disponíveis e suas descrições.

**Aliases**: `/help`, `help`

**Uso**:

```
Você: /help
```

**Saída**:

```
Available Commands:

• /metrics  → Show agent performance metrics and statistics
• /configs  → Display current agent configuration settings
• /tools    → List all available tools and their descriptions
• /clear    → Clear conversation history and start fresh
• /help     → Show this help message

Type 'exit' or 'quit' to close the application.
```

---

### `/metrics` - Métricas de Performance

**Descrição**: Mostra estatísticas detalhadas de todas as chamadas realizadas.

**Aliases**: `/metrics`, `metrics`

**Uso**:

```
Você: /metrics
```

**Saída OpenAI**:

```
📊 Métricas de Performance

Chamada #1 | ✅ Sucesso
  └─ Modelo: gpt-4
  └─ Latência: 1,234ms
  └─ Tokens: 250 (prompt: 100, completion: 150)

Chamada #2 | ✅ Sucesso
  └─ Modelo: gpt-4
  └─ Latência: 987ms
  └─ Tokens: 180 (prompt: 80, completion: 100)

📈 Estatísticas Gerais
  Total de chamadas: 2
  Taxa de sucesso: 100%
  Latência média: 1,110ms
  Total de tokens: 430
```

**Saída Ollama** (métricas adicionais):

```
📊 Métricas de Performance

Chamada #1 | ✅ Sucesso
  └─ Modelo: llama3.2:latest
  └─ Latência: 2,345ms
  └─ Tokens: 150 (prompt: 50, completion: 100)
  └─ Load duration: 145ms
  └─ Prompt eval duration: 234ms
  └─ Eval duration: 1,966ms

📈 Estatísticas Gerais
  Total de chamadas: 1
  Taxa de sucesso: 100%
  Latência média: 2,345ms
  Total de tokens: 150
```

**Informações Exibidas**:

- Número da chamada
- Status (✅ Sucesso / ❌ Erro)
- Modelo usado
- Latência em milissegundos
- Tokens (total, prompt, completion)
- **Ollama**: Durations (load, prompt_eval, eval)
- Estatísticas agregadas

---

### `/configs` - Configurações do Agente

**Descrição**: Exibe todas as configurações atuais do agente.

**Aliases**: `/configs`, `configs`

**Uso**:

```
Você: /configs
```

**Saída**:

```
⚙️ Configurações do Agente

Nome: Code Assistant
Provider: openai
Modelo: gpt-4

📝 Instruções:
Você é um especialista em Python. Sempre forneça exemplos de código.

🔧 Parâmetros:
  • temperature: 0.7
  • max_tokens: 2000
  • top_p: 0.9

🛠️ Ferramentas: 2 disponíveis
  • currentdate
  • readlocalfile

💬 Histórico: 5 mensagens (máximo: 20)
```

**Informações Exibidas**:

- Nome do agente
- Provider e modelo
- Instruções do sistema
- Parâmetros de configuração (temperature, max_tokens, etc.)
- Ferramentas disponíveis
- Tamanho do histórico

---

### `/tools` - Ferramentas Disponíveis

**Descrição**: Lista todas as ferramentas que o agente pode usar.

**Aliases**: `/tools`, `tools`

**Uso**:

```
Você: /tools
```

**Saída**:

```
🛠️ Ferramentas Disponíveis

• currentdate
  └─ Retorna a data e hora atual em qualquer timezone. Suporta offsets UTC e nomes de timezone.

• readlocalfile
  └─ Lê e extrai conteúdo de arquivos locais incluindo PDF, Excel (xlsx), CSV, Parquet, JSON, YAML e TXT.
```

**Informações Exibidas**:

- Nome da ferramenta
- Descrição detalhada do que ela faz

---

### `/clear` - Limpar Histórico

**Descrição**: Remove todo o histórico de conversação e inicia uma nova sessão.

**Aliases**: `/clear`, `clear`

**Uso**:

```
Você: /clear
```

**Saída**:

```
🗑️ Histórico limpo! Iniciando nova conversa.
```

**Efeito**:

- Remove todas as mensagens do histórico
- Preserva configurações do agente
- Próxima mensagem não terá contexto anterior

**Quando Usar**:

- Mudar completamente de assunto
- Resetar contexto após erro
- Liberar memória em conversas longas

---

### Chat (Comando Padrão)

**Descrição**: Envia mensagem ao agente de IA. Este é o comando padrão - qualquer texto que não seja um comando especial é enviado ao agente.

**Uso**:

```
Você: Explique o que é Clean Architecture
```

**Saída**:

```
✨ [Resposta em streaming]

Clean Architecture é um padrão de design de software que separa...
[texto continua em tempo real]
```

**Comportamento**:

- Processa entrada com streaming em tempo real
- Executa ferramentas automaticamente se necessário
- Mantém contexto com histórico de conversação
- Adiciona mensagem ao histórico

---

### `exit` / `quit` - Sair

**Descrição**: Encerra a aplicação CLI.

**Aliases**: `exit`, `quit`

**Uso**:

```
Você: exit
```

ou

```
Você: quit
```

**Saída**:

```
👋 Até logo! Obrigado por usar CreateAgents AI.
```

**Efeito**:

- Encerra o loop da CLI
- Finaliza programa gracefully
- Não salva histórico (sessão é temporária)

---

## 🎨 Formatação e Interface

### Cores

Comandos usam esquema de cores profissional:

- **Prompts**: Cyan
- **Respostas**: Verde
- **Sistema**: Amarelo
- **Erros**: Vermelho
- **Comandos**: Magenta

### Indicadores

Durante processamento:

```
⏳ Processando...
✨ [Agente está digitando...]
```

---

## 🔄 Fluxo de Comandos

```
User Input
  ↓
CommandRegistry.find_handler()
  ↓
¿É comando especial? → Sim → Handler específico
  ↓                         (/help, /metrics, etc.)
  Não
  ↓
ChatCommandHandler (padrão)
  ↓
Streaming Response
```

---

## 💡 Exemplos de Uso

### Fluxo Típico de Sessão

```
# Iniciar CLI
Você: /help
[Vê comandos disponíveis]

Você: /tools
[Verifica ferramentas]

Você: Que dia é hoje?
[Agent usa CurrentDateTool e responde]

Você: /metrics
[Vê estatísticas da chamada]

Você: /configs
[Revisa configurações]

Você: /clear
[Limpa histórico para novo tópico]

Você: Agora vamos falar sobre Python
[Nova conversa]

Você: exit
[Sai da CLI]
```

### Debugging

```bash
Você: [mensagem ao agente]
[Resposta parece estranha]

Você: /configs
[Verificar instruções e parâmetros]

Você: /tools
[Verificar se tool correto está disponível]

Você: /metrics
[Ver latência e tokens para identificar problemas]

Você: /clear
[Resetar contexto e tentar novamente]
```

---

## 🐛 Troubleshooting

### Comando não reconhecido

**Problema**: Digitou comando errado

**Solução**: Use `/help` para ver lista correta

### Métricas vazias

**Problema**: `/metrics` não mostra nada

**Solução**: Faça pelo menos uma chamada ao agente antes

### Clear não funciona

**Problema**: Histórico não limpa

**Solução**: Verifique que não há erro de digitação (`/clear`, não `/clean`)

---

## 📚 Veja Também

- [Guia de Uso da CLI](../user-guide/cli-usage.md)
- [Arquitetura CLI](../dev-guide/cli-architecture.md)
- [API Reference](api.md)

---

**Versão:** 0.1.3 | **Atualização:** 01/12/2025
