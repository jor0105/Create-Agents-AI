# Plano: Dashboard de Observabilidade para TraceLogger

## 📋 Análise da Situação Atual

**O que temos:**

- `TraceEntry`: Objeto com todos os dados (trace_id, run_id, inputs, outputs, duration_ms, etc.)
- `FileTraceStore`: Grava em JSONL em `~/.createagents/traces/`
- Formato estruturado e fácil de parsear

**O que falta:**

- Interface visual para explorar os dados
- Agregação/métricas (latência média, taxa de erro, custo)
- Busca/filtros por período, agente, status

---

## 🎯 Objetivo

Criar um dashboard web em Python puro que permita:

1. **Listar** todas as execuções (traces)
2. **Visualizar** detalhes de uma execução específica (árvore de chamadas)
3. **Analisar** métricas agregadas (latência, tokens, custos)
4. **Filtrar** por data, agente, status (sucesso/erro)

---

## 🏗️ Arquitetura: Streamlit

**Por que Streamlit:**

- Python puro (0 JavaScript)
- Prototipagem rápida (MVP em 5 dias)
- Deploy simples (`streamlit run dashboard.py`)
- Comunidade ativa e bem documentado

**Limitações conhecidas:**

- Menos customização de UI que React
- Performance pode degradar com 100k+ traces (mitigável com paginação)

---

## 📦 Stack Técnica

### Dependências

```toml
# Adicionar ao pyproject.toml
[tool.poetry.group.dashboard]
optional = true

[tool.poetry.group.dashboard.dependencies]
streamlit = "^1.29.0"
plotly = "^5.18.0"  # Gráficos interativos
pandas = "^2.1.0"   # Manipulação de dados
```

### Instalação

```bash
# Instalar dependências do dashboard
poetry install --with dashboard

# Rodar o dashboard
poetry run streamlit run src/createagents/dashboard/app.py
```

---

## 📝 Plano de Implementação Detalhado

### Fase 1: Leitura de Dados (1 dia)

**Objetivo:** Criar um serviço que leia os JSONL e retorne traces estruturados.

**Arquivo:** `src/createagents/dashboard/services/trace_reader.py`

**Passos:**


**Verificação:**

- [ ] Teste lendo os traces da pasta `~/.createagents/traces/`
- [ ] Confirme que consegue filtrar por data/agente
- [ ] Valide que TraceSummary é criado corretamente

---

### Fase 2: UI - Página de Listagem (1 dia)

**Objetivo:** Tela principal com lista de todas as execuções.

**Arquivo:** `src/createagents/dashboard/app.py`

**Layout:**

```
┌─────────────────────────────────────────────┐
│  🔍 TraceLogger Dashboard                    │
├─────────────────────────────────────────────┤
│  Filtros:                                    │
│  [Agente ▼] [Status ▼] [Data: últimos 7d]  │
├─────────────────────────────────────────────┤
│  Trace ID    | Agente  | Duração | Status   │
│  abc-123     | GPT-4   | 1.2s    | ✅       │
│  def-456     | Llama   | 0.8s    | ❌       │
└─────────────────────────────────────────────┘
```

**Implementação:**

```python
# src/createagents/dashboard/app.py
import streamlit as st
from datetime import date, timedelta
from services.trace_reader import TraceReader

st.set_page_config(page_title="TraceLogger Dashboard", page_icon="🔍", layout="wide")

st.title("🔍 TraceLogger Dashboard")
st.markdown("Visualize e analise traces dos seus agentes de IA")

# Sidebar com filtros
with st.sidebar:
    st.header("Filtros")

    agent_filter = st.selectbox(
        "Agente",
        ["Todos", "GPT-4", "GPT-3.5", "Llama", "Claude"]
    )

    status_filter = st.selectbox(
        "Status",
        ["Todos", "Sucesso", "Erro"]
    )

    date_range = st.date_input(
        "Período",
        value=(date.today() - timedelta(7), date.today()),
        max_value=date.today()
    )

# Main content
reader = TraceReader()

# Aplicar filtros
traces = reader.list_traces(
    since=date_range[0] if len(date_range) > 0 else None,
    agent_name=None if agent_filter == "Todos" else agent_filter,
    status=None if status_filter == "Todos" else status_filter.lower()
)

# Mostrar métricas rápidas
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Traces", len(traces))
col2.metric("Taxa de Sucesso", f"{sum(1 for t in traces if t.status == 'success') / len(traces) * 100:.1f}%" if traces else "N/A")
col3.metric("Duração Média", f"{sum(t.total_duration_ms for t in traces) / len(traces) / 1000:.2f}s" if traces else "N/A")
col4.metric("Total de Tokens", f"{sum(t.total_tokens for t in traces):,}" if traces else "0")

# Tabela de traces
st.subheader("Execuções")

if traces:
    # Converter para DataFrame para melhor visualização
    import pandas as pd

    df = pd.DataFrame([{
        "Trace ID": t.trace_id[:8],  # Primeiros 8 caracteres
        "Agente": t.agent_name or "N/A",
        "Início": t.start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "Duração": f"{t.total_duration_ms / 1000:.2f}s",
        "LLM Calls": t.total_llm_calls,
        "Tool Calls": t.total_tool_calls,
        "Tokens": f"{t.total_tokens:,}",
        "Status": "✅" if t.status == "success" else "❌"
    } for t in traces])

    # Mostrar tabela com seleção
    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # Se uma linha foi selecionada, mostrar detalhes
    if event.selection.rows:
        selected_idx = event.selection.rows[0]
        selected_trace = traces[selected_idx]

        st.divider()
        st.subheader(f"Detalhes do Trace: {selected_trace.trace_id[:8]}")

        # Aqui vai o código da Fase 3
        st.info("Detalhes do trace serão implementados na Fase 3")
else:
    st.info("Nenhum trace encontrado para os filtros selecionados.")
```

**Verificação:**

- [ ] Os filtros funcionam corretamente?
- [ ] A tabela mostra os dados corretamente?
- [ ] As métricas estão calculadas corretamente?
- [ ] O design está limpo e intuitivo?

---

### Fase 3: UI - Detalhes do Trace (1 dia)

**Objetivo:** Ao selecionar um trace na lista, mostrar a árvore de execução (waterfall).

**Arquivo:** `src/createagents/dashboard/components/trace_detail.py`

**Layout:**

```
┌─────────────────────────────────────────────┐
│  Trace: abc-123 | Agente: GPT-4 | 1.2s      │
├─────────────────────────────────────────────┤
│  Timeline (Waterfall):                       │
│  ┌─ Chat (1200ms) ──────────────────────┐  │
│  │  ├─ LLM Request (800ms) ───────────┐ │  │
│  │  └─ Tool: web_search (400ms) ──┐   │ │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  📥 Inputs:                                  │
│  User: "Busque notícias sobre IA"            │
│                                              │
│  📤 Outputs:                                 │
│  Assistant: "Encontrei 5 artigos..."         │
└─────────────────────────────────────────────┘
```

**Implementação:**

```python
# src/createagents/dashboard/components/trace_detail.py
import streamlit as st
import plotly.express as px
import pandas as pd
from typing import List
from ...domain.value_objects.tracing import TraceEntry

def render_trace_detail(trace_id: str, entries: List[TraceEntry]):
    """Renderiza os detalhes de um trace específico."""

    # Header
    st.markdown(f"### Trace ID: `{trace_id}`")

    # Métricas do trace
    col1, col2, col3 = st.columns(3)

    total_duration = max(e.duration_ms or 0 for e in entries if e.duration_ms)
    llm_calls = sum(1 for e in entries if e.event == "llm.request")
    tool_calls = sum(1 for e in entries if e.event == "tool.call")

    col1.metric("Duração Total", f"{total_duration / 1000:.2f}s")
    col2.metric("Chamadas LLM", llm_calls)
    col3.metric("Chamadas de Tools", tool_calls)

    # Timeline (Waterfall Chart)
    st.subheader("📊 Timeline de Execução")

    # Preparar dados para o gráfico
    timeline_data = []
    for entry in entries:
        if entry.duration_ms:
            timeline_data.append({
                "Operation": f"{entry.operation} ({entry.event})",
                "Start": entry.timestamp,
                "End": entry.timestamp + timedelta(milliseconds=entry.duration_ms),
                "Duration": entry.duration_ms,
                "Type": entry.run_type
            })

    if timeline_data:
        df_timeline = pd.DataFrame(timeline_data)

        fig = px.timeline(
            df_timeline,
            x_start="Start",
            x_end="End",
            y="Operation",
            color="Type",
            hover_data=["Duration"],
            title="Execução ao longo do tempo"
        )

        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=400)

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado de timeline disponível.")

    # Detalhes de entradas/saídas
    st.subheader("📥 Inputs & Outputs")

    for entry in entries:
        with st.expander(f"{entry.event} - {entry.timestamp.strftime('%H:%M:%S.%f')[:-3]}"):
            col_in, col_out = st.columns(2)

            with col_in:
                st.markdown("**Inputs:**")
                if entry.inputs:
                    st.json(entry.inputs)
                else:
                    st.text("N/A")

            with col_out:
                st.markdown("**Outputs:**")
                if entry.outputs:
                    st.json(entry.outputs)
                else:
                    st.text("N/A")

            # Metadata adicional
            if entry.data:
                st.markdown("**Metadata:**")
                st.json(entry.data)
```

**Integração no `app.py`:**

```python
# Adicionar no final do app.py, após a seleção de trace
if event.selection.rows:
    selected_idx = event.selection.rows[0]
    selected_trace = traces[selected_idx]

    st.divider()

    # Buscar todos os entries do trace
    entries = reader.get_trace(selected_trace.trace_id)

    # Renderizar detalhes
    from components.trace_detail import render_trace_detail
    render_trace_detail(selected_trace.trace_id, entries)
```

**Verificação:**

- [ ] O waterfall chart mostra a hierarquia correta?
- [ ] Os inputs/outputs são exibidos de forma legível?
- [ ] Os tempos no gráfico correspondem aos dados reais?

---

### Fase 4: Métricas Agregadas (1 dia)

**Objetivo:** Dashboard de métricas gerais.

**Arquivo:** `src/createagents/dashboard/components/metrics_panel.py`

**Layout:**

```
┌─────────────────────────────────────────────┐
│  📊 Métricas (últimos 7 dias)                │
├─────────────────────────────────────────────┤
│  Total de Execuções: 142                     │
│  Taxa de Sucesso: 94.3%                      │
│  Latência Média: 1.1s (p95: 2.3s)            │
│  Tokens Usados: 1.2M                         │
│                                              │
│  [Gráfico de latência por dia]               │
│  [Gráfico de taxa de erro por dia]           │
└─────────────────────────────────────────────┘
```

**Implementação:**

```python
# src/createagents/dashboard/services/metrics_calculator.py
from typing import List
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class AggregatedMetrics:
    total_traces: int
    success_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    total_tokens: int
    latency_by_day: pd.DataFrame
    error_rate_by_day: pd.DataFrame

class MetricsCalculator:
    @staticmethod
    def calculate(traces: List[TraceSummary]) -> AggregatedMetrics:
        if not traces:
            return AggregatedMetrics(
                total_traces=0,
                success_rate=0.0,
                avg_latency_ms=0.0,
                p95_latency_ms=0.0,
                total_tokens=0,
                latency_by_day=pd.DataFrame(),
                error_rate_by_day=pd.DataFrame()
            )

        # Calcular métricas básicas
        total = len(traces)
        successes = sum(1 for t in traces if t.status == "success")
        success_rate = (successes / total) * 100

        latencies = [t.total_duration_ms for t in traces]
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = pd.Series(latencies).quantile(0.95)

        total_tokens = sum(t.total_tokens for t in traces)

        # Métricas por dia
        df = pd.DataFrame([{
            "date": t.start_time.date(),
            "latency": t.total_duration_ms,
            "success": 1 if t.status == "success" else 0
        } for t in traces])

        latency_by_day = df.groupby("date")["latency"].mean().reset_index()
        error_rate_by_day = df.groupby("date")["success"].apply(
            lambda x: (1 - x.mean()) * 100
        ).reset_index()

        return AggregatedMetrics(
            total_traces=total,
            success_rate=success_rate,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            total_tokens=total_tokens,
            latency_by_day=latency_by_day,
            error_rate_by_day=error_rate_by_day
        )
```

```python
# src/createagents/dashboard/components/metrics_panel.py
import streamlit as st
import plotly.express as px
from services.metrics_calculator import MetricsCalculator

def render_metrics_panel(traces):
    """Renderiza o painel de métricas agregadas."""

    st.header("📊 Métricas Agregadas")

    calculator = MetricsCalculator()
    metrics = calculator.calculate(traces)

    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total de Execuções", metrics.total_traces)
    col2.metric("Taxa de Sucesso", f"{metrics.success_rate:.1f}%")
    col3.metric(
        "Latência Média",
        f"{metrics.avg_latency_ms / 1000:.2f}s",
        delta=None,
        help=f"P95: {metrics.p95_latency_ms / 1000:.2f}s"
    )
    col4.metric("Total de Tokens", f"{metrics.total_tokens:,}")

    # Gráficos
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Latência por Dia")
        if not metrics.latency_by_day.empty:
            fig_latency = px.line(
                metrics.latency_by_day,
                x="date",
                y="latency",
                markers=True,
                labels={"latency": "Latência (ms)", "date": "Data"}
            )
            st.plotly_chart(fig_latency, use_container_width=True)
        else:
            st.info("Sem dados suficientes.")

    with col_right:
        st.subheader("Taxa de Erro por Dia")
        if not metrics.error_rate_by_day.empty:
            fig_error = px.bar(
                metrics.error_rate_by_day,
                x="date",
                y="success",
                labels={"success": "Taxa de Erro (%)", "date": "Data"},
                color_discrete_sequence=["#ff6b6b"]
            )
            st.plotly_chart(fig_error, use_container_width=True)
        else:
            st.info("Sem dados suficientes.")
```

**Integração no `app.py`:**

```python
# Adicionar após os filtros e antes da lista de traces
from components.metrics_panel import render_metrics_panel

# Mostrar painel de métricas
render_metrics_panel(traces)

st.divider()
```

**Verificação:**

- [ ] As métricas correspondem aos dados reais?
- [ ] Os gráficos são claros e informativos?
- [ ] O P95 está calculado corretamente?

---

### Fase 5: Exportação (0.5 dia)

**Objetivo:** Botão para exportar traces como JSON/CSV.

**Implementação:**

```python
# Adicionar no app.py após a tabela de traces
if traces:
    st.subheader("📥 Exportar Dados")

    col_json, col_csv = st.columns(2)

    with col_json:
        import json
        json_data = json.dumps(
            [t.__dict__ for t in traces],
            default=str,
            indent=2
        )

        st.download_button(
            label="📄 Exportar como JSON",
            data=json_data,
            file_name=f"traces_{date.today()}.json",
            mime="application/json",
            use_container_width=True
        )

    with col_csv:
        df_export = pd.DataFrame([{
            "trace_id": t.trace_id,
            "agent_name": t.agent_name,
            "start_time": t.start_time,
            "end_time": t.end_time,
            "duration_ms": t.total_duration_ms,
            "status": t.status,
            "llm_calls": t.total_llm_calls,
            "tool_calls": t.total_tool_calls,
            "tokens": t.total_tokens
        } for t in traces])

        csv_data = df_export.to_csv(index=False)

        st.download_button(
            label="📊 Exportar como CSV",
            data=csv_data,
            file_name=f"traces_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
```

**Verificação:**

- [ ] O JSON exportado está bem formatado?
- [ ] O CSV abre corretamente no Excel?

---

## 🚀 Estrutura de Pastas

```
src/createagents/dashboard/
├── __init__.py
├── app.py                    # Entry point do Streamlit
├── services/
│   ├── __init__.py
│   ├── trace_reader.py       # Lê JSONL e retorna TraceSummary
│   └── metrics_calculator.py # Calcula métricas agregadas
├── components/
│   ├── __init__.py
│   ├── trace_detail.py       # Componente de detalhes do trace
│   └── metrics_panel.py      # Componente de métricas
└── utils/
    ├── __init__.py
    └── formatters.py         # Helpers (formatar duração, etc)
```

---

## ✅ Checklist de Execução

### Setup Inicial

- [ ] Criar branch `feature/observability-dashboard`
- [ ] Adicionar dependências ao `pyproject.toml`:

```toml
[tool.poetry.group.dashboard]
optional = true

[tool.poetry.group.dashboard.dependencies]
streamlit = "^1.29.0"
plotly = "^5.18.0"
pandas = "^2.1.0"
```

- [ ] Rodar `poetry install --with dashboard`
- [ ] Criar estrutura de pastas

### Fase 1: Backend (1 dia)

- [ ] Criar `src/createagents/dashboard/services/trace_reader.py`
- [ ] Implementar `TraceReader.list_traces()`
- [ ] Implementar `TraceReader.get_trace()`
- [ ] Criar modelo `TraceSummary` (se necessário)
- [ ] Testar com dados reais da pasta `~/.createagents/traces/`

### Fase 2: Lista de Traces (1 dia)

- [ ] Criar `src/createagents/dashboard/app.py`
- [ ] Implementar sidebar com filtros
- [ ] Implementar tabela de traces
- [ ] Adicionar métricas rápidas no topo
- [ ] Testar filtros (agente, status, data)

### Fase 3: Detalhes do Trace (1 dia)

- [ ] Criar `src/createagents/dashboard/components/trace_detail.py`
- [ ] Implementar waterfall chart com Plotly
- [ ] Implementar visualização de inputs/outputs
- [ ] Integrar no `app.py`
- [ ] Testar seleção de trace e visualização

### Fase 4: Métricas Agregadas (1 dia)

- [ ] Criar `src/createagents/dashboard/services/metrics_calculator.py`
- [ ] Implementar cálculo de métricas
- [ ] Criar `src/createagents/dashboard/components/metrics_panel.py`
- [ ] Adicionar gráficos de latência e erro
- [ ] Integrar no `app.py`

### Fase 5: Exportação (0.5 dia)

- [ ] Implementar botão de exportação JSON
- [ ] Implementar botão de exportação CSV
- [ ] Testar downloads

### Polimento (0.5 dia)

- [ ] Adicionar loading states
- [ ] Melhorar mensagens de erro
- [ ] Adicionar tooltips explicativos
- [ ] Revisar responsividade
- [ ] Escrever README do dashboard

### Testes Finais

- [ ] Testar com dataset vazio
- [ ] Testar com 100+ traces
- [ ] Testar todos os filtros combinados
- [ ] Validar métricas contra cálculos manuais

---

## 🎨 Melhorias Futuras (v2)

### Prioridade Alta

1. **Paginação**: Implementar paginação para datasets grandes (1000+ traces)
2. **Busca Full-Text**: Poder buscar por conteúdo de prompts/respostas
3. **Cache**: Usar `@st.cache_data` para evitar reler JSONL toda hora

### Prioridade Média

4. **Alertas**: Notificar quando taxa de erro > 5%
5. **Comparação**: Comparar performance entre versões do agente
6. **Custo**: Integrar cálculo de custo por modelo (tokens × preço)

### Prioridade Baixa

7. **Banco de Dados**: Migrar de JSONL para PostgreSQL/SQLite para queries mais rápidas
8. **Autenticação**: Adicionar login se for expor publicamente
9. **Dark Mode**: Tema escuro

---

## 📊 Estimativa de Tempo

| Fase          | Tempo      | Descrição                  |
| ------------- | ---------- | -------------------------- |
| 1. Backend    | 1 dia      | TraceReader + TraceSummary |
| 2. Lista      | 1 dia      | UI de listagem com filtros |
| 3. Detalhes   | 1 dia      | UI de trace individual     |
| 4. Métricas   | 1 dia      | Dashboard agregado         |
| 5. Exportação | 0.5 dia    | Botões de download         |
| Polimento     | 0.5 dia    | UX, erros, README          |
| **Total**     | **5 dias** | MVP funcional              |

---

## 🔧 Comandos Úteis

### Desenvolvimento

```bash
# Instalar dependências
poetry install --with dashboard

# Rodar o dashboard
poetry run streamlit run src/createagents/dashboard/app.py

# Rodar com reload automático (padrão)
# Streamlit detecta mudanças automaticamente

# Acessar em: http://localhost:8501
```

### Deploy (Opcional)

```bash
# Via Streamlit Cloud (grátis)
# 1. Fazer push para GitHub
# 2. Conectar repo no https://share.streamlit.io/
# 3. Configurar entry point: src/createagents/dashboard/app.py

# Via Docker
docker build -t createagents-dashboard .
docker run -p 8501:8501 createagents-dashboard
```

---

## 🐛 Troubleshooting

### Problema: JSONL files não encontrados

**Solução:** Verificar se a pasta `~/.createagents/traces/` existe e contém arquivos `.jsonl`.

### Problema: Gráfico de waterfall vazio

**Solução:** Verificar se os `TraceEntry` têm `duration_ms` populado. Alguns eventos podem não ter duração.

### Problema: Performance lenta com muitos traces

**Solução:**

1. Adicionar paginação
2. Usar `@st.cache_data` para cachear leitura de JSONL
3. Limitar `list_traces()` a 50 resultados por padrão

---

## 📚 Referências

- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)
- [Pandas](https://pandas.pydata.org/docs/)

---

**Autor:** Senior Developer
**Data:** 2025-12-03
**Status:** Pronto para implementação
