# 🛠️ Ferramentas (Tools)

Este guia explica como criar e usar ferramentas com seus agentes de IA no CreateAgents.

---

## 📦 Visão Geral

Ferramentas são **capacidades adicionais** que seus agentes podem usar para executar tarefas específicas como buscar informações, fazer cálculos, ler arquivos, chamar APIs, etc.

### Criando Ferramentas com `@tool`

O decorator `@tool` é a forma **principal e recomendada** de criar ferramentas no CreateAgents. Ele automaticamente:

- Infere o nome da ferramenta a partir do nome da função
- Extrai a descrição da docstring (Google Style)
- Gera o schema de parâmetros a partir dos type hints
- Cria validação automática via Pydantic

```python
from createagents import tool

@tool
def search(query: str, max_results: int = 10) -> str:
    """Buscar informações na web.

    Args:
        query: A consulta de busca para executar.
        max_results: Número máximo de resultados.

    Returns:
        Resultados da busca formatados.
    """
    return f"Resultados para: {query}"
```

---

## 🎯 Modos de Uso do Decorator `@tool`

### 1. Uso Básico (Sem Parênteses)

O modo mais simples - o nome e descrição são inferidos automaticamente:

```python
from createagents import tool

@tool
def calculator(expression: str) -> str:
    """Calcular uma expressão matemática.

    Args:
        expression: Expressão matemática para calcular.

    Returns:
        Resultado do cálculo.
    """
    return str(eval(expression))
```

### 2. Nome Customizado

Para usar um nome diferente do nome da função:

```python
@tool("weather_lookup")
def get_weather_data(city: str) -> str:
    """Consultar previsão do tempo.

    Args:
        city: Nome da cidade.

    Returns:
        Previsão do tempo.
    """
    return f"Tempo em {city}: Ensolarado"
```

### 3. Com Schema Pydantic Explícito

Para validação mais complexa ou quando você quer controle total sobre o schema:

```python
from pydantic import BaseModel, Field
from createagents import tool

class SearchInput(BaseModel):
    """Schema de entrada para busca."""
    query: str = Field(description="Consulta de busca")
    max_results: int = Field(default=10, ge=1, le=100, description="Máximo de resultados")
    include_images: bool = Field(default=False, description="Incluir imagens")

@tool(args_schema=SearchInput)
def advanced_search(query: str, max_results: int = 10, include_images: bool = False) -> str:
    """Busca avançada com validação.

    Args:
        query: Consulta de busca.
        max_results: Máximo de resultados (1-100).
        include_images: Se deve incluir imagens.

    Returns:
        Resultados da busca.
    """
    return f"Buscando: {query}, max={max_results}, images={include_images}"
```

### 4. Funções Assíncronas

O decorator funciona perfeitamente com funções `async`:

```python
import httpx
from createagents import tool

@tool
async def fetch_url(url: str) -> str:
    """Buscar conteúdo de uma URL.

    Args:
        url: URL para buscar.

    Returns:
        Conteúdo da resposta.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

### 5. Todas as Opções

Você pode combinar múltiplas opções:

```python
@tool(
    name="custom_search",
    description="Busca customizada com configurações avançadas",
    args_schema=SearchInput,
    parse_docstring=False,
    return_direct=True
)
def search_impl(query: str, max_results: int = 10, include_images: bool = False) -> str:
    """Esta docstring será ignorada pois parse_docstring=False."""
    return f"Resultados para: {query}"
```

---

## 💉 Argumentos Injetados (InjectedToolArg)

Às vezes você precisa passar informações do runtime para a ferramenta que não devem ser expostas ao LLM. Use os marcadores de injeção:

### InjectedToolCallId

Recebe o ID único da chamada da ferramenta:

```python
from typing import Annotated
from createagents import tool
from createagents.domain.value_objects import InjectedToolCallId

@tool
def traceable_action(
    action: str,
    call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """Ação rastreável com ID de chamada.

    Args:
        action: Ação a executar.
        call_id: ID da chamada (injetado pelo runtime).

    Returns:
        Resultado com trace ID.
    """
    print(f"[{call_id}] Executando: {action}")
    return f"Ação '{action}' executada com sucesso"
```

### InjectedState

Recebe o estado atual do agente:

```python
from typing import Annotated, Dict, Any
from createagents import tool
from createagents.domain.value_objects import InjectedState

@tool
def user_action(
    action: str,
    state: Annotated[Dict[str, Any], InjectedState]
) -> str:
    """Executar ação com contexto do usuário.

    Args:
        action: Ação a executar.
        state: Estado do agente (injetado pelo runtime).

    Returns:
        Resultado personalizado.
    """
    user = state.get("current_user", "anônimo")
    return f"Usuário {user} executou: {action}"
```

### Marcador Customizado

Você pode criar seus próprios marcadores:

```python
from createagents.domain.value_objects import InjectedToolArg

class InjectedSessionId(InjectedToolArg):
    """Marcador para ID de sessão injetado."""
    pass

@tool
def session_action(
    data: str,
    session_id: Annotated[str, InjectedSessionId]
) -> str:
    """Ação com sessão.

    Args:
        data: Dados para processar.
        session_id: ID da sessão (injetado).

    Returns:
        Resultado.
    """
    return f"[Session: {session_id}] Processado: {data}"
```

> **Importante:** Parâmetros marcados com `InjectedToolArg` e suas subclasses **NÃO aparecem no schema** enviado ao LLM. O LLM não sabe que eles existem - são puramente internos.

---

## 🎛️ Controlando Seleção de Ferramentas (tool_choice)

O parâmetro `tool_choice` controla como o modelo de IA seleciona ferramentas:

### Modos Disponíveis

| Modo               | Descrição                                      |
| ------------------ | ---------------------------------------------- |
| `"auto"`           | Modelo decide se/qual ferramenta usar (padrão) |
| `"none"`           | Modelo não pode usar ferramentas               |
| `"required"`       | Modelo deve usar pelo menos uma ferramenta     |
| `"<nome_da_tool>"` | Força uso de uma ferramenta específica         |

### Exemplos de Uso

```python
import asyncio
from createagents import CreateAgent, tool

@tool
def calculator(expression: str) -> str:
    """Calcular expressão matemática."""
    return str(eval(expression))

@tool
def weather(city: str) -> str:
    """Consultar clima."""
    return f"Ensolarado em {city}"

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        tools=[calculator, weather]
    )

    # Modo auto (padrão) - modelo decide
    response = await agent.chat(
        "Quanto é 15 * 7?",
        tool_choice="auto"
    )

    # Forçar uso de ferramenta
    response = await agent.chat(
        "Me diga algo interessante",
        tool_choice="required"
    )

    # Forçar ferramenta específica
    response = await agent.chat(
        "Qualquer coisa sobre São Paulo",
        tool_choice="weather"
    )

    # Desabilitar ferramentas
    response = await agent.chat(
        "Apenas converse comigo",
        tool_choice="none"
    )

asyncio.run(main())
```

### Formato de Dicionário

Você também pode usar o formato de dicionário (compatível com OpenAI):

```python
response = await agent.chat(
    "Calcule algo",
    tool_choice={
        "type": "function",
        "function": {"name": "calculator"}
    }
)
```

---

## 📦 Ferramentas Built-in

O CreateAgents vem com algumas ferramentas prontas para uso.

### ✅ CurrentDateTool (Sempre Disponível)

Obtém data e hora atuais em qualquer timezone.

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        tools=["currentdate"]
    )

    response = await agent.chat("Que dia é hoje?")
    print(response)

asyncio.run(main())
```

**Ações suportadas:**

- `date` - Data (YYYY-MM-DD)
- `time` - Hora (HH:MM:SS)
- `datetime` - Data e hora completos
- `timestamp` - Unix timestamp
- `date_with_weekday` - Data com dia da semana

---

### 🔧 ReadLocalFileTool (Opcional)

Lê arquivos locais em múltiplos formatos.

**Formatos:** TXT, MD, CSV, Excel (XLS/XLSX), PDF, Parquet, JSON, YAML

**Dependências:** `tiktoken`, `unstructured`, `pandas`, `openpyxl`, `pyarrow`, `chardet`

**Instalação:**

```bash
pip install createagents[file-tools]
```

**Uso:**

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        tools=["readlocalfile"]
    )

    resposta = await agent.chat("Leia o arquivo report.pdf e resuma")
    print(resposta)

asyncio.run(main())
```

**Limites:**

- Tamanho máximo: 100MB
- Tokens máximos: Depende da AI utilizada

**Funcionalidades:**

- ✅ Validação de tamanho
- ✅ Detecção automática de encoding
- ✅ Suporte a múltiplos formatos
- ✅ Tratamento robusto de erros

---

## 🚀 Exemplos Completos

### Combinando Tools Built-in e Customizadas

```python
import asyncio
from createagents import CreateAgent, tool

@tool
def calculate(expression: str) -> str:
    """Calcular expressão matemática.

    Args:
        expression: Expressão para calcular.

    Returns:
        Resultado do cálculo.
    """
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Erro: {e}"

@tool
def search_knowledge(topic: str) -> str:
    """Buscar informação sobre um tópico.

    Args:
        topic: Tópico para buscar.

    Returns:
        Informação encontrada.
    """
    # Simular busca
    return f"Informação sobre {topic}: Lorem ipsum..."

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        instructions="Você é um assistente útil com acesso a ferramentas.",
        tools=[
            "currentdate",         # Built-in
            "readlocalfile",       # Built-in (opcional)
            calculate,             # Customizada
            search_knowledge       # Customizada
        ]
    )

    # O agente escolhe automaticamente qual ferramenta usar
    response = await agent.chat("Quanto é 25 * 4?")
    print(response)

    response = await agent.chat("Que horas são em São Paulo?")
    print(response)

asyncio.run(main())
```

### Tool com Pydantic e Validação Complexa

```python
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from createagents import tool

class ProductSearchInput(BaseModel):
    """Schema para busca de produtos."""

    query: str = Field(description="Termo de busca")
    category: Optional[str] = Field(default=None, description="Categoria do produto")
    min_price: float = Field(default=0, ge=0, description="Preço mínimo")
    max_price: float = Field(default=10000, le=100000, description="Preço máximo")
    sort_by: str = Field(default="relevance", description="Ordenação")

    @field_validator("sort_by")
    @classmethod
    def validate_sort(cls, v):
        allowed = ["relevance", "price_asc", "price_desc", "rating"]
        if v not in allowed:
            raise ValueError(f"sort_by deve ser um de: {allowed}")
        return v

@tool(args_schema=ProductSearchInput)
def search_products(
    query: str,
    category: Optional[str] = None,
    min_price: float = 0,
    max_price: float = 10000,
    sort_by: str = "relevance"
) -> str:
    """Buscar produtos no catálogo.

    Args:
        query: Termo de busca.
        category: Categoria do produto.
        min_price: Preço mínimo.
        max_price: Preço máximo.
        sort_by: Ordenação dos resultados.

    Returns:
        Lista de produtos encontrados.
    """
    filters = []
    if category:
        filters.append(f"categoria={category}")
    filters.append(f"preço={min_price}-{max_price}")
    filters.append(f"ordenar={sort_by}")

    return f"Produtos para '{query}': [{', '.join(filters)}]"
```

---

## 📋 Checklist de Instalação

### Instalação Básica ✅

```bash
pip install createagents
```

Inclui:

- [x] Decorator `@tool`
- [x] CurrentDateTool
- [x] Gerenciamento de histórico
- [x] Métricas de performance
- [x] OpenAI e Ollama adapters

### Instalação com File Tools 📁

```bash
pip install createagents[file-tools]
```

Inclui tudo da instalação básica mais:

- [x] ReadLocalFileTool
- [x] Suporte para PDF, Excel, CSV, Parquet

---

## 🔍 Verificar Ferramentas Disponíveis

### Listar Todas as Ferramentas do Agente

```python
from createagents import CreateAgent, tool

@tool
def my_custom_tool(x: int) -> int:
    """Minha ferramenta customizada."""
    return x * 2

agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["currentdate", my_custom_tool]
)

# Todas as ferramentas deste agente
tools = agent.get_all_available_tools()
print("Ferramentas disponíveis:")
for name, description in tools.items():
    print(f"  - {name}: {description[:50]}...")
```

### Listar Apenas Ferramentas do Sistema

```python
# Ferramentas built-in disponíveis globalmente
system_tools = agent.get_system_available_tools()
print("Ferramentas do sistema:")
for name, description in system_tools.items():
    print(f"  - {name}: {description[:50]}...")

# Verificar se uma ferramenta opcional está disponível
if "readlocalfile" in system_tools:
    print("✅ ReadLocalFileTool disponível!")
else:
    print("⚠️ Instale com: pip install createagents[file-tools]")
```

---

## ⚡ Performance

### Uso de Memória

| Instalação     | Memória Base | Com ReadLocalFileTool |
| -------------- | ------------ | --------------------- |
| Básica         | ~50MB        | N/A                   |
| Com file-tools | ~50MB        | ~200MB (quando usada) |

---

## 🤔 FAQ

**P: Por que usar `@tool` ao invés de criar classes?**
R: O decorator `@tool` é mais simples, requer menos código, e automaticamente infere schema e validação. É a forma recomendada para 99% dos casos.

**P: Posso usar o `@tool` com funções já existentes?**
R: Sim! Basta adicionar type hints e uma docstring Google Style.

**P: Como sei quais ferramentas estão disponíveis?**
R: Use `agent.get_all_available_tools()` para listar.

**P: O que acontece se eu tentar usar uma ferramenta não instalada?**
R: Você receberá erro claro: `pip install createagents[file-tools]`

**P: Os argumentos injetados são visíveis para o LLM?**
R: Não. Parâmetros com `InjectedToolArg` são completamente invisíveis para o modelo.

**P: Como forço o modelo a usar uma ferramenta específica?**
R: Use `tool_choice="nome_da_ferramenta"` na chamada `chat()`.

---

**Última atualização:** 02/12/2025
