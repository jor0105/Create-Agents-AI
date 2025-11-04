from tests.embeddings_tests.indexar import create_embeddings
import logging

logging.basicConfig(level=logging.INFO)

print("Iniciando processamento de embeddings...")

result = create_embeddings(
    documents=["/home/jordan/Downloads/Databases/dados_bolsa_br/Docs_Cvm/DFP/2024/dfp_cia_aberta_DRE_con_2024.parquet"],
    model_name="qwen3-embedding:4b",
    chunk_size=1000,
    chunk_overlap=150,
    batch_size=512,
    num_workers=4,
    output_prefix="DFP_INDEX",
)

# Resultados disponíveis para análise
print("\n" + "=" * 50)
print("RESUMO DO PROCESSAMENTO")
print("=" * 50)

if "error" in result:
    print(f"❌ ERRO: {result['error']}")

print(f"Total de chunks: {result.get('total_chunks', 0)}")
print(f"Chunks processados: {result.get('chunks_processed', 0)}")
print(f"Chunks com falha: {result.get('chunks_failed', 0)}")
print(f"Duplicados removidos: {result.get('duplicates_removed', 0)}")
print(f"Arquivos processados: {result.get('files_processed', 0)}")
print(f"Arquivos com falha: {result.get('files_failed', 0)}")
print(f"Tempo decorrido: {result.get('time_seconds', 0)}s")
print(f"Velocidade: {result.get('chunks_per_second', 0)} chunks/s")

if result.get('total_chunks', 0) > 0:
    print(f"\n📁 Arquivos gerados:")
    print(f"  - Índice FAISS: {result.get('faiss_path', 'N/A')}")
    print(f"  - Metadados: {result.get('metadata_path', 'N/A')}")
    print(f"  - Estatísticas: {result.get('stats_path', 'N/A')}")
    print(f"\n📊 Detalhes técnicos:")
    print(f"  - Dimensão dos embeddings: {result.get('embedding_dimension', 'N/A')}")
    print(f"  - Tipo de índice: {result.get('index_type', 'N/A')}")
else:
    print("\n⚠️  Nenhum arquivo foi gerado (processamento sem chunks)")

print("=" * 50)
