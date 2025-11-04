"""
Script de teste para o sistema RAG
"""
from pathlib import Path
from perguntar import AdvancedRAG

if __name__ == "__main__":
    # Configuração (ajustado para usar notebook_index)
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    INDEX_PREFIX = "notebook_index"
    EMBEDDING_MODEL = "qwen3-embedding:4b"
    LLM_MODEL = "granite4:latest"  # Ajuste conforme seu modelo instalado

    print("=" * 70)
    print("🧪 TESTE DO SISTEMA RAG")
    print("=" * 70)
    print(f"📌 Índice: {INDEX_PREFIX}")
    print(f"📌 Modelo de embedding: {EMBEDDING_MODEL}")
    print(f"📌 Modelo LLM: {LLM_MODEL}")
    print(f"📌 Diretório: {PROJECT_ROOT}")
    print("=" * 70 + "\n")

    # Inicializa sistema RAG
    rag = AdvancedRAG(
        index_path=str(PROJECT_ROOT / f"{INDEX_PREFIX}.faiss"),
        metadata_path=str(PROJECT_ROOT / f"{INDEX_PREFIX}.jsonl"),
        embedding_model=EMBEDDING_MODEL,
        llm_model=LLM_MODEL,
        use_reranking=True,
        use_query_expansion=True,
        enable_logging=True,
    )

    # Lista de perguntas para testar
    perguntas = [
        "Qual é o código que identifica o ativo opção de call no historical_quotes?",
        "Quais são todos os ativos presentes no historical_quotes?",
        "O que contém este documento sobre a B3?",
    ]

    # Testa cada pergunta
    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n{'=' * 70}")
        print(f"TESTE {i}/{len(perguntas)}")
        print(f"{'=' * 70}")

        result = rag.query(
            question=pergunta,
            k=15,  # Recupera 10 documentos inicialmente
            rerank_to=10,  # Rerank para os 10 melhores
        )

        # Exibe resultados
        print("\n" + "=" * 70)
        print("📊 RESULTADO")
        print("=" * 70)
        print(f"\n❓ PERGUNTA:\n{result['question']}\n")
        print(f"💡 RESPOSTA:\n{result['answer']}\n")
        print("📚 FONTES:")
        for j, source in enumerate(result["sources"], 1):
            print(
                f"   {j}. {source['source']} (pág. {source['page']}) - {source['type']}"
            )

        print("\n📈 MÉTRICAS:")
        metrics = result["metrics"]
        print(f"   ⏱️  Tempo total: {metrics['total_time']:.2f}s")
        print(f"   🔍 Retrieval: {metrics['retrieval_time']:.2f}s")
        if metrics.get("rerank_time"):
            print(f"   🔄 Reranking: {metrics['rerank_time']:.2f}s")
        print(f"   💭 Geração: {metrics['generation_time']:.2f}s")
        print(f"   📊 Documentos usados: {metrics['context_chunks']}")
        print(f"   📝 Tamanho resposta: {metrics['response_length']} caracteres")

    print("\n" + "=" * 70)
    print("✅ TESTES CONCLUÍDOS")
    print("✅ Métricas salvas em: rag_metrics.jsonl")
    print("=" * 70)
