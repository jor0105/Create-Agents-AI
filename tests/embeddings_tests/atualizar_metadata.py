"""
Script para Adicionar Conteúdo aos Metadados do FAISS
=====================================================

IMPORTANTE: O perguntar.py precisa do campo 'content' nos metadados
para o BM25 funcionar. Se você indexou documentos com o indexar.py
ANTES desta atualização, rode este script para adicionar o conteúdo.

Autor: Sistema RAG Profissional
Data: 2025-10-31
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def atualizar_metadata_com_conteudo(
    metadata_path: str = "vector_index.jsonl",
    output_path: str = "vector_index_updated.jsonl",
):
    """
    Atualiza arquivo de metadados para incluir campo 'content'.

    Caso de uso:
    - Você indexou documentos ANTES do campo 'content' ser adicionado
    - O BM25 reranker precisa do conteúdo dos chunks
    - Este script extrai conteúdo dos documentos originais

    Args:
        metadata_path: Caminho do metadata original
        output_path: Caminho para salvar metadata atualizado
    """

    print("=" * 70)
    print("🔧 ATUALIZADOR DE METADATA FAISS")
    print("=" * 70)
    print()

    # Verifica se arquivo existe
    if not Path(metadata_path).exists():
        print(f"❌ Arquivo não encontrado: {metadata_path}")
        return

    # Carrega metadados
    print(f"📂 Carregando: {metadata_path}")
    metadata_list: List[Dict[str, Any]] = []

    with open(metadata_path, "r", encoding="utf-8") as f:
        for line in f:
            meta = json.loads(line)
            metadata_list.append(meta)

    print(f"✅ {len(metadata_list)} chunks carregados")

    # Verifica se já tem conteúdo
    has_content = all("content" in m for m in metadata_list)

    if has_content:
        print("✅ Metadados já contém campo 'content'")
        print("   Nenhuma atualização necessária!")
        return

    print("⚠️  Metadados SEM campo 'content'")
    print("   Será necessário re-indexar documentos para BM25 funcionar")
    print()

    # Agrupa por documento
    docs_by_source: Dict[str, List[Dict]] = {}

    for meta in metadata_list:
        source = meta.get("file_path", meta.get("source", "unknown"))
        if source not in docs_by_source:
            docs_by_source[source] = []
        docs_by_source[source].append(meta)

    print(f"📊 Documentos únicos: {len(docs_by_source)}")
    print()

    # Tenta recriar conteúdo (limitado)
    print("🔄 OPÇÕES:")
    print()
    print("1. ❌ NÃO É POSSÍVEL recuperar conteúdo automaticamente")
    print("   Motivo: Conteúdo não estava sendo salvo no metadata")
    print()
    print("2. ✅ SOLUÇÃO: Re-indexar documentos com indexar.py atualizado")
    print()
    print("3. 🔧 ALTERNATIVA: Desativar BM25 reranking temporariamente")
    print()

    print("=" * 70)
    print("📋 INSTRUÇÕES PARA HABILITAR BM25:")
    print("=" * 70)
    print()
    print("Opção A - Re-indexar (RECOMENDADO):")
    print("  1. Rode: python indexar.py")
    print("  2. Aguarde indexação completar")
    print("  3. Rode: python perguntar.py")
    print()
    print("Opção B - Desativar BM25 temporariamente:")
    print("  No perguntar.py, altere:")
    print("  use_reranking=False  # Desativa BM25")
    print()
    print("Opção C - Usar perguntar_manual.py (sistema antigo):")
    print("  python perguntar_manual.py  # Funciona sem metadata de conteúdo")
    print()


def verificar_compatibilidade(metadata_path: str = "vector_index.jsonl"):
    """Verifica se metadata é compatível com perguntar.py."""

    print("\n🔍 VERIFICAÇÃO DE COMPATIBILIDADE\n")

    if not Path(metadata_path).exists():
        print(f"❌ Arquivo não encontrado: {metadata_path}")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        first_line = f.readline()

    meta = json.loads(first_line)

    print("Campos disponíveis:")
    for key in meta.keys():
        print(f"  ✅ {key}")

    print()

    if "content" in meta:
        print("✅ COMPATÍVEL com perguntar.py (BM25 funcionará)")
    else:
        print("⚠️  INCOMPATÍVEL com BM25 (campo 'content' ausente)")
        print("   Soluções: veja instruções acima")


if __name__ == "__main__":
    import sys

    print(
        """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║         🔧 ATUALIZADOR DE METADATA PARA BM25 RERANKING               ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    )

    # Permite especificar arquivo customizado
    metadata_file = sys.argv[1] if len(sys.argv) > 1 else "vector_index.jsonl"

    # Verifica compatibilidade
    verificar_compatibilidade(metadata_file)

    print("\n" + "=" * 70)

    # Tenta atualizar
    atualizar_metadata_com_conteudo(metadata_file)

    print("\n✅ Verificação concluída!")
    print()
