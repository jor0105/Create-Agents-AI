from perguntar import AdvancedRAG, QueryExpander

# =============================================================================
# EXEMPLO 1: Uso Básico (Simples)
# =============================================================================


def exemplo_basico():
    """Exemplo mais simples possível."""

    print("\n" + "=" * 70)
    print("EXEMPLO 1: USO BÁSICO")
    print("=" * 70 + "\n")

    # Inicializa sistema
    rag = AdvancedRAG(
        index_path="vector_index.faiss",
        metadata_path="vector_index.jsonl",
        embedding_model="qwen3-embedding:4b",
        llm_model="granite4:latest",
        use_reranking=True,  # Ativa BM25 reranking
        use_query_expansion=True,  # Ativa query expansion
        enable_logging=True,  # Salva métricas
    )

    # Faz pergunta
    resultado = rag.query(
        question="O que são opções financeiras?",
        k=10,  # Busca 10 docs inicialmente
        rerank_to=4,  # Usa apenas os 4 melhores
    )

    # Exibe resposta
    print(f"\n💡 RESPOSTA:\n{resultado['answer']}\n")
    print(f"⏱️  Tempo total: {resultado['metrics']['total_time']:.2f}s")


# =============================================================================
# EXEMPLO 2: Comparação Com/Sem Reranking
# =============================================================================


def exemplo_comparacao_reranking():
    """Compara qualidade com e sem reranking."""

    print("\n" + "=" * 70)
    print("EXEMPLO 2: COMPARAÇÃO DE RERANKING")
    print("=" * 70 + "\n")

    pergunta = "Como calcular o preço de uma opção?"

    # SEM reranking
    print("🔴 SEM RERANKING:")
    rag_sem_rerank = AdvancedRAG(
        index_path="vector_index.faiss",
        metadata_path="vector_index.jsonl",
        embedding_model="qwen3-embedding:4b",
        llm_model="granite4:latest",
        use_reranking=False,  # ❌ Desativado
        use_query_expansion=False,
        enable_logging=False,
    )

    resultado_sem = rag_sem_rerank.query(pergunta, k=4, rerank_to=4)
    print(f"Resposta: {resultado_sem['answer'][:200]}...")
    print(f"Tempo: {resultado_sem['metrics']['total_time']:.2f}s\n")

    # COM reranking
    print("🟢 COM RERANKING:")
    rag_com_rerank = AdvancedRAG(
        index_path="vector_index.faiss",
        metadata_path="vector_index.jsonl",
        embedding_model="qwen3-embedding:4b",
        llm_model="granite4:latest",
        use_reranking=True,  # ✅ Ativado
        use_query_expansion=True,
        enable_logging=False,
    )

    resultado_com = rag_com_rerank.query(pergunta, k=10, rerank_to=4)
    print(f"Resposta: {resultado_com['answer'][:200]}...")
    print(f"Tempo: {resultado_com['metrics']['total_time']:.2f}s")

    print("\n📊 ANÁLISE:")
    print(
        f"Tempo extra do reranking: +{resultado_com['metrics'].get('rerank_time', 0):.2f}s"
    )
    print("Qualidade: [Compare manualmente as respostas acima]")


# =============================================================================
# EXEMPLO 3: Query Expansion Customizada
# =============================================================================


def exemplo_query_expansion():
    """Demonstra query expansion customizada."""

    print("\n" + "=" * 70)
    print("EXEMPLO 3: QUERY EXPANSION CUSTOMIZADA")
    print("=" * 70 + "\n")

    # Cria expander
    expander = QueryExpander()

    # Adiciona termos customizados do seu domínio
    expander.add_custom_expansion(
        term="bdi", expansions=["índice bdi", "baltic dry index", "frete marítimo"]
    )

    expander.add_custom_expansion(
        term="derivativo", expansions=["opção", "futuro", "swap", "forward"]
    )

    # Testa expansão
    queries = [
        "Qual o valor do BDI?",
        "O que são derivativos?",
        "Como funcionam as opções?",
    ]

    for query in queries:
        expanded = expander.expand(query, max_expansions=3)
        print(f"Original:  '{query}'")
        print(f"Expandida: '{expanded}'")
        print()


# =============================================================================
# EXEMPLO 4: Análise de Métricas Salvas
# =============================================================================


def exemplo_analise_metricas():
    """Analisa métricas salvas no rag_metrics.jsonl."""

    print("\n" + "=" * 70)
    print("EXEMPLO 4: ANÁLISE DE MÉTRICAS")
    print("=" * 70 + "\n")

    import json
    from pathlib import Path

    metrics_file = Path("rag_metrics.jsonl")

    if not metrics_file.exists():
        print("❌ Arquivo rag_metrics.jsonl não encontrado.")
        print("   Execute algumas queries primeiro!")
        return

    # Carrega métricas
    retrievals = []
    generations = []

    with open(metrics_file, "r") as f:
        for line in f:
            entry = json.loads(line)
            if entry["event_type"] == "retrieval":
                retrievals.append(entry)
            elif entry["event_type"] == "generation":
                generations.append(entry)

    if not retrievals:
        print("❌ Nenhuma métrica de retrieval encontrada.")
        return

    # Calcula estatísticas
    print(f"📊 ESTATÍSTICAS ({len(retrievals)} queries):\n")

    # Retrieval
    retrieval_times = [r["retrieval_time_ms"] for r in retrievals]
    rerank_times = [r["rerank_time_ms"] for r in retrievals if r.get("rerank_time_ms")]

    print("🔍 RETRIEVAL:")
    print(f"   Tempo médio: {sum(retrieval_times)/len(retrieval_times):.1f}ms")
    print(f"   Min/Max: {min(retrieval_times):.1f}ms / {max(retrieval_times):.1f}ms")

    if rerank_times:
        print("\n🔄 RERANKING:")
        print(f"   Tempo médio: {sum(rerank_times)/len(rerank_times):.1f}ms")
        print(f"   Overhead: {sum(rerank_times)/sum(retrieval_times)*100:.1f}%")

    # Generation
    if generations:
        gen_times = [g["generation_time_ms"] for g in generations]
        response_lengths = [g["response_length"] for g in generations]

        print("\n💭 GERAÇÃO:")
        print(f"   Tempo médio: {sum(gen_times)/len(gen_times):.1f}ms")
        print(
            f"   Tamanho médio resposta: {sum(response_lengths)/len(response_lengths):.0f} caracteres"
        )

    # Queries mais comuns
    print("\n📝 QUERIES RECENTES:")
    for i, r in enumerate(retrievals[-5:], 1):
        query = r.get("original_query", r.get("query", "N/A"))
        print(f"   {i}. {query[:60]}...")


# =============================================================================
# EXEMPLO 5: Benchmark de Performance
# =============================================================================


def exemplo_benchmark():
    """Testa performance com múltiplas queries."""

    print("\n" + "=" * 70)
    print("EXEMPLO 5: BENCHMARK DE PERFORMANCE")
    print("=" * 70 + "\n")

    import time

    # Queries de teste
    test_queries = [
        "O que são opções?",
        "Como funciona o mercado de derivativos?",
        "Qual a diferença entre call e put?",
        "Como calcular o valor intrínseco?",
        "O que é volatilidade implícita?",
    ]

    # Inicializa RAG
    rag = AdvancedRAG(
        index_path="vector_index.faiss",
        metadata_path="vector_index.jsonl",
        embedding_model="qwen3-embedding:4b",
        llm_model="granite4:latest",
        use_reranking=True,
        use_query_expansion=True,
        enable_logging=False,  # Desativa para benchmark limpo
    )

    print(f"🏃 Executando {len(test_queries)} queries...\n")

    start = time.time()
    results = []

    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}/{len(test_queries)}: {query[:40]}...")

        result = rag.query(query, k=10, rerank_to=4)
        results.append(result)

    total_time = time.time() - start

    # Estatísticas
    print("\n" + "=" * 70)
    print("📊 RESULTADOS DO BENCHMARK")
    print("=" * 70)
    print(f"\n⏱️  Tempo total: {total_time:.2f}s")
    print(f"⚡ Throughput: {len(test_queries)/total_time:.2f} queries/segundo")
    print(f"📊 Tempo médio/query: {total_time/len(test_queries):.2f}s")

    # Breakdown
    avg_retrieval = sum(r["metrics"]["retrieval_time"] for r in results) / len(results)
    avg_generation = sum(r["metrics"]["generation_time"] for r in results) / len(
        results
    )

    print(
        f"\n🔍 Retrieval médio: {avg_retrieval:.2f}s ({avg_retrieval/total_time*100:.1f}%)"
    )
    print(
        f"💭 Geração média: {avg_generation:.2f}s ({avg_generation/total_time*100:.1f}%)"
    )


# =============================================================================
# EXEMPLO 6: Teste de Qualidade (Manual)
# =============================================================================


def exemplo_teste_qualidade():
    """
    Teste manual de qualidade das respostas.
    Compare com perguntar_manual.py para ver a diferença.
    """

    print("\n" + "=" * 70)
    print("EXEMPLO 6: TESTE DE QUALIDADE")
    print("=" * 70 + "\n")

    # Inicializa RAG avançado
    rag = AdvancedRAG(
        index_path="vector_index.faiss",
        metadata_path="vector_index.jsonl",
        embedding_model="qwen3-embedding:4b",
        llm_model="granite4:latest",
        use_reranking=True,
        use_query_expansion=True,
        enable_logging=True,
    )

    # Query difícil (teste de qualidade)
    query_dificil = "Compare opções europeias e americanas em termos de exercício"

    print(f"❓ PERGUNTA DIFÍCIL:\n{query_dificil}\n")

    resultado = rag.query(query_dificil, k=15, rerank_to=5)

    print("=" * 70)
    print("💡 RESPOSTA:")
    print("=" * 70)
    print(resultado["answer"])
    print("\n" + "=" * 70)

    print("\n📚 FONTES USADAS:")
    for i, source in enumerate(resultado["sources"], 1):
        print(f"   {i}. {source['source']} (página {source['page']})")

    print("\n📊 MÉTRICAS:")
    print(f"   ⏱️  Tempo total: {resultado['metrics']['total_time']:.2f}s")
    print(f"   📄 Documentos usados: {resultado['metrics']['context_chunks']}")

    print("\n✅ Avalie manualmente:")
    print("   - A resposta está correta?")
    print("   - Comparou ambos os tipos?")
    print("   - Usou apenas informações do contexto?")


# =============================================================================
# MENU PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    print(
        """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║           🚀 SISTEMA RAG AVANÇADO - EXEMPLOS DE USO                  ║
║                                                                      ║
║  Escolha um exemplo para executar:                                  ║
║                                                                      ║
║  1. Uso Básico (recomendado para começar)                           ║
║  2. Comparação Com/Sem Reranking                                    ║
║  3. Query Expansion Customizada                                     ║
║  4. Análise de Métricas Salvas                                      ║
║  5. Benchmark de Performance                                        ║
║  6. Teste de Qualidade (query difícil)                              ║
║                                                                      ║
║  0. Executar TODOS os exemplos                                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    )

    try:
        escolha = input(
            "Digite o número do exemplo (ou Enter para exemplo 1): "
        ).strip()

        if not escolha:
            escolha = "1"

        exemplos = {
            "1": exemplo_basico,
            "2": exemplo_comparacao_reranking,
            "3": exemplo_query_expansion,
            "4": exemplo_analise_metricas,
            "5": exemplo_benchmark,
            "6": exemplo_teste_qualidade,
        }

        if escolha == "0":
            print("\n🚀 EXECUTANDO TODOS OS EXEMPLOS...\n")
            for num, func in exemplos.items():
                try:
                    func()
                    input("\n[Pressione Enter para continuar...]")
                except Exception as e:
                    print(f"\n❌ Erro no exemplo {num}: {e}")
        elif escolha in exemplos:
            exemplos[escolha]()
        else:
            print(f"❌ Opção inválida: {escolha}")

    except KeyboardInterrupt:
        print("\n\n👋 Até logo!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback

        traceback.print_exc()
