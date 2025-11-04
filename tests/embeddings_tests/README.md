# Sistema RAG (Retrieval-Augmented Generation)

Sistema completo de RAG profissional com indexação de documentos, busca vetorial, reranking BM25 e geração de respostas.

## 📋 Estrutura

```
embeddings_tests/
├── indexar.py          # Pipeline de indexação de documentos
├── perguntar.py        # Sistema RAG de perguntas e respostas
├── main.py            # Script para criar índices
├── test_rag.py        # Script de testes do sistema RAG
└── README.md          # Esta documentação
```

## 🚀 Como Usar

### 1. Instalar Dependências

```bash
poetry install
```

As dependências necessárias incluem:

- `pymupdf` (fitz) - Para processar PDFs
- `pandas` - Para processar CSV/Excel
- `pyarrow` - Para processar Parquet
- `numpy` - Operações numéricas
- `faiss-cpu` - Indexação vetorial
- `ollama` - API para modelos de embedding e LLM

### 2. Criar Índice de Documentos

Edite o arquivo `main.py` para configurar seus documentos:

```python
result = create_embeddings(
    documents=["/caminho/para/seu/documento.pdf"],
    model_name="qwen3-embedding:4b",
    chunk_size=1000,
    chunk_overlap=150,
    batch_size=512,
    num_workers=4,
    output_prefix="meu_index",
)
```

Execute:

```bash
poetry run python tests/embeddings_tests/main.py
```

**Arquivos gerados:**

- `meu_index.faiss` - Índice FAISS com embeddings
- `meu_index.jsonl` - Metadados dos chunks
- `meu_index_stats.json` - Estatísticas do processamento
- `meu_index_metrics.jsonl` - Métricas de indexação (opcional)

### 3. Fazer Perguntas

Edite o arquivo `test_rag.py` para configurar suas perguntas:

```python
# Configuração
INDEX_PREFIX = "meu_index"
EMBEDDING_MODEL = "qwen3-embedding:4b"
LLM_MODEL = "qwen3:latest"

# Perguntas
perguntas = [
    "Sua pergunta aqui?",
    "Outra pergunta?",
]
```

Execute:

```bash
poetry run python tests/embeddings_tests/test_rag.py
```

## 📊 Funcionalidades

### Sistema de Indexação (`indexar.py`)

#### ✨ Principais Features:

1. **Splitter Recursivo Inteligente**

   - Respeita limites semânticos (não corta listas, citações, blocos de código)
   - Overlap baseado em sentenças completas
   - Proteção contra recursão infinita
   - Mínimo de chunk size configurável

2. **Suporte a Múltiplos Formatos**

   - PDF (com rastreamento preciso de páginas)
   - CSV/Excel (com contexto de colunas/sheets)
   - Parquet (com schema)
   - TXT/Markdown

3. **Deduplicação Automática**

   - Hash SHA256 para identificação única
   - Remove chunks duplicados automaticamente

4. **Escolha Automática de Índice**

   - FAISS Flat para volumes pequenos (< 10k chunks)
   - FAISS IVF para grandes volumes (≥ 10k chunks)
   - Configuração manual também disponível

5. **Metadados Ricos**

   - Fonte, página, tipo de documento
   - Timestamps de criação e indexação
   - Contexto do documento

6. **Logging Estruturado**
   - Métricas em JSON (JSONL)
   - Rastreamento de performance
   - Análise posterior facilitada

### Sistema RAG (`perguntar.py`)

#### ✨ Principais Features:

1. **Query Expansion**

   - Expande queries com sinônimos e termos relacionados
   - Dicionário customizável
   - Melhora recall sem modelos pesados

2. **BM25 Reranking**

   - Reordena resultados vetoriais usando BM25
   - Sem modelos extras (apenas TF-IDF)
   - Ideal para ambientes com RAM limitada

3. **Busca Vetorial FAISS**

   - Busca eficiente por similaridade
   - Suporta índices Flat e IVF
   - Normalização de embeddings

4. **Geração de Respostas**

   - Usa contexto recuperado para gerar respostas
   - Metadados nas fontes citadas
   - Controle de alucinação ("Não sei" quando apropriado)

5. **Métricas Detalhadas**
   - Tempo de retrieval, reranking e geração
   - Número de documentos usados
   - Scores de similaridade e BM25
   - Logging em JSON para análise

## ⚙️ Configurações Avançadas

### Parâmetros de Indexação

```python
create_embeddings(
    documents=["..."],
    model_name="qwen3-embedding:4b",

    # Chunking
    chunk_size=1000,              # Tamanho máximo do chunk
    chunk_overlap=150,            # Overlap entre chunks
    min_chunk_size=50,            # Tamanho mínimo aceitável

    # Performance
    batch_size=512,               # Chunks por lote
    num_workers=4,                # Threads paralelas

    # Índice
    use_ivf_index=None,           # None=automático, True/False=manual
    ivf_nlist=100,                # Clusters para IVF
    ivf_threshold=10000,          # Threshold para ativar IVF

    # Qualidade
    normalize_embeddings=True,    # Normaliza vetores
    deduplicate=True,             # Remove duplicados
    add_document_context=True,    # Adiciona contexto do doc

    # Output
    output_prefix="meu_index",
    enable_structured_logging=True,
    custom_metadata={"projeto": "RAG", "versão": "1.0"}
)
```

### Parâmetros de Query

```python
rag.query(
    question="Sua pergunta?",
    k=10,                 # Docs iniciais (busca vetorial)
    rerank_to=4          # Docs finais (após BM25)
)
```

## 📈 Métricas e Análise

### Arquivo de Métricas (`*_metrics.jsonl`)

Exemplo de entrada:

```json
{
  "timestamp": "2025-11-04T08:31:33",
  "session_id": "a1b2c3d4",
  "event_type": "retrieval",
  "original_query": "Qual é a data?",
  "expanded_query": "qual é a data do primeiro registro",
  "num_results": 3,
  "retrieval_time_ms": 820,
  "rerank_time_ms": 5,
  "vector_avg_score": 0.7234,
  "bm25_avg_score": 12.45
}
```

### Análise de Métricas

```python
import json
import pandas as pd

# Carrega métricas
metrics = []
with open("meu_index_metrics.jsonl", "r") as f:
    for line in f:
        metrics.append(json.loads(line))

df = pd.DataFrame(metrics)

# Análise
print(f"Tempo médio de retrieval: {df['retrieval_time_ms'].mean():.2f}ms")
print(f"Tempo médio de reranking: {df['rerank_time_ms'].mean():.2f}ms")
print(f"Score vetorial médio: {df['vector_avg_score'].mean():.4f}")
```

## 🔧 Troubleshooting

### Erro: "Modelo não encontrado"

```bash
# Liste modelos disponíveis
ollama list

# Baixe o modelo necessário
ollama pull qwen3-embedding:4b
ollama pull qwen3:latest
```

### Erro: "Chunk size muito grande"

Reduza o `chunk_size` para caber no contexto do modelo:

```python
chunk_size=800,  # Reduzido de 1000
```

### Performance lenta

1. Aumente `num_workers` (paralelização)
2. Aumente `batch_size` (menos lotes)
3. Use índice IVF para grandes volumes
4. Considere modelo de embedding menor

### Respostas de baixa qualidade

1. Aumente `k` (mais documentos recuperados)
2. Ajuste `chunk_overlap` (melhor contexto)
3. Use reranking (`use_reranking=True`)
4. Ative query expansion (`use_query_expansion=True`)
5. Teste diferentes modelos LLM

## 📚 Exemplos de Uso

### Indexar Múltiplos Documentos

```python
result = create_embeddings(
    documents=[
        "/docs/manual.pdf",
        "/docs/relatorio.xlsx",
        "/docs/dados.csv",
        "/docs/notas/",  # Diretório inteiro
    ],
    model_name="qwen3-embedding:4b",
    output_prefix="conhecimento_base",
)
```

### Query Customizada

```python
from perguntar import AdvancedRAG

rag = AdvancedRAG(
    index_path="conhecimento_base.faiss",
    metadata_path="conhecimento_base.jsonl",
    embedding_model="qwen3-embedding:4b",
    llm_model="qwen3:latest",
    use_reranking=True,
    use_query_expansion=True,
)

result = rag.query(
    question="Como configurar o sistema?",
    k=15,
    rerank_to=5
)

print(result["answer"])
```

### Adicionar Expansões Customizadas

```python
from perguntar import QueryExpander

expander = QueryExpander()
expander.add_custom_expansion("RAG", ["retrieval", "augmented", "generation"])
expander.add_custom_expansion("AI", ["inteligência artificial", "machine learning", "deep learning"])

query_expandida = expander.expand("Como usar RAG com AI?")
print(query_expandida)
```

## 🎯 Boas Práticas

1. **Chunking**

   - Use `chunk_size` entre 500-1500 caracteres
   - `chunk_overlap` entre 10-20% do chunk_size
   - `min_chunk_size` ≈ 5-10% do chunk_size

2. **Indexação**

   - Sempre use `deduplicate=True`
   - Ative `normalize_embeddings=True`
   - Use `add_document_context=True` para melhor rastreabilidade

3. **Query**

   - Comece com `k=10` e `rerank_to=3-5`
   - Ative reranking para melhor precisão
   - Use query expansion para melhor recall

4. **Performance**
   - Monitore métricas regularmente
   - Ajuste `num_workers` baseado em CPU
   - Use IVF para > 10k chunks

## 📝 Licença

Este sistema RAG é parte do projeto AI_Agent.
