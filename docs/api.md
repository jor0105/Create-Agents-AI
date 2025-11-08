# 📚 API Reference

Documentação completa da API pública do **AI Agent Creator**.

---

## 🤖 AIAgent

O controller principal para interação com agentes de IA.

### Construtor

```python
AIAgent(
    provider: str,
    model: str,
    name: Optional[str] = None,
    instructions: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    tools: Optional[Sequence[Union[str, BaseTool]]] = None,
    history_max_size: int = 10
)
```

**Parâmetros:**

| Parâmetro          | Tipo   | Descrição                                                 | Obrigatório |
| ------------------ | ------ | --------------------------------------------------------- | ----------- |
| `provider`         | `str`  | Provider de IA: `"openai"` ou `"ollama"`                  | ✅ Sim      |
| `model`            | `str`  | Nome do modelo (ex: `"gpt-4"`, `"llama2"`)                | ✅ Sim      |
| `name`             | `str`  | Nome do agente                                            | ❌ Não      |
| `instructions`     | `str`  | Instruções/personalidade do agente                        | ❌ Não      |
| `config`           | `dict` | Configurações do modelo (temperature, max_tokens, etc)    | ❌ Não      |
| `tools`            | `list` | Lista de ferramentas: `["current_date", "readlocalfile"]` | ❌ Não      |
| `history_max_size` | `int`  | Tamanho máximo do histórico (padrão: 10)                  | ❌ Não      |

**Exemplo:**

```python
from src.presentation import AIAgent

agent = AIAgent(
    provider="openai",
    model="gpt-4",
    instructions="Você é um assistente técnico",
    config={"temperature": 0.7, "max_tokens": 2000},
    tools=["current_date"],
    history_max_size=20
)
```

---

### Métodos

#### chat()

Envia mensagem ao agente e retorna resposta.

```python
def chat(message: str) -> str
```

**Parâmetros:**

- `message` (str): Mensagem do usuário

**Retorna:** `str` - Resposta do agente

**Exemplo:**

```python
response = agent.chat("Como criar uma função em Python?")
print(response)
```

---

#### get_configs()

Retorna configurações e histórico do agente.

```python
def get_configs() -> Dict[str, Any]
```

**Retorna:** `dict` com:

- `name`: Nome do agente
- `model`: Modelo usado
- `provider`: Provider (openai/ollama)
- `instructions`: Instruções
- `history`: Lista de mensagens
- `tools`: Ferramentas disponíveis
- `config`: Configurações do modelo

**Exemplo:**

```python
config = agent.get_configs()
print(f"Modelo: {config['model']}")
print(f"Histórico: {len(config['history'])} mensagens")
```

---

#### clear_history()

Limpa o histórico de mensagens.

```python
def clear_history() -> None
```

**Exemplo:**

```python
agent.clear_history()
print("Histórico limpo!")
```

---

#### get_metrics()

Retorna métricas de performance.

```python
def get_metrics() -> List[ChatMetrics]
```

**Retorna:** `List[ChatMetrics]` com:

- `response_time` (float): Tempo de resposta em segundos
- `tokens_used` (int): Tokens consumidos
- `status` (str): Status da requisição
- `timestamp` (datetime): Momento da execução

**Exemplo:**

```python
metrics = agent.get_metrics()
for m in metrics:
    print(f"Tempo: {m.response_time:.2f}s, Tokens: {m.tokens_used}")
```

---

#### export_metrics_json()

Exporta métricas em formato JSON.

```python
def export_metrics_json(filepath: Optional[str] = None) -> str
```

**Parâmetros:**

- `filepath` (str, opcional): Caminho para salvar

**Retorna:** JSON string

**Exemplo:**

```python
# Salvar em arquivo
agent.export_metrics_json("metrics.json")

# Obter como string
json_data = agent.export_metrics_json()
```

---

#### export_metrics_prometheus()

Exporta métricas em formato Prometheus.

```python
def export_metrics_prometheus(filepath: Optional[str] = None) -> str
```

**Parâmetros:**

- `filepath` (str, opcional): Caminho para salvar

**Retorna:** String formato Prometheus

**Exemplo:**

```python
agent.export_metrics_prometheus("metrics.prom")
```

---

## 🛠️ Ferramentas (Tools)

### Ferramentas Disponíveis

#### CurrentDateTool

Obtém data/hora em qualquer timezone.

**Nome:** `"current_date"`

**Uso:**

```python
agent = AIAgent(
    provider="openai",
    model="gpt-4",
    tools=["current_date"]
)

response = agent.chat("Que dia é hoje?")
```

**Ações:**

- `date`: Data (YYYY-MM-DD)
- `time`: Hora (HH:MM:SS)
- `datetime`: Data e hora
- `timestamp`: Unix timestamp
- `date_with_weekday`: Data com dia da semana

---

#### ReadLocalFileTool

Lê arquivos locais em múltiplos formatos.

**Nome:** `"readlocalfile"`

**Requer:** `poetry install -E file-tools`

**Formatos:**

- Texto: TXT, MD, CSV, JSON, YAML
- Documentos: PDF
- Planilhas: Excel (XLS, XLSX), Parquet

**Uso:**

```python
agent = AIAgent(
    provider="openai",
    model="gpt-4",
    tools=["readlocalfile"]
)

response = agent.chat("Leia o arquivo report.pdf")
```

**Limites:**

- Tamanho máximo: 100MB
- Tokens máximos: 30.000

---

## 📊 Configurações do Modelo

Parâmetros para controlar o comportamento do modelo (OpenAI):

```python
config = {
    "temperature": 0.7,        # 0-1: Criatividade
    "max_tokens": 2000,        # Limite de tokens
    "top_p": 0.9,              # 0-1: Nucleus sampling
    "frequency_penalty": 0,    # 0-2: Reduz repetição
    "presence_penalty": 0,     # 0-2: Encoraja novos tópicos
}

agent = AIAgent(provider="openai", model="gpt-4", config=config)
```

**Parâmetros:**

| Nome                | Faixa | Descrição                                            |
| ------------------- | ----- | ---------------------------------------------------- |
| `temperature`       | 0-1   | Controla aleatoriedade. 0=determinístico, 1=criativo |
| `max_tokens`        | 1-∞   | Limite de tokens na resposta                         |
| `top_p`             | 0-1   | Nucleus sampling                                     |
| `frequency_penalty` | 0-2   | Penalidade por repetição                             |
| `presence_penalty`  | 0-2   | Encoraja novos tópicos                               |

---

## 💡 Exemplos de Uso

```python
from src.presentation import AIAgent

# Básico
agent = AIAgent(provider="openai", model="gpt-4")
response = agent.chat("Olá!")

# Com ferramentas
agent = AIAgent(
    provider="openai",
    model="gpt-4",
    tools=["current_date", "readlocalfile"]
)

# Local (Ollama)
agent = AIAgent(provider="ollama", model="llama2")

# Personalizado
agent = AIAgent(
    provider="openai",
    model="gpt-4",
    instructions="Seja técnico",
    config={"temperature": 0.3},
    history_max_size=50
)
```

---

**Versão:** 0.1.0 | **Atualização:** Novembro 2025
