#!/usr/bin/env python3
"""
Script interativo para fazer perguntas ao sistema RAG
"""
import sys
from pathlib import Path
from perguntar import AdvancedRAG


def main():
    # Configuração
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    INDEX_PREFIX = "notebook_index"
    EMBEDDING_MODEL = "qwen3-embedding:4b"
    LLM_MODEL = "granite4:latest"

    print("\n" + "=" * 70)
    print("💬 SISTEMA RAG INTERATIVO")
    print("=" * 70)
    print("Digite suas perguntas (ou 'sair' para encerrar)")
    print("=" * 70 + "\n")

    # Inicializa sistema RAG
    try:
        rag = AdvancedRAG(
            index_path=str(PROJECT_ROOT / f"{INDEX_PREFIX}.faiss"),
            metadata_path=str(PROJECT_ROOT / f"{INDEX_PREFIX}.jsonl"),
            embedding_model=EMBEDDING_MODEL,
            llm_model=LLM_MODEL,
            use_reranking=True,
            use_query_expansion=True,
            enable_logging=True,
        )
    except SystemExit:
        print("\n❌ Erro ao carregar o sistema RAG")
        print("Certifique-se de que os arquivos de índice existem:")
        print(f"  - {PROJECT_ROOT / f'{INDEX_PREFIX}.faiss'}")
        print(f"  - {PROJECT_ROOT / f'{INDEX_PREFIX}.jsonl'}")
        print("\nExecute primeiro: poetry run python tests/embeddings_tests/main.py")
        return 1

    # Loop interativo
    while True:
        print("\n" + "-" * 70)
        pergunta = input("❓ Sua pergunta: ").strip()

        if not pergunta:
            continue

        if pergunta.lower() in ["sair", "exit", "quit", "q"]:
            print("\n👋 Até logo!")
            break

        # Processa pergunta
        try:
            result = rag.query(
                question=pergunta,
                k=10,
                rerank_to=4
            )

            # Exibe resultado
            print("\n" + "=" * 70)
            print("💡 RESPOSTA:")
            print("=" * 70)
            print(result["answer"])
            
            print("\n📚 FONTES:")
            for i, source in enumerate(result["sources"], 1):
                print(f"  {i}. {source['source']} (pág. {source['page']})")
            
            print("\n📊 MÉTRICAS:")
            metrics = result["metrics"]
            print(f"  ⏱️  Tempo total: {metrics['total_time']:.2f}s")
            print(f"  📄 Documentos usados: {metrics['context_chunks']}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Até logo!")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            continue

    return 0


if __name__ == "__main__":
    sys.exit(main())
