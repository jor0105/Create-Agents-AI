# ✅ Checklist de Implementação - Sistema RAG Avançado

## 🚀 ETAPA 1: Preparação (5 minutos)

### Verificar Ambiente

- [ ] Python 3.8+ instalado
- [ ] Ollama rodando (`ollama list`)
- [ ] Modelos baixados:
  - [ ] `qwen3-embedding:4b`
  - [ ] `granite4:latest` (ou seu modelo LLM preferido)
- [ ] Bibliotecas instaladas:
  - [ ] `ollama`
  - [ ] `faiss-cpu` (ou `faiss-gpu`)
  - [ ] `numpy`
  - [ ] `pandas`
  - [ ] `pyarrow`
  - [ ] `langchain-text-splitters`
  - [ ] `pymupdf` (fitz)

**Comando de verificação:**

```bash
python -c "import ollama, faiss, numpy, pandas, pyarrow, fitz; print('✅ OK')"
```

---

## 🔧 ETAPA 2: Re-Indexação (OBRIGATÓRIO para BM25)

### Por que re-indexar?

O campo `content` foi adicionado ao metadata. Índices antigos não têm esse campo e o BM25 não funcionará.

### Passos:

1. **Backup (opcional mas recomendado):**

```bash
cp vector_index.faiss vector_index_old.faiss
cp vector_index.jsonl vector_index_old.jsonl
```

2. **Verificar se precisa re-indexar:**

```bash
python atualizar_metadata.py
```

3. **Re-indexar documentos:**

```bash
python indexar.py
```

4. **Verificar sucesso:**

```bash
# Deve mostrar campo 'content' nos metadados
python atualizar_metadata.py
```

**Checklist:**

- [ ] Backup feito (opcional)
- [ ] `atualizar_metadata.py` executado
- [ ] `indexar.py` executado sem erros
- [ ] Verificação de compatibilidade OK
- [ ] Arquivos gerados:
  - [ ] `vector_index.faiss`
  - [ ] `vector_index.jsonl`
  - [ ] `vector_index_stats.json`

---

## 🧪 ETAPA 3: Testes Básicos (10 minutos)

### Teste 1: Sistema Funciona

```bash
python perguntar.py
```

**Verificar:**

- [ ] Carrega índice sem erros
- [ ] Inicializa BM25 (mensagem "Inicializando BM25 reranker...")
- [ ] Executa query completa
- [ ] Salva métricas em `rag_metrics.jsonl`

### Teste 2: Comparação Reranking

```bash
python exemplo_uso_rag_avancado.py
# Escolha opção 2
```

**Verificar:**

- [ ] Mostra diferença de qualidade
- [ ] Tempo de reranking razoável (<500ms)
- [ ] Respostas são diferentes (e idealmente melhores)

### Teste 3: Query Expansion

```bash
python exemplo_uso_rag_avancado.py
# Escolha opção 3
```

**Verificar:**

- [ ] Queries são expandidas corretamente
- [ ] Sinônimos fazem sentido
- [ ] Possível adicionar termos customizados

---

## 📊 ETAPA 4: Validação de Qualidade (30 minutos)

### Criar Dataset de Teste

Crie arquivo `test_queries.txt` com 10-20 perguntas do seu domínio:

```
O que são opções de compra?
Como calcular o valor intrínseco?
Qual a diferença entre call e put?
...
```

### Testar Qualidade

```python
# test_quality.py
from perguntar import AdvancedRAG

rag = AdvancedRAG(
    index_path="vector_index.faiss",
    metadata_path="vector_index.jsonl",
    embedding_model="qwen3-embedding:4b",
    llm_model="granite4:latest",
    use_reranking=True,
    use_query_expansion=True,
    enable_logging=True
)

with open("test_queries.txt") as f:
    queries = [line.strip() for line in f if line.strip()]

for i, query in enumerate(queries, 1):
    print(f"\n{'='*70}")
    print(f"Query {i}/{len(queries)}: {query}")
    print('='*70)

    result = rag.query(query, k=10, rerank_to=4)
    print(f"\nResposta: {result['answer'][:200]}...")
    print(f"Tempo: {result['metrics']['total_time']:.2f}s")

    # Avalie manualmente: resposta faz sentido?
    feedback = input("\nResposta boa? (s/n): ")

    # Salva feedback
    with open("quality_feedback.txt", "a") as f:
        f.write(f"{query}\t{feedback}\n")
```

**Checklist:**

- [ ] Dataset de teste criado
- [ ] Script de teste executado
- [ ] Respostas avaliadas manualmente
- [ ] Taxa de sucesso calculada (ex: 8/10 = 80%)

---

## 🔍 ETAPA 5: Análise de Métricas (15 minutos)

### Verificar Logs

```bash
python exemplo_uso_rag_avancado.py
# Escolha opção 4
```

**Analisar:**

- [ ] Tempo médio de retrieval (<500ms ideal)
- [ ] Overhead de reranking (<200ms ideal)
- [ ] Tempo médio de geração (variável, depende do LLM)
- [ ] Queries mais comuns
- [ ] Scores médios (vetor e BM25)

### Identificar Problemas

**Se retrieval muito lento (>1s):**

- Reduzir `k` (buscar menos docs)
- Verificar tamanho do índice (`vector_index_stats.json`)

**Se reranking muito lento (>500ms):**

- Corpus muito grande (considerar sample menor)
- Muitos documentos sendo reranked (reduzir `k`)

**Se respostas ruins:**

- Verificar qualidade dos chunks (muito pequenos/grandes?)
- Testar sem reranking (`use_reranking=False`)
- Verificar se docs relevantes estão no índice

---

## 🎯 ETAPA 6: Otimização (Opcional, 1-2 horas)

### Tuning de Hiperparâmetros

Teste diferentes configurações:

```python
# Teste 1: Mais documentos
result_1 = rag.query(query, k=20, rerank_to=8)

# Teste 2: Menos documentos
result_2 = rag.query(query, k=5, rerank_to=3)

# Teste 3: Sem expansion
rag_no_exp = AdvancedRAG(..., use_query_expansion=False)
result_3 = rag_no_exp.query(query, k=10, rerank_to=4)
```

**Encontrar melhor configuração:**

- [ ] `k` ideal (trade-off recall vs latência)
- [ ] `rerank_to` ideal (trade-off precision vs latência)
- [ ] Query expansion ajuda? (compare)
- [ ] BM25 ajuda? (compare com/sem)

### Customizar Query Expansion

Adicione termos específicos do seu domínio:

```python
from perguntar import QueryExpander

expander = QueryExpander()

# Exemplo: domínio financeiro
expander.add_custom_expansion("bdi", ["índice bdi", "baltic dry index"])
expander.add_custom_expansion("call", ["opção de compra", "call option"])
expander.add_custom_expansion("put", ["opção de venda", "put option"])

# Salvar para uso futuro (modificar perguntar.py)
```

**Checklist:**

- [ ] Hiperparâmetros testados
- [ ] Melhor configuração identificada
- [ ] Termos customizados adicionados (se aplicável)
- [ ] Configuração documentada

---

## 📈 ETAPA 7: Benchmark Comparativo (30 minutos)

### Comparar: Antigo vs Novo

```bash
# Sistema ANTIGO (sem melhorias)
python perguntar_manual.py  # Salve respostas

# Sistema NOVO (com melhorias)
python perguntar.py  # Compare respostas
```

**Criar tabela de comparação:**

| Query   | Antigo           | Novo              | Ganho? |
| ------- | ---------------- | ----------------- | ------ |
| Query 1 | Resposta parcial | Resposta completa | ✅     |
| Query 2 | Resposta correta | Resposta correta  | =      |
| Query 3 | Resposta errada  | Resposta correta  | ✅     |
| ...     | ...              | ...               | ...    |

**Métricas finais:**

- [ ] % de respostas melhoradas
- [ ] % de respostas mantidas (já eram boas)
- [ ] % de respostas pioradas (debugging necessário)
- [ ] Latência média comparada

---

## 🚀 ETAPA 8: Deploy/Produção (Opcional)

### Checklist de Produção

**Performance:**

- [ ] Tempo de resposta <5s (90% das queries)
- [ ] Taxa de sucesso >80%
- [ ] Métricas sendo logadas corretamente

**Robustez:**

- [ ] Testa queries vazias
- [ ] Testa queries muito longas
- [ ] Testa queries com caracteres especiais
- [ ] Error handling adequado

**Monitoramento:**

- [ ] `rag_metrics.jsonl` sendo escrito
- [ ] Script de análise de métricas pronto
- [ ] Alertas para queries lentas (opcional)

**Documentação:**

- [ ] README atualizado
- [ ] Exemplos de uso documentados
- [ ] Configurações recomendadas documentadas

---

## 🔮 ETAPA 9: Próximos Passos (Futuro)

### Se qualidade é suficiente (70/100):

- [ ] Sistema em produção
- [ ] Monitoramento contínuo
- [ ] Feedback dos usuários

### Se precisa melhorar (95/100):

**Fase 1 - Quick Wins (1-2 dias):**

- [ ] Implementar Cross-Encoder Reranking
- [ ] Implementar RRF (Reciprocal Rank Fusion)
- [ ] Hardware: 12GB RAM

**Fase 2 - Chunking (3-5 dias):**

- [ ] Semantic Chunking
- [ ] Parent-Child Chunking
- [ ] Hardware: 16GB RAM

**Fase 3 - Query Intelligence (2-4 dias):**

- [ ] HyDE
- [ ] Multi-Query
- [ ] Hardware: 16GB RAM

**Consulte `ROADMAP_BIG_TECH.md` para detalhes completos.**

---

## 📝 Checklist Final

### Sistema está pronto se:

- [x] ✅ Re-indexação concluída com campo `content`
- [x] ✅ Testes básicos passando
- [x] ✅ BM25 reranking funcionando
- [x] ✅ Query expansion funcionando
- [x] ✅ Logging estruturado ativo
- [x] ✅ Métricas sendo salvas
- [x] ✅ Qualidade validada (>80% respostas boas)
- [x] ✅ Performance aceitável (<5s por query)
- [x] ✅ Documentação lida e entendida

### Se TODOS os itens acima estão marcados:

🎉 **PARABÉNS! Seu sistema RAG está pronto para uso!** 🎉

---

## 🆘 Troubleshooting Rápido

### Erro: "campo 'content' não encontrado"

**Solução:** Re-indexar com `python indexar.py`

### BM25 muito lento

**Solução:** Reduzir `k` inicial ou desativar temporariamente

### Respostas piores com reranking

**Solução:** Testar `use_reranking=False` ou ajustar BM25 params

### Queries expandidas incorretas

**Solução:** Customizar dicionário de expansão

### Memória insuficiente (8GB)

**Solução:**

1. Reduzir corpus
2. Desativar BM25 temporariamente
3. Considerar upgrade para 12-16GB

---

## 📚 Referências Rápidas

- **Uso básico:** `README_MELHORIAS.md`
- **Roadmap completo:** `ROADMAP_BIG_TECH.md`
- **Sumário técnico:** `SUMARIO_IMPLEMENTACOES.md`
- **Exemplos:** `exemplo_uso_rag_avancado.py`
- **Verificação:** `atualizar_metadata.py`

---

**Última atualização:** 2025-10-31
**Versão do sistema:** MVP 1.0 (Score: 70/100)
