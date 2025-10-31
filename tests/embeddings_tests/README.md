# 🚀 Pipeline Modular de Embeddings com Ollama - Versão Profissional

Sistema extremamente simples e modular para criar embeddings de documentos usando modelos do Ollama, com **detecção automática de índice** e melhores práticas da indústria.

## ✨ Características

- ✅ **Ultra Simples**: Uma única função para tudo
- ✅ **Totalmente Modular**: Customize qualquer parâmetro
- ✅ **Múltiplos Formatos**: PDF, CSV, Parquet, Excel, TXT, MD
- ✅ **Processamento Paralelo**: Aproveita múltiplos cores
- ✅ **Seguro para Notebooks**: Logs detalhados e tratamento de erros
- ✅ **Eficiente em Memória**: Streaming de dados grandes
- 🆕 **Detecção Automática de Índice**: Escolhe Flat ou IVF baseado no volume
- 🆕 **Normalização de Embeddings**: Para similaridade coseno eficiente
- 🆕 **Deduplicação Automática**: Economiza 20-40% de espaço
- 🆕 **Metadados Profissionais**: Rastreamento completo (15+ campos)

## 📦 Instalação

```bash
pip install ollama faiss-cpu numpy pandas pyarrow pymupdf langchain-text-splitters openpyxl
```

## 🎯 Uso Rápido

### Exemplo Básico (com Detecção Automática)

```python
from indexar import create_embeddings

# O sistema decide automaticamente o melhor índice!
result = create_embeddings(
    documents=["./meus_documentos"],  # Diretório ou lista de arquivos
    model_name="qwen3-embedding:4b"   # Modelo do Ollama
)

# < 10.000 chunks → IndexFlatL2 (busca exata)
# ≥ 10.000 chunks → IndexIVFFlat (busca aproximada, escalável)

print(f"✓ {result['total_chunks']} chunks indexados")
print(f"🔧 Índice: {result['index_type']} ({'automático' if result['index_auto_selected'] else 'manual'})")
print(f"🗑️  Duplicados removidos: {result['duplicates_removed']}")
```

### Exemplo com Arquivos Específicos

```python
result = create_embeddings(
    documents=[
        "artigo1.pdf",
        "dados.csv",
        "relatorio.parquet",
        "planilha.xlsx"
    ],
    model_name="qwen3-embedding:4b",
    chunk_size=800,
    chunk_overlap=100,
    output_prefix="arquivos_especificos"
)
```

### Exemplo Completo com Todas as Opções

````python
result = create_embeddings(
    # Documentos
    documents=["./docs_tecnicos", "./relatorios"],

    # Modelo de IA
    model_name="qwen3-embedding:4b",

    # Configuração de chunking
    chunk_size=1200,
    chunk_overlap=200,
    min_chunk_size=50,  # ✅ Ignora chunks muito pequenos

    # Qualidade RAG (RECOMENDADO - sempre True)
    normalize_embeddings=True,  # ✅ Para similaridade coseno
    deduplicate=True,  # ✅ Remove duplicados (-20 a -40%)
    add_document_context=True,  # ✅ Metadados ricos

    # Índice FAISS (detecção automática por padrão)
    # use_ivf_index=None (padrão) - Sistema decide automaticamente
    # use_ivf_index=True - Força IVF
    # use_ivf_index=False - Força Flat
    ivf_threshold=10000,  # Threshold para ativar IVF

    # Metadados customizados
    custom_metadata={
        "project": "RAG System",
        "version": "2.0"
    },

    # Performance
    batch_size=512,
    num_workers=4,
    output_prefix="indice_completo"
)
```## 📋 Parâmetros

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `documents` | List[str] | **Obrigatório** | Arquivos ou diretórios para processar |
| `model_name` | str | "qwen3-embedding:4b" | Modelo Ollama para embeddings |
| `chunk_size` | int | 1000 | Tamanho máximo de cada chunk (caracteres) |
| `chunk_overlap` | int | 150 | Sobreposição entre chunks (caracteres) |
| `batch_size` | int | 512 | Chunks a processar por vez |
| `num_workers` | int | 4 | Número de threads paralelas |
| `output_prefix` | str | "vector_index" | Prefixo dos arquivos de saída |
| `normalize_embeddings` | bool | True | ✅ Normaliza vetores (RECOMENDADO) |
| `deduplicate` | bool | True | ✅ Remove duplicados (RECOMENDADO) |
| `min_chunk_size` | int | 50 | Tamanho mínimo de chunk |
| `add_document_context` | bool | True | Adiciona contexto do documento |
| `use_ivf_index` | bool\|None | None | None=automático, True=IVF, False=Flat |
| `ivf_threshold` | int | 10000 | Chunks para ativar IVF automaticamente |
| `ivf_nlist` | int | 100 | Número de clusters IVF |
| `custom_metadata` | Dict | None | Metadados customizados (JSON) |

## 📄 Formatos Suportados

- **PDF** (.pdf) - Documentos de texto (com rastreamento de páginas)
- **CSV** (.csv) - Planilhas de dados
- **Parquet** (.parquet) - Dados colunares
- **Excel** (.xlsx, .xls) - Planilhas do Microsoft Excel
- **Texto** (.txt) - Arquivos de texto simples
- **Markdown** (.md) - Documentos Markdown

## 🆕 Detecção Automática de Índice FAISS

O sistema agora escolhe **automaticamente** o melhor tipo de índice baseado no volume de documentos:

| Volume de Chunks | Índice Selecionado | Características |
|------------------|-------------------|-----------------|
| **< 10.000** | IndexFlatL2 | ✅ Busca exata, muito rápida |
| **≥ 10.000** | IndexIVFFlat | ✅ Busca aproximada, escalável (10-100x mais rápido) |

**Você não precisa se preocupar!** O sistema otimiza automaticamente.

### Controlando Manualmente (se necessário):

```python
# Detecção automática (RECOMENDADO)
result = create_embeddings(documents=["./docs"])

# Forçar Flat (busca exata)
result = create_embeddings(documents=["./docs"], use_ivf_index=False)

# Forçar IVF (grande escala)
result = create_embeddings(documents=["./docs"], use_ivf_index=True)

# Ajustar threshold (padrão: 10.000)
result = create_embeddings(documents=["./docs"], ivf_threshold=15000)
````

## 🎨 Modelos do Ollama Recomendados

```python
# Para português (recomendado)
model_name="qwen3-embedding:4b"

# Alternativas
model_name="llama2"
model_name="nomic-embed-text"
model_name="mxbai-embed-large"
```

## ⚙️ Otimização de Performance

### Máxima Velocidade (usa mais recursos)

```python
batch_size=1024      # Lotes grandes
num_workers=16       # Muitas threads
```

### Mínimo de Recursos (mais lento, mas seguro)

```python
batch_size=128       # Lotes pequenos
num_workers=2        # Poucas threads
```

### Balanceado (recomendado)

```python
batch_size=512       # Lotes médios
num_workers=4        # Threads moderadas
```

## 📊 Chunks por Tipo de Documento

### Documentos Técnicos/Científicos

```python
chunk_size=1500      # Chunks grandes
chunk_overlap=250    # Overlap maior
```

### Dados Tabulares (CSV/Excel)

```python
chunk_size=500       # Chunks pequenos
chunk_overlap=50     # Overlap mínimo
```

### Documentos Gerais

```python
chunk_size=1000      # Tamanho médio
chunk_overlap=150    # Overlap médio
```

## 📂 Arquivos Gerados

Após o processamento, dois arquivos são criados:

1. **`[output_prefix].faiss`** - Índice vetorial FAISS para busca
2. **`[output_prefix].jsonl`** - Metadados de cada chunk

## 💡 Exemplos Práticos

### 1. Processar diretório inteiro

```python
result = create_embeddings(
    documents=["./documentos"],
    model_name="qwen3-embedding:4b"
)
```

### 2. Múltiplas fontes

```python
result = create_embeddings(
    documents=[
        "./artigos",
        "./relatorios",
        "documento_importante.pdf"
    ],
    model_name="qwen3-embedding:4b"
)
```

### 3. Usar em Jupyter Notebook

```python
# Os logs aparecem automaticamente mostrando progresso
result = create_embeddings(
    documents=["./dados"],
    output_prefix="notebook_index"
)

# Resultados disponíveis para análise
print(f"Chunks: {result['total_chunks']}")
print(f"Tempo: {result['time_seconds']}s")
```

## 🔧 Uso via Linha de Comando

```bash
# Processar documentos via CLI
python indexar.py ./documentos --model qwen3-embedding:4b --chunk-size 1000 --output meu_indice

# Ver todas as opções
python indexar.py --help
```

## 📝 Arquivos no Projeto

- **`indexar.py`** - Módulo principal com a função `create_embeddings()`
- **`exemplo_uso.py`** - Exemplos de uso em scripts Python
- **`exemplo_embeddings.ipynb`** - Notebook interativo com exemplos
- **`indexar_antigo.py`** - Versão anterior (backup)

## 🚀 Começando Rápido

1. Instale as dependências
2. Garanta que o Ollama está rodando
3. Importe e use:

```python
from indexar import create_embeddings

result = create_embeddings(
    documents=["./meus_docs"],
    model_name="qwen3-embedding:4b"
)
```

Pronto! Seus embeddings estão criados.

## 🤝 Integração com RAG

Os arquivos gerados podem ser usados diretamente em sistemas RAG:

```python
import faiss
import json

# Carregar índice
index = faiss.read_index("meu_indice.faiss")

# Carregar metadados
metadata = []
with open("meu_indice.jsonl", "r") as f:
    for line in f:
        metadata.append(json.loads(line))

# Fazer busca
query_vector = [...]  # Seu vetor de consulta
distances, indices = index.search(query_vector, k=5)

# Recuperar chunks relevantes
for idx in indices[0]:
    print(metadata[idx])
```

## 📖 Documentação Adicional

- **Ollama**: https://ollama.ai
- **FAISS**: https://github.com/facebookresearch/faiss
- **LangChain**: https://python.langchain.com

## 🐛 Solução de Problemas

### "Prompt too long"

Reduza o `chunk_size`:

```python
chunk_size=800  # ou 500
```

### Processamento muito lento

Aumente `num_workers` e `batch_size`:

```python
num_workers=8
batch_size=1024
```

### Usando muita RAM

Reduza `batch_size`:

```python
batch_size=128
```

## 📄 Licença

Este código é fornecido como está para uso educacional.
