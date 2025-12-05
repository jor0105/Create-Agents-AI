# Plano de Implementação do Dashboard TraceLogger

## 1. Resumo Executivo

Este documento descreve o plano para construir um **Dashboard de Observabilidade baseado em Streamlit** para o framework `CreateAgentsAI`. O dashboard visualizará os traces gerados pelo sistema `TraceLogger`, oferecendo uma experiência estilo "LangSmith" para depurar, analisar e monitorar o desempenho dos agentes.

**Objetivo**: Fornecer uma visão em tempo real (ou quase real) dos traces de execução do agente, incluindo chamadas de ferramentas, trocas com LLM, latência, custos e uso de tokens, consumindo os logs JSONL produzidos pelo `FileTraceStore`.

## 2. Arquitetura e Fluxo de Dados

### 2.1 Fonte de Dados

- **Formato**: JSON Lines (`.jsonl`).
- **Localização**: `~/.createagents/traces/` (Padrão) ou `TRACE_STORE_PATH`.
- **Estrutura**: Cada linha é um objeto JSON `TraceEntry`.
- **Persistência**: Gerida pelo `FileTraceStore` existente (arquivos rotacionados diariamente ou por tamanho).

### 2.2 Stack Tecnológico do Dashboard

- **Framework**: `Streamlit` (Desenvolvimento rápido de UI).
- **Processamento de Dados**: `Pandas` (Filtragem e agregação eficiente).
- **Visualização**: `Plotly` (Gráficos interativos) + Elementos nativos do Streamlit.
- **Runtime**: Python 3.10+.

## 3. Etapas de Implementação

### Etapa 1: Configuração do Projeto

Criar uma aplicação de dashboard independente dentro do diretório `examples`:

```
examples/dashboard/
├── app.py              # Aplicação principal Streamlit
├── requirements.txt    # Dependências (streamlit, pandas, plotly)
├── loader.py           # Lógica de carregamento e processamento de dados
└── components/         # Componentes de UI
    ├── sidebar.py      # Filtros
    ├── trace_list.py   # Visualização principal em tabela
    └── trace_detail.py # Visualização hierárquica/árvore
```

### Etapa 2: Camada de Carregamento de Dados (`loader.py`)

Implementação de um padrão robusto de classe `TraceLoader`:

- **Cache**: Usar `@st.cache_data` para carregar arquivos. Como os arquivos de trace são apenas de adição (na maioria), podemos fazer cache baseando-nos na data de modificação ou tamanho.
- **Parsing**: Ler eficientemente os arquivos `traces_*.jsonl`.
- **Reconstrução de Hierarquia**: Converter registros planos `TraceEntry` em uma estrutura de árvore aninhada (religando `parent_run_id` ao `run_id`).
- **Conversão para DataFrame**: Criar um DataFrame plano para a "Visualização em Lista" (ordenando por data/hora, filtrando por sessão/agente).

### Etapa 3: Módulos de UI do Dashboard

#### A. Barra Lateral (Filtros)

- **Fonte de Dados**: Seletor de caminho (padrão é `~/.createagents/traces`).
- **Intervalo de Tempo**: Sliders de Data/Hora.
- **ID da Sessão**: Dropdown de múltipla escolha.
- **Status**: Filtro específico para `erro` vs `sucesso`.
- **Busca**: Campo de texto para `ID do Trace` ou palavra-chave em entrada/saída.

#### B. Início (Estatísticas Gerais)

- **KPIs**: Total de Execuções, Taxa de Erro (%), Latência Média (ms), Custo Total ($).
- **Gráficos**:
  - Requisições por Minuto (Gráfico de linha).
  - Distribuição de Latência (Histograma).
  - Uso de Tokens por Modelo (Gráfico de barras).

#### C. Visualização de Lista de Traces

Uma tabela principal exibindo traces:

- **Colunas**: Status (Ícone), Horário, Nome do Agente, Operação, Latência (ms), Tokens, Custo ($).
- **Interação**: Clicar em uma linha abre a **Visualização Detalhada do Trace**.

#### D. Visualização Detalhada do Trace (O Clone do "LangSmith")

Este é o recurso central.

- **Layout Dividido**:
  - **Esquerda (Árvore)**: Uma lista hierárquica de passos (Agente -> Ferramenta -> LLM).
    - Indentação visual baseada na profundidade.
    - Ícones para diferentes tipos de eventos (🤖 LLM, 🔧 Ferramenta, 🧠 Agente).
    - Codificação por cores para status (Verde/Vermelho).
  - **Direita (Inspetor)**:
    - **Metadados**: Modelo, Horário, Latência.
    - **Entradas**: Visualizador JSON.
    - **Saídas**: Visualizador JSON.
    - **Erros**: Stack trace destacado se presente.

### Etapa 4: Otimização para "Execução de 24h"

- **Carregamento Preguiçoso (Lazy Loading)**: Não carregar os payloads detalhados completos na lista principal, se possível.
- **Paginação**: Se houver milhares de traces, paginar a visualização em lista.
- **Auto-Atualização**: Botão ou intervalo estrito para verificar mudanças nos arquivos.

## 4. Checklist de Desenvolvimento

- [ ] Criar diretório `examples/dashboard`.
- [ ] Implementar `loader.py` usando a lógica do `FileTraceStore` mas otimizada para leitura.
- [ ] Construir UI básica em `app.py`.
- [ ] Implementar algoritmo de reconstrução da Visualização em Árvore.
- [ ] Adicionar visualizadores específicos para Chamadas de Ferramentas (entradas/saídas) e Chamadas LLM (prompts/conclusões).
- [ ] Testar com arquivos de log grandes (dados simulados de execução de 24h).

## 5. Dependências Necessárias

```text
streamlit>=1.30.0
pandas>=2.0.0
plotly>=5.18.0
watchdog>=3.0.0  # Opcional, para recarregamento automático na mudança de arquivo
```
